#!/usr/bin/env python3
"""Hunt split address materialization (movw/movt) for target vaddrs.

Background (PLAN.md 2.1): the 61u.key strings have zero absolute-pointer
refs in 1.1.2_APPS.bin, so the code must build their addresses in registers.
Encoding-level scan (no disassembler: immune to sweep desync):
  Thumb-2 movw/movt (hw1 0xF24x/0xF2Cx) + ARM movw/movt (0xE30/0xE34),
decoded to (Rd, imm16) at every alignment in executable LOAD segments.
A movw imm16==low16(T) followed within 128B by movt same-Rd imm16==high16(T)
is a full materialization of T.

Usage:
    python3 tools/hunt_refs.py firmware/1.1.2_APPS.bin
    python3 tools/hunt_refs.py firmware/1.1.2_APPS.bin --targets 0x108d08a4,...

Exit 0 always; prints PAIR hits (decisive) then unpaired half-hits (leads).
"""

import argparse
import re
import struct
import subprocess
import sys

DEFAULT_TARGETS = [
    0x108d08a4,  # fs:/mcp/61u.key
    0x108d08b4,  # fs:/card0/61u.key
    0x10aff2e4,  # /61u.key
    0x10aff29c,  # lctsys/61s.dat
    0x11267a40,  # fs:/mcp/lctsys/61s.dat
    0x10e9fc4a,  # OEM_LCTSystemCtl.c
]


def load_segments(path):
    out = subprocess.run(['readelf', '-W', '-l', path],
                         capture_output=True, text=True).stdout
    segs = []
    for m in re.finditer(
            r'LOAD\s+0x([0-9a-fA-F]+)\s+0x([0-9a-fA-F]+)\s+'
            r'0x[0-9a-fA-F]+\s+0x([0-9a-fA-F]+)\s+0x[0-9a-fA-F]+\s+([RWE ]+)',
            out):
        off, vaddr, fsz, flags = m.groups()
        segs.append({'off': int(off, 16), 'vaddr': int(vaddr, 16),
                     'fsz': int(fsz, 16), 'flags': flags.strip()})
    return [s for s in segs if 'E' in s['flags']]


def scan(data, segs):
    """Return list of (vaddr, kind, rd, imm16): kind in movw/movt/tmovw/tmovt."""
    out = []
    for seg in segs:
        base_off, base_v = seg['off'], seg['vaddr']
        blob = data[base_off:base_off + seg['fsz']]
        # Thumb-2 32-bit movw/movt at any 2-byte alignment
        for i in range(0, len(blob) - 4, 2):
            hw1, hw2 = struct.unpack('<HH', blob[i:i + 4])
            if (hw1 & 0xfff0) == 0xf240 or (hw1 & 0xfff0) == 0xf2c0:
                is_movt = (hw1 & 0xfff0) == 0xf2c0
                imm4 = hw1 & 0xf
                i_bit = (hw1 >> 10) & 1
                imm3 = (hw2 >> 12) & 0x7
                rd = (hw2 >> 8) & 0xf
                imm8 = hw2 & 0xff
                imm16 = (imm4 << 12) | (i_bit << 11) | (imm3 << 8) | imm8
                out.append((base_v + i, 'tmovt' if is_movt else 'tmovw', rd, imm16))
        # ARM movw/movt at any 4-byte alignment (cond-agnostic).
        # Encoding: cond(31:28) 0011 0 bit22(0=movw/1=movt) 0000 imm4(19:16)
        #           Rd(15:12) imm12(11:0); imm16 = imm4:imm12.
        for i in range(0, len(blob) - 4, 4):
            w = struct.unpack('<I', blob[i:i + 4])[0]
            if (w & 0x0fb00000) == 0x03000000 or (w & 0x0fb00000) == 0x03400000:
                is_movt = bool(w & 0x00400000)
                rd = (w >> 12) & 0xf
                imm16 = ((w >> 16) & 0xf) << 12 | (w & 0xfff)
                out.append((base_v + i, 'amovt' if is_movt else 'amovw', rd, imm16))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('bin', help='APPS.bin path')
    ap.add_argument('--targets', default=','.join(hex(t) for t in DEFAULT_TARGETS))
    args = ap.parse_args()

    targets = [int(x, 0) for x in args.targets.split(',') if x.strip()]
    data = open(args.bin, 'rb').read()
    segs = load_segments(args.bin)
    print(f"exec segments: {len(segs)}", file=sys.stderr)

    ops = scan(data, segs)
    print(f"movw/movt ops decoded: {len(ops)}", file=sys.stderr)

    by_reg = {}
    pairs = []
    for vaddr, kind, rd, imm16 in ops:
        w = kind in ('tmovw', 'amovw')
        for t in targets:
            want = ((t >> 16) & 0xffff) if not w else (t & 0xffff)
            if imm16 != want:
                continue
            if w:
                by_reg.setdefault(rd, []).append((vaddr, t, kind))
            else:
                for vw, tt, wk in by_reg.get(rd, []):
                    if tt == t and 0 <= vaddr - vw <= 128:
                        pairs.append((vw, vaddr, rd, t, wk, kind))
    for vw, vt, rd, t, wk, tk in sorted(pairs):
        print(f"PAIR r{rd}={t:#x} {wk}@{vw:#x} + {tk}@{vt:#x}")

    # unpaired halves (leads, can be noisy)
    paired = {(vw, t) for vw, _, _, t, _, _ in pairs}
    n = 0
    for rd, lst in sorted(by_reg.items()):
        for vw, t, wk in sorted(lst):
            if (vw, t) not in paired:
                if n < 20:
                    print(f"half r{rd} low16({t:#x}) {wk}@{vw:#x}")
                n += 1
    print(f"{len(pairs)} pairs, {n} unpaired low16 halves")


if __name__ == '__main__':
    main()
