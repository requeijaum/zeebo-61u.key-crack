#!/usr/bin/env python3
"""Find every way code references a string/data address in an ARM ELF.

Why (see re/notes.md sections 2b, 28e, 29a): `getReferencesTo()` and the
movw/movt-only scan in `hunt_refs.py` both came back empty for the 61u.key
strings, which is a false negative. On 1.1.2_APPS.bin the LCT AT handlers
reach `/61u.key` through a plain Thumb `adr`, and the dsatparm log strings are
reached through a pointer-to-record table. Neither pattern is a movw/movt pair
nor a literal-pool dword, so neither old tool could see them.

This tool is encoding-level (no disassembler, so it cannot desync) and covers:

  1. dat   -- absolute LE32 dword equal to the target (a DATA reference:
              a pointer in a table/struct, not an instruction)
  2. ADR   -- Thumb ADR (hw & 0xF800 == 0xA000), target computed from PC
  3. LIT   -- Thumb LDR (literal) [pc, #imm], word at the literal == target
  4. MOVW  -- Thumb-2 movw+movt pair materializing the target
  5. PLT   -- ARM `ldr pc, [pc, #-4]` slot resolving to the target

Function attribution: each hit is attributed to the nearest preceding
function-start heuristic (push {...lr} / stmdb sp! / ldr pc,[pc,#-4] boundary),
so output groups by function instead of dumping thousands of bare sites.

Segment bases use the ELF **paddr**, not vaddr: these Qualcomm images have
vaddr 0xf0000000 but the toolchain/Ghidra load at paddr 0x10000000, and using
the wrong one silently shifts every address by 0xf0000000. (Section 28b.)

Usage:
    python3 tools/find_str_refs.py firmware/1.1.2_APPS.bin --str /61u.key
    python3 tools/find_str_refs.py firmware/1.1.2_APPS.bin --addr 0x10aff2e4
    python3 tools/find_str_refs.py firmware/1.1.2_APPS.bin --str usb.key \\
        --context 0x200

Exit 0 always. Reads the file, writes nothing.
"""

import argparse
import re
import struct
import subprocess
import sys

PLT_MAGIC = b'\x04\xf0\x1f\xe5'  # ARM: ldr pc, [pc, #-4]


def load_segments(path, use_paddr=True):
    """Return [(file_off, file_off+filesz, load_addr, flags)], sorted."""
    out = subprocess.run(['readelf', '-W', '-l', path],
                         capture_output=True, text=True).stdout
    segs = []
    # LOAD  Offset VirtAddr PhysAddr FileSiz MemSiz Flags Align
    # Flags may be two tokens ("R E"), so allow an internal space.
    pat = re.compile(
        r'\s*LOAD\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)'
        r'\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)\s+([RWE ]{3,5})\s+(0x[0-9a-f]+)')
    for line in out.splitlines():
        m = pat.match(line)
        if not m:
            continue
        g = m.groups()
        off, va, pa, fsz, flags = int(g[0], 16), int(g[1], 16), \
            int(g[2], 16), int(g[3], 16), g[5]
        if not fsz:
            continue
        segs.append((off, off + fsz, pa if use_paddr else va,
                     flags.replace(' ', '')))
    segs.sort()
    return segs


class Image:
    def __init__(self, path):
        self.path = path
        self.data = open(path, 'rb').read()
        self.segs = load_segments(path)
        self.exe_ranges = [s for s in self.segs if 'E' in s[3]]

    def addr_of(self, off):
        for lo, hi, base, _ in self.segs:
            if lo <= off < hi:
                return base + (off - lo)
        return None

    def off_of(self, addr):
        for lo, hi, base, _ in self.segs:
            if base <= addr < base + (hi - lo):
                return lo + (addr - base)
        return None

    def word(self, addr):
        o = self.off_of(addr)
        if o is None or o + 4 > len(self.data):
            return None
        return struct.unpack_from('<I', self.data, o)[0]

    def string_at(self, addr, maxlen=48):
        o = self.off_of(addr)
        if o is None:
            return None
        raw = self.data[o:o + maxlen].split(b'\0')[0]
        if not raw or not re.fullmatch(rb'[\x20-\x7e]+', raw):
            return None
        return raw.decode('latin1')

    def each_exec_aligned(self, step=2):
        """Yield (addr, halfword) over every executable segment at `step`."""
        for lo, hi, base, _ in self.exe_ranges:
            a0, a1 = base, base + (hi - lo)
            a = a0
            while a < a1:
                o = self.off_of(a)
                if o is not None and o + 2 <= len(self.data):
                    yield a, struct.unpack_from('<H', self.data, o)[0]
                a += step


