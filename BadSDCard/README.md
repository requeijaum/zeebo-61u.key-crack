# BadSDCard — the card artifact, built and verified

The SD slot is the only input the console takes from outside without a signature,
and the platform reads it before any authentication. This directory describes the
artifact that exercises that path, what has been verified about it, and what has
not.

**What this is:** a FAT32 image with the known auto-copy marker, sentinel files,
and (in the `lfn` profile) long file names that overrun a fixed 128-byte stack
buffer when passed to the firmware's own copy routines.

**What this is not:** a working exploit. The copy mechanism is proven against the
firmware's own machine code under emulation. The *trigger* — whether a name taken
from the card ever reaches those routines — is still unproven, and notes §45
records why: the marker string has no static reference in the image.

---

## 1. Artifacts

Built by `tools/bad_sd.py`; the images themselves are regenerable and are not
committed (they are 256 MB each).

| Image | Profile | FAT | Size | SHA-256 (first 16) | Asks |
|---|---|---|---|---|---|
| `out/probe16.raw` | probe | 16 | 64 MB | `d6969b0c83a899f4` | does the platform copy anything at all? (period-correct card) |
| `out/probe.raw` | probe | 32 | 256 MB | `40ad1ecef90a0a5c` | same question, if the driver wants FAT32 |
| `out/lfn16.raw` | lfn | 16 | 64 MB | `18d9ce477f915974` | long-name baits, FAT16 |
| `out/lfn.raw` | lfn | 32 | 256 MB | `0970b47411661285` | long-name baits, FAT32 |
| `out/wide16.raw` | wide | 16 | 64 MB | `38be0cb363c937fe` | long names in **seven** candidate scan locations at once |

`wide` is the profile to run when only one bench session is possible: it plants a
200-character name in the root, `/longcheerzeebo`, `/mif`, `/mod`, `/img`,
`/lctsys`, `/DCIM`, `/tmp` and in a root-level long-named directory, so the run
answers "does any scan location reach a copy routine" instead of "which one".
The cost is that a crash does not localise the directory.

Both filesystems are valid by construction: `fsck.vfat -n` accepts every image and
`mdir` lists every tree. The MBR variants (`--layout mbr`) are one command away
and are not kept on disk, because the laptop has 8 GB free and each 256 MB image
costs a full minute of disk.

Rebuild any of them:

```
python3 tools/bad_sd.py build --profile probe --fat 16 --size-mb 64 --out out/probe16.raw
python3 tools/bad_sd.py build --profile lfn --out out/lfn.raw --manifest out/lfn.json
python3 tools/bad_sd.py build --profile probe --layout mbr --out out/probe-mbr.raw
python3 tools/bad_sd.py build --profile qx --app-dir ../payload --out out/qx.raw
python3 tools/bad_sd.py verify out/probe16.raw --fat 16
```

`--profile qx` copies an application tree the operator supplies; no payload is
bundled here on purpose.

---

## 2. What is in the image

| Path | Purpose |
|---|---|
| `/longcheerzeebo/autocopysdcardinfotoenand.dat` | the marker the firmware names, empty by design |
| `/zzprobe.txt` | sentinel: 15 known bytes, to see whether any copy reaches internal storage |
| `/mif/ZZPROBE.mif` | sentinel inside a partition the platform already writes |
| `/mif/<200 chars>.mif` | long-name bait (lfn profile only) |
| `/mif/GOOD.mif` | short-name control beside the bait |
| `/mod/<200 chars>/<200 chars>.mod` | long-name directory and module baits |
| `/mod/GOODAPP/GOOD.mod` | short-name control |
| `/61u.key` | 14 `A` bytes, negative control (only with `--with-key`) |

Both profiles avoid any file whose content could be executed: the baits hold
zeros, and the marker is empty.

---

## 3. Verification performed

Structural, with two independent readers:

```
$ python3 tools/bad_sd.py build --profile probe --out out/probe.raw
wrote out/probe.raw (268435456 bytes, probe/super)
sha256 40ad1ecef90a0a5cc48dc5066338c193abd266b6b97f62b40671a83d3e2ee291
  fsck.vfat: out/probe.raw: 6 files, 5/130554 clusters
  mdir: readable (3 entries in root)
```

`fsck.vfat` validates FAT chains, directory entries and long-name checksums; a
filesystem it accepts is not malformed. `mdir` independently lists the tree,
including the 200-character names.

For the MBR layout, `fsck.vfat` has no offset option here, so the tool slices the
volume out and verifies that; the partition table itself is checked structurally.
That is stated rather than hidden.

Mechanism, against the firmware's own code:

