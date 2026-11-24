#!/usr/bin/env python3
"""bad_sd.py — build and verify a Zeebo SD card image for delivery tests.

The card is the only input the console accepts from outside without a signature,
so it is the delivery vehicle for the data-file route (notes §40/§45). This tool
produces the image; writing it to physical media is the operator's step.

What it does NOT claim
----------------------
There is no proven code-execution path on the card. What is measured:

  * the platform mounts the card as `card0` and has a FAT driver (FAT12/16/32),
  * a copy feature exists whose logs live at `fs:/mcp/lctsys/sdautocopy.log`,
  * the marker path `fs:/card0/longcheerzeebo/autocopysdcardinfotoenand.dat`
    exists in the image but has no static reference, so the trigger is unknown.

So an image built here is an *experiment*, not an exploit. `probe` asks the
cheapest question (does anything get copied); `lfn` adds the long-name bait for
the parser hypothesis; `qx` adds an application tree the operator supplies.

Layouts
-------
`super`  — volume boot record at sector 0 (no partition table).
`mbr`    — MBR at sector 0, volume at sector 32.

Both are produced because the console's driver behaviour is unmeasured; the
superfloppy form is the one `fsck.vfat` can verify end to end here.

Verification
------------
The builder re-parses what it wrote, and optionally runs `fsck.vfat -n` and
`mdir` when they exist. An image that fails verification is never written.

Usage
-----
    python3 tools/bad_sd.py build --profile probe --out out/probe.raw
    python3 tools/bad_sd.py build --profile lfn --out out/lfn.raw --size-mb 256
    python3 tools/bad_sd.py build --profile qx --app-dir ../payload --out out/qx.raw
    python3 tools/bad_sd.py verify out/probe.raw

Writing to a card (operator, elsewhere — never from the agent):

    sudo dd if=out/probe.raw of=/dev/sdX bs=4M status=progress conv=fsync
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

SECTOR = 512
PART_START = 32  # sector, MBR layout only
MARKER_DIR = "longcheerzeebo"
MARKER_FILE = "autocopysdcardinfotoenand.dat"

# ---------------------------------------------------------------- helpers ----


def lfn_checksum(alias11: bytes) -> int:
    s = 0
    for c in alias11:
        s = (((s & 1) << 7) + (s >> 1) + c) & 0xFF
    return s


def short_alias(longname: str, counter: int) -> bytes:
    base, _, ext = longname.rpartition(".")
    if not base:
        base, ext = longname, ""
    clean = lambda s: "".join(c.upper() if c.isalnum() else "_" for c in s)
    stem = (clean(base)[:6] + f"~{counter}")[:8].ljust(8)
    return (stem + clean(ext)[:3].ljust(3)).encode("ascii")


def lfn_entries(longname: str, alias11: bytes) -> bytes:
    units = [ord(c) for c in longname] + [0x0000]
    n = (len(units) + 12) // 13
    units += [0xFFFF] * (n * 13 - len(units))
    chk = lfn_checksum(alias11)
    out = bytearray()
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
        out += e
    return bytes(out)


def short_entry(alias11: bytes, attr: int, cluster: int, size: int) -> bytes:
    assert len(alias11) == 11, f"alias must be 11 bytes: {alias11!r}"
    e = bytearray(32)
    e[0:11] = alias11
    e[11] = attr
    e[20:22] = struct.pack("<H", (cluster >> 16) & 0xFFFF)
    e[26:28] = struct.pack("<H", cluster & 0xFFFF)
    e[28:32] = struct.pack("<I", size)
    return bytes(e)


# ------------------------------------------------------------------ image ----


class Entry:
    """Plain class on purpose: `tools/dis.py` shadows the stdlib `dis`, so any
    import chain that reaches `dataclasses` (via `inspect`) explodes here."""

    __slots__ = ("path", "kind", "size", "cluster", "note")

    def __init__(self, path: str, kind: str, size: int, cluster: int, note: str = ""):
        self.path = path
        self.kind = kind
        self.size = size
        self.cluster = cluster
        self.note = note


class Fat32:
    def __init__(self, size_mb: int, layout: str = "super", spc: int = 4,
                 reserved: int = 32):
        if layout not in ("super", "mbr"):
            raise ValueError("layout must be super or mbr")
        self.layout = layout
        self.base = 0 if layout == "super" else PART_START
        self.total = size_mb * 1024 * 1024 // SECTOR
        self.spc = spc
        self.reserved = reserved

        fat = 256
        for _ in range(4):
            clusters = (self.total - self.base - reserved - 2 * fat) // spc
            fat = (clusters * 4 + SECTOR - 1) // SECTOR
        self.fat_sectors = fat
        self.data_start = self.base + reserved + 2 * fat
        self.nclusters = (self.total - self.data_start) // spc
        if self.nclusters < 65525:
            raise ValueError(
                f"{size_mb} MB gives {self.nclusters} clusters; FAT32 needs >= 65525 "
                "(use --size-mb 256 or larger)")

        self.buf = bytearray(self.total * SECTOR)
        self.fat = [0] * (self.nclusters + 2)
        self.fat[0] = 0x0FFFFFF8
        self.fat[1] = 0x0FFFFFFF
        self.fat[2] = 0x0FFFFFFF  # root
        self.next_free = 3
        self.dirs: dict[int, bytearray] = {}
        self.counter = 1
        self.entries: list[Entry] = []

    # -- allocation ----------------------------------------------------------

    def alloc(self, nclus: int) -> int:
        start = self.next_free
        for i in range(nclus):
            self.fat[start + i] = start + i + 1
        self.fat[start + nclus - 1] = 0x0FFFFFFF
        self.next_free += nclus
        if self.next_free > self.nclusters + 2:
            raise ValueError("image full")
        return start

    def clus_off(self, c: int) -> int:
        return (self.data_start + (c - 2) * self.spc) * SECTOR

    def write_data(self, start: int, data: bytes) -> None:
        c, off = start, 0
        while off < len(data):
            chunk = data[off:off + self.spc * SECTOR]
            self.buf[self.clus_off(c):self.clus_off(c) + len(chunk)] = chunk
            off += len(chunk)
            c = self.fat[c]

    # -- directory entries ---------------------------------------------------

    def add(self, parent: bytearray, name: str, is_dir: bool, content: bytes = b"",
            parent_clus: int = 0, note: str = "", path: str = "") -> int:
        if is_dir:
            start = self.alloc(1)
            self.dirs[start] = bytearray(
                short_entry(b".          ", 0x10, start, 0)
                + short_entry(b"..         ", 0x10, parent_clus, 0))
            size = 0
        elif content:
            nclus = (len(content) + self.spc * SECTOR - 1) // (self.spc * SECTOR)
            start = self.alloc(max(1, nclus))
            self.write_data(start, content)
            size = len(content)
        else:
            start, size = 0, 0

        alias = short_alias(name, self.counter)
        self.counter += 1
        parent += lfn_entries(name, alias)
        parent += short_entry(alias, 0x10 if is_dir else 0x20, start, size)
        self.entries.append(Entry(path or name, "dir" if is_dir else "file", size,
                                  start, note))
        return start

    def finalize(self, root: bytearray, label: str) -> bytes:
        nsec = max(1, (len(root) + self.spc * SECTOR - 1) // (self.spc * SECTOR))
        # extend the root chain (starts at cluster 2)
        c = 2
        for _ in range(nsec - 1):
            self.fat[c] = self.next_free
            c = self.next_free
            self.next_free += 1
        self.fat[c] = 0x0FFFFFFF
        self.write_data(2, bytes(root))

        for start, data in self.dirs.items():
            n = max(1, (len(data) + self.spc * SECTOR - 1) // (self.spc * SECTOR))
            c = start
            for _ in range(n - 1):
                self.fat[c] = self.next_free
                c = self.next_free
                self.next_free += 1
            self.fat[c] = 0x0FFFFFFF
            self.write_data(start, bytes(data))

        fatbin = struct.pack(f"<{len(self.fat)}I", *self.fat)
        fatbin = fatbin[:self.fat_sectors * SECTOR].ljust(self.fat_sectors * SECTOR, b"\x00")
        for i in range(2):
            off = (self.base + self.reserved + i * self.fat_sectors) * SECTOR
            self.buf[off:off + len(fatbin)] = fatbin

        vbr = self._vbr(label)
        self.buf[self.base * SECTOR:(self.base + 1) * SECTOR] = vbr
        self.buf[(self.base + 6) * SECTOR:(self.base + 7) * SECTOR] = vbr  # backup
        self.buf[(self.base + 1) * SECTOR:(self.base + 2) * SECTOR] = self._fsinfo()

        if self.layout == "mbr":
            self.buf[0:SECTOR] = self._mbr()
        return bytes(self.buf)

    # -- metadata structures -------------------------------------------------

    def _vbr(self, label: str) -> bytes:
        b = bytearray(SECTOR)
        b[0:3] = b"\xeb\x58\x90"
        b[3:11] = b"ZEEBOSD "
        struct.pack_into("<H", b, 11, SECTOR)
        b[13] = self.spc
        struct.pack_into("<H", b, 14, self.reserved)
        b[16] = 2
        b[21] = 0xF8
        struct.pack_into("<H", b, 24, 63)
        struct.pack_into("<H", b, 26, 255)
        struct.pack_into("<I", b, 28, self.base)                 # hidden sectors
        struct.pack_into("<I", b, 32, self.total - self.base)    # total sectors
        struct.pack_into("<I", b, 36, self.fat_sectors)
        struct.pack_into("<H", b, 40, 0)                         # ext flags
        struct.pack_into("<H", b, 42, 0)                         # fs version
        struct.pack_into("<I", b, 44, 2)                         # root cluster
        struct.pack_into("<H", b, 48, 1)                         # fsinfo sector
        struct.pack_into("<H", b, 50, 6)                         # backup boot sector
        b[64] = 0x80
        b[66] = 0x29
        struct.pack_into("<I", b, 67, 0x6BEEF00D)
        b[71:82] = (label[:11]).ljust(11).encode("ascii")
        b[82:90] = b"FAT32   "
        b[510:512] = b"\x55\xaa"
        return bytes(b)

    def _fsinfo(self) -> bytes:
        fi = bytearray(SECTOR)
        fi[0:4] = b"RRaA"
        fi[484:488] = b"rrAa"
        free = sum(1 for x in self.fat[2:] if x == 0)
        struct.pack_into("<I", fi, 488, free)
        struct.pack_into("<I", fi, 492, self.next_free)
        fi[510:512] = b"\x55\xaa"
        return bytes(fi)

    def _mbr(self) -> bytes:
        m = bytearray(SECTOR)
        m[446] = 0x80                      # boot flag
        m[446 + 1:446 + 4] = b"\xfe\xff\xff"  # CHS start (ignored, kept sane)
        m[446 + 4] = 0x0C                  # FAT32 LBA
        m[446 + 5:446 + 8] = b"\xfe\xff\xff"  # CHS end
        struct.pack_into("<I", m, 446 + 8, self.base)
        struct.pack_into("<I", m, 446 + 12, self.total - self.base)
        m[510:512] = b"\x55\xaa"
        return bytes(m)


# ---------------------------------------------------------------- profiles ---


def profile_probe(img: Fat32, with_key: bool) -> bytearray:
    """Cheapest question: does the platform copy anything at all?"""
    root = bytearray()
    root += short_entry(b"ZEEBOSD    ", 0x08, 0, 0)  # volume label, 11 chars

    if with_key:
        start = img.alloc(1)
        img.write_data(start, b"A" * 14)
        root += short_entry(b"61U     KEY", 0x20, start, 14)
        img.entries.append(Entry("/61u.key", "file", 14, start, "negative control (14xA)"))

    start = img.alloc(1)
    payload = b"BADSD probe v1\n"
    img.write_data(start, payload)
    root += short_entry(b"ZZPROBE TXT", 0x20, start, len(payload))
    img.entries.append(Entry("/zzprobe.txt", "file", len(payload), start,
                             "sentinel: does any copy reach internal storage?"))

    mk = img.add(root, MARKER_DIR, True, note="marker directory (copy trigger)",
                 path="/" + MARKER_DIR)
    img.add(img.dirs[mk], MARKER_FILE, False, b"", parent_clus=mk,
            note="known marker path, empty by design",
            path=f"/{MARKER_DIR}/{MARKER_FILE}")

    mif = img.add(root, "mif", True, note="game data partition", path="/mif")
    data = b"\x00" * 64
    img.add(img.dirs[mif], "ZZPROBE.mif", False, data, parent_clus=mif,
            note="sentinel inside a partition the platform writes",
            path="/mif/ZZPROBE.mif")
    return root


def profile_lfn(img: Fat32, with_key: bool, name_len: int = 200) -> bytearray:
    """Adds long-name baits for the parser hypothesis (unproven)."""
    root = profile_probe(img, with_key)
    long = "A" * name_len

    # locate the mif directory by its entry record
    mif_clus = next(e.cluster for e in img.entries if e.path == "/mif")
    img.add(img.dirs[mif_clus], long + ".mif", False, b"\x00" * 64,
            parent_clus=mif_clus, note=f"{name_len}-char LFN in /mif",
            path=f"/mif/{long}.mif")
    img.add(img.dirs[mif_clus], "GOOD.mif", False, b"\x00" * 64,
            parent_clus=mif_clus, note="control file, short name", path="/mif/GOOD.mif")

    mod = img.add(root, "mod", True, note="module partition", path="/mod")
    app = img.add(img.dirs[mod], long, True, parent_clus=mod,
                  note=f"{name_len}-char directory name", path=f"/mod/{long}")
    img.add(img.dirs[app], long + ".mod", False, b"\x00" * 64, parent_clus=app,
            note=f"{name_len}-char module name", path=f"/mod/{long}/{long}.mod")
    good = img.add(img.dirs[mod], "GOODAPP", True, parent_clus=mod,
                   note="control directory", path="/mod/GOODAPP")
    img.add(img.dirs[good], "GOOD.mod", False, b"\x00" * 64, parent_clus=good,
            note="control module", path="/mod/GOODAPP/GOOD.mod")
    return root


def profile_qx(img: Fat32, app_dir: Path, with_key: bool) -> bytearray:
    """lfn profile plus a real application tree supplied by the operator."""
    if not app_dir.is_dir():
        raise SystemExit(f"--app-dir {app_dir} is not a directory")
    root = profile_lfn(img, with_key)
    mod_clus = next(e.cluster for e in img.entries if e.path == "/mod")
    app_name = app_dir.name
    app = img.add(img.dirs[mod_clus], app_name, True, parent_clus=mod_clus,
                  note="application directory copied from --app-dir",
                  path=f"/mod/{app_name}")
    for src in sorted(app_dir.rglob("*")):
        rel = src.relative_to(app_dir)
        if src.is_dir():
            parent = app
            path = f"/mod/{app_name}"
            for part in rel.parts:
                path += "/" + part
                parent = img.add(img.dirs[parent], part, True, parent_clus=parent,
                                 note="directory from --app-dir", path=path)
        else:
            data = src.read_bytes()
            parent_clus = app
            for part in rel.parts[:-1]:
                parent_clus = next(e.cluster for e in img.entries
                                   if e.path.endswith("/" + part) and e.kind == "dir")
            img.add(img.dirs[parent_clus], src.name, False, data,
                    parent_clus=parent_clus, note="file from --app-dir",
                    path=f"/mod/{app_name}/{rel}")
    return root


# ------------------------------------------------------------ verification ---


def verify_internal(data: bytes, layout: str) -> list[str]:
    errs: list[str] = []
    base = 0 if layout == "super" else PART_START

    if len(data) % SECTOR:
        errs.append("size not a multiple of 512")
    if data[510:512] != b"\x55\xaa":
        errs.append("sector 0 signature missing")

    if layout == "mbr":
        ptype = data[446 + 4]
        start = struct.unpack("<I", data[446 + 8:446 + 12])[0]
        if ptype != 0x0C:
            errs.append(f"partition type {ptype:#x} is not 0x0C")
        if start != PART_START:
            errs.append(f"partition starts at {start}, expected {PART_START}")

    vbr = data[base * SECTOR:(base + 1) * SECTOR]
    if vbr[510:512] != b"\x55\xaa":
        errs.append("VBR signature missing")
    bps, spc, rsv, nfats = struct.unpack("<HBHB", vbr[11:17])
    if bps != SECTOR:
        errs.append(f"bytes per sector {bps}")
    if (spc, nfats) != (4, 2):
        errs.append(f"geometry spc={spc} fats={nfats}")
    if vbr[82:90] != b"FAT32   ":
        errs.append("filesystem type field is not FAT32")
    fat_sz = struct.unpack("<I", vbr[36:40])[0]
    if struct.unpack("<I", vbr[44:48])[0] != 2:
        errs.append("root cluster is not 2")

    fat_off = (base + rsv) * SECTOR
    fat = struct.unpack(f"<{fat_sz * SECTOR // 4}I", data[fat_off:fat_off + fat_sz * SECTOR])
    data_start = base + rsv + 2 * fat_sz

    def chain(c: int) -> list[int]:
        out, seen = [], set()
        while c < 0x0FFFFFF8:
            if c < 2 or c in seen:
                raise ValueError(f"bad chain at {c}")
            seen.add(c)
            out.append(c)
            c = fat[c]
        return out

    def read_dir(c: int) -> list[bytes]:
        raw = b""
        for cc in chain(c):
            off = (data_start + (cc - 2) * spc) * SECTOR
            raw += data[off:off + spc * SECTOR]
        out = []
        for i in range(0, len(raw), 32):
            e = raw[i:i + 32]
            if len(e) < 32 or e[0] == 0x00:
                break
            if e[0] == 0xE5:
                continue
            out.append(e)
        return out

    def walk(c: int, prefix: str, depth: int = 0) -> None:
        if depth > 8:
            errs.append(f"{prefix}: too deep")
            return
        pending: list[bytes] = []
        for e in read_dir(c):
            if e[11] == 0x0F:
                pending.append(e)
                continue
            alias = e[0:11]
            attr = e[11]
            clus = struct.unpack("<H", e[26:28])[0] | (struct.unpack("<H", e[20:22])[0] << 16)
            size = struct.unpack("<I", e[28:32])[0]
            if pending:
                seqs = [x[0] & 0x1F for x in pending]
                if seqs != list(range(len(pending), 0, -1)):
                    errs.append(f"{prefix}: LFN sequence broken")
                if pending[0][13] != lfn_checksum(alias):
                    errs.append(f"{prefix}: LFN checksum mismatch")
                pending.clear()
            name = alias.decode("ascii", "replace").strip()
            if attr & 0x10 and alias not in (b".          ", b"..         "):
                walk(clus, f"{prefix}{name}/", depth + 1)
            elif size and not chain(clus):
                errs.append(f"{prefix}{name}: empty chain for non-zero size")
            elif size:
                try:
                    if len(chain(clus)) * spc * SECTOR < size:
                        errs.append(f"{prefix}{name}: chain shorter than size")
                except ValueError as exc:
                    errs.append(f"{prefix}{name}: {exc}")

    try:
        walk(2, "/")
    except ValueError as exc:
        errs.append(f"root: {exc}")
    return errs


def verify_tools(path: Path, layout: str) -> list[str]:
    """Independent checks with fsck.fat and mtools, when installed."""
    notes: list[str] = []
    if shutil.which("fsck.vfat"):
        target = path
        tmp = None
        if layout == "mbr":
            tmp = Path(tempfile.mkstemp(suffix=".raw")[1])
            with open(path, "rb") as src, open(tmp, "wb") as dst:
                src.seek(PART_START * SECTOR)
                while True:
                    chunk = src.read(1 << 20)
                    if not chunk:
                        break
                    dst.write(chunk)
            target = tmp
        res = subprocess.run(["fsck.vfat", "-n", str(target)],
                             capture_output=True, text=True)
        out = (res.stdout + res.stderr).strip()
        notes.append("fsck.vfat: " + out.splitlines()[-1])
        if res.returncode != 0:
            notes.append("fsck.vfat reported problems (see above)")
        if tmp:
            tmp.unlink()
    else:
        notes.append("fsck.vfat not installed: structural check only")

    if shutil.which("mdir"):
        spec = str(path) if layout == "super" else f"{path}@@{PART_START * SECTOR}"
        res = subprocess.run(["mdir", "-i", spec, "::"], capture_output=True, text=True)
        if res.returncode != 0:
            notes.append("mdir could not read the image")
        else:
            files = sum(1 for ln in res.stdout.splitlines() if "<DIR>" in ln or " TXT" in ln)
            notes.append(f"mdir: readable ({files} entries in root)")
    return notes


# ------------------------------------------------------------------- build ---


def build(args) -> tuple[bytes, dict]:
    img = Fat32(args.size_mb, layout=args.layout)
    if args.profile == "probe":
        root = profile_probe(img, args.with_key)
    elif args.profile == "lfn":
        root = profile_lfn(img, args.with_key, args.name_len)
    else:
        root = profile_qx(img, Path(args.app_dir), args.with_key)

    data = img.finalize(root, args.label)
    manifest = {
        "profile": args.profile,
        "layout": args.layout,
        "size_mb": args.size_mb,
        "label": args.label,
        "sha256": hashlib.sha256(data).hexdigest(),
        "entries": [{"path": e.path, "kind": e.kind, "size": e.size,
                     "cluster": e.cluster, "note": e.note} for e in img.entries],
        "marker": f"/{MARKER_DIR}/{MARKER_FILE}",
        "notes": [
            "no code-execution path is proven for this image",
            "writing this to physical media is the operator's step, not the agent's",
        ],
    }
    return data, manifest


def cmd_build(args) -> int:
    data, manifest = build(args)
    errs = verify_internal(data, args.layout)
    if errs:
        print("VERIFY FAILED, image not written:")
        for e in errs:
            print("  -", e)
        return 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    manifest["fsck"] = verify_tools(out, args.layout)
    if args.manifest:
        Path(args.manifest).write_text(json.dumps(manifest, indent=2))
    print(f"wrote {out} ({out.stat().st_size} bytes, {args.profile}/{args.layout})")
    print(f"sha256 {manifest['sha256']}")
    for note in manifest["fsck"]:
        print(" ", note)
    print(f"entries {len(manifest['entries'])}")
    return 0


def cmd_verify(args) -> int:
    path = Path(args.image)
    data = path.read_bytes()
    layout = args.layout
    if layout == "auto":
        layout = "mbr" if data[446 + 4] in (0x0C, 0x0B) and data[446 + 8:446 + 12] != b"\x00" * 4 else "super"
    errs = verify_internal(data, layout)
    print(f"layout {layout}")
    for e in errs:
        print("  BAD:", e)
    for note in verify_tools(path, layout):
        print(" ", note)
    print("VERIFY OK" if not errs else f"VERIFY FAILED ({len(errs)})")
    return 0 if not errs else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="build an image")
    b.add_argument("--profile", choices=["probe", "lfn", "qx"], default="probe")
    b.add_argument("--layout", choices=["super", "mbr"], default="super")
    b.add_argument("--size-mb", type=int, default=256)
    b.add_argument("--name-len", type=int, default=200)
    b.add_argument("--with-key", action="store_true",
                   help="add a 61u.key negative control")
    b.add_argument("--app-dir", help="application tree for the qx profile")
    b.add_argument("--label", default="ZEEBOSD")
    b.add_argument("--out", required=True)
    b.add_argument("--manifest")
    b.set_defaults(func=cmd_build)

    v = sub.add_parser("verify", help="re-parse and check an image")
    v.add_argument("image")
    v.add_argument("--layout", choices=["auto", "super", "mbr"], default="auto")
    v.set_defaults(func=cmd_verify)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
