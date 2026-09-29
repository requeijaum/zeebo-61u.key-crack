#!/usr/bin/env python3
"""Find code references to a target paddr inside a given paddr range.

Covers Thumb BL/BLX (24-bit imm11/imm10H), Thumb B, and the ARM PLT
form `ldr pc,[pc,#-4]` (literal at +4, bit0 selects the entry).

Usage: python3 tools/refs.py <img> <target> [lo] [hi]
"""
import re, struct, subprocess, sys
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_ARM

img = sys.argv[1]
tgt = int(sys.argv[2], 16)
lo = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x10000000
hi = int(sys.argv[4], 16) if len(sys.argv) > 4 else 0x1140c000

d = open(img, "rb").read()
out = subprocess.run(["readelf", "-W", "-l", img], capture_output=True, text=True).stdout
segs = []
for line in out.splitlines():
    m = re.match(r"\s*LOAD\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)\s+([RWE ]{3,5})", line)
    if m:
        off, paddr, fsz = (int(m.group(i), 16) for i in (1, 3, 4))
        segs.append((paddr, paddr + fsz, off, "R E" in m.group(6) or "RWE" in m.group(6)))

def fo(a):
    for p, e, o, _ in segs:
        if p <= a < e:
            return o + (a - p)
    return None

T = Cs(CS_ARCH_ARM, CS_MODE_THUMB); T.skipdata = True

def scan(a, b, text=True):
    for addr in range(a, b):
        if addr % 2 and text:      # thumb text is 2-byte aligned
            continue
        o = fo(addr)
        if o is None:
            continue
        for i in T.disasm(d[o:o + 4], addr):
            if i.address != addr:
                break
            if i.mnemonic in ("bl", "blx") and i.op_str.startswith("#0x"):
                try:
                    if int(i.op_str[1:], 16) == tgt:
                        yield addr, i.mnemonic
                except ValueError:
                    pass
            break

def scan_plt():
    """ARM PLT stubs: ldr pc,[pc,#-4], literal at +4, entry = lit & ~1."""
    A = Cs(CS_ARCH_ARM, CS_MODE_ARM); A.skipdata = False
    for a in range(lo, hi, 4):
        o = fo(a)
        if o is None:
            continue
        w = struct.unpack("<I", d[o:o + 4])[0]
        if (w & 0xFFFF0000) == 0xE51FF000:      # ldr pc,[pc,#-4]
            lo2 = struct.unpack("<i", struct.pack("<I", (w & 0xFFF) | 0xFFFFF000 if w & 0x80000000 else w & 0xFFF))[0]
            la = a + 8 + lo2
            lo_f = fo(la)
            if lo_f is None:
                continue
            lit = struct.unpack("<I", d[lo_f:lo_f + 4])[0]
            if (lit & ~1) == tgt:
                yield a, f"ARM PLT -> {lit & ~1:#x}"

hits = list(scan(lo, hi)) + list(scan_plt())
hits.sort()
for a, k in hits:
    print(f"  {a:#x}  {k}")
print(f"# {len(hits)} hit(s) for {tgt:#x} in [{lo:#x},{hi:#x}) in {img}")