def thumb2_expand(hw1, hw2):
    """Decode a 32-bit Thumb-2 movw/movt. Returns (kind, rd, imm16) or None."""
    # MOVW: 1111 0x10 0100 imm4 | 0 imm3 Rd imm8   (0xF240-0xF25F)
    # MOVT: 1111 0x10 1100 imm4 | 0 imm3 Rd imm8   (0xF2C0-0xF2DF)
    if (hw1 & 0xFBF0) == 0xF240:
        kind = 'w'
    elif (hw1 & 0xFBF0) == 0xF2C0:
        kind = 't'
    else:
        return None
    i = (hw1 >> 10) & 1
    imm4 = hw1 & 0xF
    imm3 = (hw2 >> 12) & 7
    imm8 = hw2 & 0xFF
    rd = (hw2 >> 8) & 0xF
    imm16 = (imm4 << 12) | (i << 11) | (imm3 << 8) | imm8
    return kind, rd, imm16


def find_refs(img, targets, context=0x40):
    """targets: set of ints. Returns {target: [(kind, addr)]}."""
    hits = {t: [] for t in targets}
    tset = set(targets)

    # (1) absolute dword, over the whole file
    for t in targets:
        pat = struct.pack('<I', t)
        i = img.data.find(pat)
        while i != -1:
            a = img.addr_of(i)
            if a is not None:
                hits[t].append(('dat', a))
            i = img.data.find(pat, i + 1)

    for lo, hi, base, _ in img.exe_ranges:
        step = 2
        a = base
        end = base + (hi - lo)
        while a < end:
            o = img.off_of(a)
            if o is None or o + 4 > len(img.data):
                a += step
                continue
            hw1 = struct.unpack_from('<H', img.data, o)[0]

            # (6) PLT: ARM ldr pc,[pc,#-4]; the literal is the next word
            if img.data[o:o + 4] == PLT_MAGIC and (a & 3) == 0:
                lit = img.word(a + 4)
                if lit is not None:
                    tgt = (lit + 8) & 0xFFFFFFFF
                    if tgt in tset:
                        hits[tgt].append(('plt', a))
                a += 4
                continue

            # (2) Thumb ADR
            if (hw1 & 0xF800) == 0xA000:
                imm = (hw1 & 0x7FF) << 2
                tgt = (((a + 4) & ~3) + imm) & 0xFFFFFFFF
                if tgt in tset:
                    hits[tgt].append(('adr', a))
                a += step
                continue

            # (3) Thumb LDR (literal)
            if (hw1 & 0xF800) == 0x4800:
                imm = (hw1 & 0xFF) << 2
                lit = ((a + 4) & ~3) + imm
                val = img.word(lit)
                if val in tset:
                    hits[val].append(('lit', a))
                a += step
                continue

            # (4)/(5) Thumb-2 movw/movt pair
            if o + 4 <= len(img.data):
                hw2 = struct.unpack_from('<H', img.data, o + 2)[0]
                d1 = thumb2_expand(hw1, hw2)
                if d1 and d1[0] == 'w':
                    # look ahead up to 128B for a matching movt on same reg
                    kind, rd, imm16 = d1
                    full = imm16
                    b = a + 4
                    seen = 0
                    while b < a + 128 and seen < 32:
                        ob = img.off_of(b)
                        if ob is None or ob + 4 > len(img.data):
                            break
                        h1 = struct.unpack_from('<H', img.data, ob)[0]
                        h2 = struct.unpack_from('<H', img.data, ob + 2)[0]
                        d2 = thumb2_expand(h1, h2)
                        if d2 and d2[0] == 't' and d2[1] == rd:
                            full = (d2[2] << 16) | imm16
                            if full in tset:
                                hits[full].append(('movw', a))
                            break
                        b += 2
                        seen += 1
            a += step
    return hits


def tlist(targets):
    return list(targets)


# --- function-start heuristic (for grouping hits) -----------------------


def function_starts(img, limit=None):
    """Approximate set of function entry addresses from prologues."""
    starts = set()
    for lo, hi, base, _ in img.exe_ranges:
        a = base
        end = base + (hi - lo)
        while a < end:
            o = img.off_of(a)
            if o is None or o + 2 > len(img.data):
                a += 2
                continue
            hw = struct.unpack_from('<H', img.data, o)[0]
            # Thumb push {...}: 1011 0101 <reglist>. The reglist occupies
            # bits 0-7 (r0..r7) with LR in bit 8, so test the whole low byte --
            # `push {r4,lr}` is 0xB510 and a low-*nibble* test misses it.
            if (hw & 0xFF00) == 0xB500 and (hw & 0xFF):
                starts.add(a)
            # stmdb sp!, {...,lr}
            if (hw & 0xFF00) == 0xB900 and (hw & 0xFF):
                starts.add(a)
            a += 2
    if limit:
        starts = set(list(starts)[:limit])
    return sorted(starts)


