#!/usr/bin/env python3
"""Disassemble a window of an APPS/AMSS image at PADDR (the third LOAD column,
which is what Ghidra loads and what all notes use). Read-only.

Usage: python3 tools/dis.py 0x10763af0 [ninst] [--arm] [--img PATH]
"""
import re, subprocess, sys
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_ARM

DEFAULT = "/home/rafaelfrequiao/projects/zeebo-lle/nand/1.1.2_APPS.bin"

def load_segments(img):
    """Return [(paddr, paddr+filesz, fileoff)] from readelf -l."""
    out = subprocess.run(["readelf", "-W", "-l", img], capture_output=True, text=True).stdout
    segs = []
    for line in out.splitlines():
        m = re.match(r"\s*LOAD\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)"
                     r"\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)\s+([RWE ]{3,5})", line)
        if m:
            off, _vaddr, paddr, filesz = (int(m.group(i), 16) for i in (1, 2, 3, 4))
            segs.append((paddr, paddr + filesz, off))
    return segs

def foff(segs, addr):
    for p, e, o in segs:
        if p <= addr < e:
            return o + (addr - p)
    raise SystemExit(f"address {addr:#x} not in any LOAD segment")

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    img = DEFAULT
    for a in sys.argv[1:]:
        if a.startswith("--img="):
            img = a.split("=", 1)[1]
    if not args:
        raise SystemExit(__doc__)
    a = int(args[0], 16)
    n = int(args[1]) if len(args) > 1 else 32
    thumb = "--arm" not in sys.argv
    segs = load_segments(img)
    data = open(img, "rb").read()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB if thumb else CS_MODE_ARM)
    md.skipdata = True
    off = foff(segs, a)
    print(f"=== {a:#x} (foff {off:#x}) {'THUMB' if thumb else 'ARM'} [{img}] ===")
    count = 0
    for ins in md.disasm(data[off:off + n * 8], a):
        print(f"  {ins.address:08x}  {ins.bytes.hex(' '):<20} {ins.mnemonic:7} {ins.op_str}")
        count += 1
        if count >= n:
            break

if __name__ == "__main__":
    main()
