#!/usr/bin/env python3
"""QCDM/DIAG fuzzer skeleton for the Zeebo rear port (UNTESTED, no hardware).

Background (re/notes.md section 9): DFS Port Manager occasionally enumerates
the port at boot without a key (USB race, no authorization). This script
speaks raw DIAG frames to try unauthenticated commands and SPC/password
defaults, especially inside that boot window.

QCDM framing (public Qualcomm DIAG knowledge, VERIFY against a live port):
  frame  = 0x7E + escaped(payload + crc16_le) + 0x7E
  escape = 0x7D, escaped byte ^= 0x20 (applies to 0x7E and 0x7D)
  crc    = CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF) over payload

Commands implemented:
  VERNO (0x00), ESN (0x01), SPC unlock (0x41 + 6 ASCII digits),
  PASSWORD (0x46 + 6 ASCII digits, CDMA heritage - may not exist),
  DOWNLOAD 0x3A (known-good post-gate; try pre-gate for a behavior delta).

Usage:
    python3 tools/diag_fuzz.py --dry-run          # no hardware: print frames
    python3 tools/diag_fuzz.py /dev/ttyUSB0       # needs locked console
    python3 tools/diag_fuzz.py /dev/ttyUSB0 --spc-list 000000,123456

Response classes: valid reply (first byte echoes/known) vs DIAG_BAD_CMD
(0x13) vs timeout. Anything that is NOT bad-cmd/timeout is a lead.
"""

import argparse
import struct
import sys
import time

DIAG_VERNO = 0x00
DIAG_ESN = 0x01
DIAG_BAD_CMD = 0x13
DIAG_SPC = 0x41
DIAG_PASSWORD = 0x46
DIAG_DOWNLOAD = 0x3A

DEFAULT_SPCS = ["000000", "123456", "654321", "111111", "123123"]


def crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def frame(payload: bytes) -> bytes:
    raw = payload + struct.pack("<H", crc16_ccitt(payload))
    out = bytearray(b"\x7e")
    for b in raw:
        if b in (0x7E, 0x7D):
            out += bytes((0x7D, b ^ 0x20))
        else:
            out.append(b)
    out += b"\x7e"
    return bytes(out)


def unframe(buf: bytes):
    """Split stream into (payload, ok_crc) frames. Returns (frames, rest)."""
    frames, cur, esc = [], bytearray(), False
    for b in buf:
        if b == 0x7E:
            if cur:
                payload, crc = bytes(cur[:-2]), struct.unpack("<H", bytes(cur[-2:]))[0]
                frames.append((payload, crc16_ccitt(payload) == crc))
                cur = bytearray()
        elif b == 0x7D:
            esc = True
        else:
            cur.append(b ^ 0x20 if esc else b)
            esc = False
    return frames, bytes(cur)


def cmd_spc(code: str) -> bytes:
    assert len(code) == 6 and code.isdigit()
    return bytes((DIAG_SPC,)) + code.encode()


def cmd_password(code: str) -> bytes:
    assert len(code) == 6 and code.isdigit()
    return bytes((DIAG_PASSWORD,)) + code.encode()


PROBES = [("VERNO", bytes((DIAG_VERNO,))),
          ("ESN", bytes((DIAG_ESN,))),
          ("DOWNLOAD-0x3A", bytes((DIAG_DOWNLOAD,)))]


def dry_run(spcs):
    for name, p in PROBES:
        print(f"{name:14} {frame(p).hex()}")
    for s in spcs:
        print(f"SPC-{s:6}      {frame(cmd_spc(s)).hex()}")
        print(f"PASSWORD-{s:6} {frame(cmd_password(s)).hex()}")


def live(port, spcs, timeout=1.0):
    import serial
    ser = serial.Serial(port, 115200, timeout=timeout)
    time.sleep(0.3)
    plan = ([(n, p) for n, p in PROBES]
            + [(f"SPC-{s}", cmd_spc(s)) for s in spcs]
            + [(f"PASSWORD-{s}", cmd_password(s)) for s in spcs])
    for name, payload in plan:
        ser.reset_input_buffer()
        ser.write(frame(payload))
        time.sleep(timeout)
        data = ser.read(4096)
        frames, _ = unframe(data)
        if not frames:
            print(f"{name:14} TIMEOUT")
            continue
        for p, ok in frames:
            tag = "OK " if ok else "CRC-ERR "
            if p and p[0] == DIAG_BAD_CMD:
                tag = "BAD-CMD"
            print(f"{name:14} {tag} reply={p.hex()}")
            if ok and p and p[0] not in (DIAG_BAD_CMD,):
                print(f"  ^^^ LEAD: {name} answered ({len(p)} bytes)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("port", nargs="?", help="serial port (omit with --dry-run)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--spc-list", default=",".join(DEFAULT_SPCS))
    args = ap.parse_args()
    spcs = [s for s in args.spc_list.split(",") if s.strip()]
    if args.dry_run or not args.port:
        dry_run(spcs)
    else:
        live(args.port, spcs)


if __name__ == "__main__":
    main()