def attribute(starts, addr):
    """Nearest function start <= addr (binary search)."""
    lo, hi = 0, len(starts) - 1
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if starts[mid] <= addr:
            best = starts[mid]
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def find_callers(img, targets, window=0x400):
    """Direct BL/BLX call sites targeting `targets`.

    Sweep method matters here, learned the hard way on 1.1.2_APPS.bin:

    * A single linear capstone sweep over the 19 MB RE segment desyncs on the
      first data island and then reports ZERO real callers. Useless.
    * Resync at each `push {...}` prologue (hw & 0xFF00 == 0xB500 with a
      non-empty reglist, bits 0-7) and decode forward with skipdata=True.
      This finds real callers but still misses any block that is not preceded
      by a recognisable prologue, and it can only see direct calls -- an
      indirect `blx rN` through a vtable/table is invisible to it.
    * Note the reglist is in bits 0-7: `push {r4,lr}` is 0xB510, so testing
      the low *nibble* (as an earlier version did) misses the most common
      prologue in the image.

    So: absence of callers here is a lead, never a proof. Confirm any negative
    result by disassembling the region by hand.
    """
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.skipdata = True
    hits = {t: set() for t in targets}
    tset = set(targets)
    for lo, hi, base, flags in img.exe_ranges:
        blob = img.data[lo:hi]
        n = len(blob)
        a = base
        while a < base + n - 2:
            o = a - base
            hw = struct.unpack_from('<H', blob, o)[0]
            if (hw & 0xFF00) == 0xB500 and (hw & 0xFF):
                for ins in md.disasm(blob[o:o + window], a):
                    if ins.mnemonic in ('bl', 'blx'):
                        m = re.match(r'#(0x[0-9a-f]+)', ins.op_str)
                        if m:
                            t = int(m.group(1), 16)
                            if t in tset:
                                hits[t].add(ins.address)
            a += 2
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('elf')
    ap.add_argument('--str', action='append', default=[],
                    help='string to locate (repeatable)')
    ap.add_argument('--addr', action='append', default=[],
                    help='address in hex, e.g. 0x10aff2e4 (repeatable)')
    ap.add_argument('--vaddr', action='store_true',
                    help='use ELF vaddr instead of paddr (default: paddr)')
    ap.add_argument('--callers', action='append', default=[],
                    help='function address in hex; report direct BL/BLX call sites')
    ap.add_argument('--list-all-offsets', action='store_true',
                    help='also report every file offset of each string')
    args = ap.parse_args()

    img = Image(args.elf)
    if args.vaddr:
        img.segs = load_segments(args.elf, use_paddr=False)
    print(f"# {args.elf}  {len(img.segs)} LOAD segments "
          f"(addr space: {'vaddr' if args.vaddr else 'paddr'})")
    for lo, hi, base, fl in img.segs:
        print(f"#   foff {lo:#x}-{hi:#x}  -> {base:#x}  {fl}")

    targets = {}
    for s in args.str:
        pat = s.encode('latin1')
        offs = [m.start() for m in re.finditer(re.escape(pat), img.data)]
        for o in offs:
            a = img.addr_of(o)
            if a is not None:
                targets[a] = s
                if args.list_all_offsets:
                    print(f"#   str {s!r} at foff {o:#x} addr {a:#x}")
    for a in args.addr:
        targets[int(a, 16)] = a

    if not targets and not args.callers:
        print("no targets resolved (string not found, or outside LOAD segs)")
        return 0

    starts = function_starts(img)

    if args.callers:
        cs = {int(a, 16) for a in args.callers}
        ch = find_callers(img, cs)
        print(f"\n# direct BL/BLX callers (resync sweep; "
              f"indirect vtable calls are invisible -- see find_callers docstring)")
        for t in sorted(cs):
            found = sorted(ch.get(t, []))
            print(f"\n=== callers of {t:#x} : {len(found)} ===")
            for a in found:
                fs = attribute(starts, a)
                print(f"  bl/blx @{a:#x}  fn~{fs:#x}" if fs else f"  bl/blx @{a:#x}")

    if targets:
        print(f"\n# {len(targets)} target(s): " +
              ", ".join(f"{a:#x}({s!r})" for a, s in sorted(targets.items())))
        hits = find_refs(img, set(targets))

        for t in sorted(targets):
            found = hits.get(t, [])
            print(f"\n=== target {t:#x} {targets[t]!r} : {len(found)} hit(s) ===")
            for kind, a in sorted(set(found), key=lambda x: x[1]):
                if kind == 'dat':
                    print(f"  dat  @{a:#x}  (table/struct pointer, not an instruction)")
                    continue
                fs = attribute(starts, a)
                near = f" fn~{fs:#x}" if fs else ""
                s = img.string_at(t)
                print(f"  {kind:<5} @{a:#x}{near}" + (f"  -> {s!r}" if s else ""))
    return 0


if __name__ == '__main__':
    sys.exit(main())