```
$ python3 -P tools/test_evil_unicorn.py out/wide16.raw
  len=204 strcat=SMASH strcpy=SMASH  AAAAAAAAAAAAAAAAAAAAAAAA...
  len=200 strcat=SMASH strcpy=SMASH  AAAAAAAAAAAAAAAAAAAAAAAA...
12/12 long names smash a 128B stack buffer.
Mechanism proven with the firmware's own bytes: a long name overruns a 128-byte stack buffer.
NOT proven: that an SD-derived name reaches these functions (notes §20/§45).
```

and on the FAT32 image, same result:

```
$ python3 -P tools/test_evil_unicorn.py out/lfn.raw
LFN names in image: 11
  len=204 strcat=SMASH strcpy=SMASH  AAAAAAAAAAAAAAAAAAAAAAAA...
  len=200 strcat=SMASH strcpy=SMASH  AAAAAAAAAAAAAAAAAAAAAAAA...
  len=204 strcat=SMASH strcpy=SMASH  AAAAAAAAAAAAAAAAAAAAAAAA...
3/3 long names smash a 128B stack buffer.
Mechanism proven with the firmware's own bytes: a long name overruns a 128-byte stack buffer.
NOT proven: that an SD-derived name reaches these functions (notes §20/§45).
```

The two routines are `0x1079BFF4` (word-at-a-time copy) and `0x101D7F48`
(concatenate), executed as Thumb from `1.1.2_APPS.bin` with a 128-byte stack
buffer and a canary past it. The names come from the image, parsed as FAT.

---

## 4. Bench procedure

Writing to physical media is the operator's step. The agent builds images; it does
not touch block devices.

1. Write the image: `dd if=out/probe.raw of=/dev/sdX bs=4M status=progress conv=fsync`.
2. Console off, card in, console on. Observe: boot completes? menu? anything copied?
3. Compare with the same run without a card.
4. Remove the card before every power change.

Order of tests matches `HARDWARE_TODO.md`:

| Test | Image | Question |
|---|---|---|
| 1  | `probe16.raw` + `61u.key` (`--with-key`) | does a 14-byte key file open anything? (expected: no) |
| 4b | `probe16.raw`, then `probe.raw` | does the platform copy from the card at all — and in which FAT variant? |
| 8  | `wide16.raw` alone, or `lfn16.raw` then `lfn.raw` | does a long name reach a copy routine and crash? |

Run the FAT16 card first: a 2011 handheld is more likely to have been shipped with,
and tested against, a FAT16 card, and a FAT16 image is 64 MB, so a small card is
enough.

---

## 5. Hazard

If the copy feature does run, the contents of this card land on the **internal**
partition, in `/mod` and `/mif`. Those are the partitions the shell loads its own
files from, so a card that installs something malformed can leave a console whose
shell fails to start.

- Recovery from a boot loop: remove the card and power cycle.
- Recovery from a *copied* bad file: unknown. There is no NAND reflash image for
  this unit in the project, so a console that copied a corrupting file may stay
  broken.

Run the `probe` profile before the `lfn` profile, always. The `probe` card asks
whether copying happens without asking it to happen with hostile names.

---

## 6. Open questions

1. Does the platform copy from the card in this firmware, and under what trigger?
   The marker string exists but nothing references it. The copy module's message
   blob at `0x1035AE00` names the operations — create `/mif`, create `/mod`,
   `CopyBrewAppletInto…` — and its logger is called from a wrapper at
   `0x10359F9C`; what is still missing is the entry point that starts a copy.
2. Does the driver require an MBR, a superfloppy, or both? Both images exist for
   that reason.
3. Which partition does a copy touch — `/mod`, `/mif`, or both? The image puts a
   sentinel in each.
4. Is the long-name path actually reached, and if so, from which directory scan?
5. Is the card expected to be FAT32, or would a 2011-era machine prefer FAT16? Both
   are built now, so this is answered by the bench run rather than guessed.
6. Which directory does the copy read — the root, `/mif`, or `/mod`? The sentinels
   are placed in all three.

---

## 7. Tooling notes

- `tools/dis.py` shadows the standard library module of the same name. Any script
  in `tools/` that imports something reaching `inspect` (unicorn does) must run as
  `python3 -P tools/<script>.py`, or the import fails with a `dis` attribute
  error. `tools/bad_sd.py` avoids `dataclasses` for the same reason.
- `tools/make_evil_sd.py` is the earlier builder, superseded by `bad_sd.py`: it
  writes a partition table that `fsck.fat` refuses to recognise, so its images
  could not be verified independently.
