# RE Notes — 61u.key validation

## 1. String references (APPS.bin, `firmware/strings_1.1.2_APPS.txt`)

| String | Line(s) | Meaning |
|--------|---------|---------|
| `fs:/mcp/61u.key` | 94917 | internal NAND key path, checked first |
| `fs:/card0/61u.key` | 94918 | SD card key path, checked second |
| `lctsys/61s.dat` | 124178 | related file read in same function |
| `/61u.key` | 124179 | fallback/suffix match |
| `lctsys/imsi.dat` | 124170 | IMSI provisioning file nearby |
| `fs:/mcp/lctsys/61s.dat` | 220729 | absolute 61s.dat path |
| `..\..\apps\LCTUtility\src\OEM_LCTSystemCtl.c` | 171491 | source file of validation logic |
| `Could not start AEECLSID_AUXSETTINGS applet` | 90811 | DIAG enable path via AUXSETTINGS |
| `cannot find card0 usb.key` / `we found the usb.key in card0` | strings_61u lines 220-221 | parallel `usb.key` mechanism, same card0 pattern |

No `61u.key` references exist in AMSS.bin (modem side) — validation is
ARM11/BREW-side only. AMSS has the WMS/QMI stack (SMS path) but no key logic.

## 2. Validation function (`re/thumb_61u_func1.asm`)

- Thumb function at `0x1078c8d0` (APPS.bin linked address, base `0x10000000`).
- Prologue `push {r4-r7,lr} / sub sp,#12`; repeated BREW-style error branches
  calling `0x1083f22c` (likely `DBGPRINTF`/`AEECLSID` log) then cleanup via
  `0x1083f2d0` (release) / `0x1083f2c0` (alloc) — classic IFILEMGR open/read
  scaffolding, not crypto.
- Two near-identical halves: first uses struct offset `+44` (`0x2c`), second
  `+40` (`0x28`) — the two key paths (`/mcp` then `/card0`). Each half:
  open file → null checks → `IFILE_Read` via vtable (`ldr r3,[r2]; blx r3`)
  → validate buffer → enable DIAG via AUXSETTINGS vtable call (`+84 = 0x54`).
- Magic event codes compared as halfwords: `0x97`, then `0x97-0xFF-0x0B`;
  second half: `0xA9`, then `0xA9-0xFF-0x24`. These gate the AUXSETTINGS call.
- Verdict: the function checks key **presence + format**, then enables DIAG
  USB SER1 until reboot. No RSA/ECDSA/HMAC verify visible in this function —
  the actual key↔console binding (if any) is either a plain comparison
  against `61s.dat`/provisioned data or lives in the TecToy-side keygen tool
  (not in firmware). Ghidra decompilation still pending to confirm.

## 3. Dead end: `re/thumb_61u_validation.asm`

- Disassembly starting at `0x10bff2f5` is **misaligned garbage**
  (`movs r1,r1`, `strh r0,[r0,#32]` …) — that address is mid-instruction,
  not a function entry. The PLAN.md reference to `~0x10bff2f5` as a "second
  ref" should be re-derived from the `61u.key` string xrefs in Ghidra.
  The real entry point found so far is `0x1078c8d0`.

## 4. EFS2 / `61s.dat` status

- **CORRECTION (2026-09-27, wiki mirror): `61s.dat` is the SIM PIN, not key
  material.** TripleOxygen wiki (`docs/tripleoxygen_wiki_61s.md`): "Este
  arquivo contém o código PIN do SIM card de seu Zeebo. É um arquivo de
  texto contendo um número de 4 algarismos." It is read by nearby SIM code
  (`dsatparm.c`, next to `lctsys/imsi.dat`), not by the key check. Earlier
  "hash/salt/state" guesses in PLAN.md/README.md are retired.
- `nand.py` model (zeebx-emu): dirent `ref` indexes a `u32` page table;
  confirmed for `tectoy.ttf` (13/94 pages match known copy at base
  `0x4c23104`, then diverges — old generation; current map = base + journal).
- Raw scan of `firmware/part_EFS2APPS.bin`: **18 copies** of the `61s.dat`
  dirent, all with `ref=0x1bff8`. At the known table base the entry is
  `0xffffffff` (deleted). Content not recoverable from this generation.
- Prior recovery attempt lives on the SD card at
  `/media/.../zeebo/ROMs/debug_nand/_efs2_recovered/` (`efs2_tree.txt`,
  `chain_manifest.tsv`, dated 2026-09-11): `/lctsys` node found
  (`inode=0x67`) but with **no children recovered**; `mcp/` and `card0/`
  extractions are empty. Note: that tree maps `inode 0x1bff8` to
  `/mif/flixfile.dat` — generations are mixed, so inode↔name is not 1:1.
  No further EFS2 work planned: the file is just the SIM PIN.
- **Data scarcity explained** (hospital wiki): on unlock, the Hospital
  *removes* the `61u.key` so DIAG stays always on. Keys exist only on
  still-locked consoles and are harvestable solely via JTAG — hence ~10
  known pairs. Target locked-console owners (Telegram groups), not owners
  of already-unlocked consoles.
- Wiki mirrors archived in `docs/tripleoxygen_wiki_{61u,61s,diag_port,usbkey}.md`
  (source: `~/projects/zeebo/research/sources/tripleoxygen-wiki/`).

## 5. Data findings (10 pairs, `data/spreadsheet.csv`)

- All BR IMEIs share TAC `35580002`; MX unit is `SQAAF…` hardware.
- Serial layout (observed): `[0:5]` plant (`BQAAF`/`SQAAF`) +
  `[5:16]` batch (`0150B215810`, `0150B214810`, `0250B212005`) +
  `[16:]` 7-digit unit sequence.
- Duplicate key `3ulp223EpFKhDT` for IMEIs `…098020`/`…084657` (common IMEI
  prefix 10 chars, common serial prefix 16 chars). Per Moon Sarito this may
  be a spreadsheet error — do NOT build on it.
- Batch hypothesis falsified at available granularity: unit prefix `24`
  maps to 4 different keys, prefix `18` to 2 different keys
  (`python3 tools/stats.py data/spreadsheet.csv --serials`).
- All IMEIs pass Luhn; keys are 14-char `[A-Za-z0-9]`, ~39/62 symbols used,
  no fixed per-position prefix (n=10, descriptive only).
