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

- **STATUS 2026-09-27: the old disassembly does NOT match this firmware.**
  Byte patterns from `thumb_61u_func1.asm` (prologue `b5f0 b083 4606
  2800 d107`, magic compares `9728 ff38 0b38`, etc.) have **0 hits** in
  `1.1.2_APPS.bin`. That slice (`/tmp/thumb_61u_func1.bin`, base
  `~0x1078c8d0`) came from a different firmware version or a carved
  region — its address numbering does not map to this file
  (`0x1078c8d0 - 0x10000000 = fileoff 0x78c8d0` = garbage bytes here).
  Treat it as a *structural reference* (control flow shape) only.
- What the slice suggests (unconfirmed): `IFILEMGR_OpenFile` → `IFILE_Read`
  via vtable → format check → DIAG enable via AUXSETTINGS. Two near-identical
  halves = the two key paths (`/mcp` then `/card0`). No crypto visible.

## 2b. Ghidra project (2026-09-27)

- Install: `~/projects/dkwdrv_hacking/ghidra_install/ghidra_12.1_PUBLIC`
  (Ghidra 12.1, Java 21). Project: `re/ghidra/Zeebo61u` (**673 MB,
  gitignored** — regenerate: import `firmware/1.1.2_APPS.bin` as ELF,
  run auto-analysis; scripts in `re/ghidra_scripts/`).
- Import: ELF loader, `ARM:LE:32:v8`, entry `0x10000000`, 14 program
  headers. Auto-analysis completed (~22 min headless).
- Strings located (Ghidra vaddrs = file offsets via `0x76000→0x1013a000` seg):

  | String | Ghidra vaddr | File offset |
  |--------|--------------|-------------|
  | `fs:/mcp/61u.key` | `0x108d08a4` | `0x80c8a4` |
  | `fs:/card0/61u.key` | `0x108d08b4` | `0x80c8b4` |
  | `/61u.key` | `0x10aff2e4` | `0xa3b2e4` |
  | `lctsys/61s.dat` | `0x10aff29c` / `0x11267a40` | `0xa3b29c` / `0x11a3a40` |
  | `OEM_LCTSystemCtl.c` | `0x10e9fc4a` | `0xddbc4a` |

- **Open problem: no code xrefs.** `getReferencesTo()` on all string
  addresses returns empty, and a raw LE32 hunt for the string vaddrs
  finds **0 hits** in the file — the code never stores absolute pointers
  to these strings. Trailing dwords after the strings (e.g.
  `0x1141e4f8` after `card0/61u.key`) look like struct/table entries:
  access is likely via struct offsets or `movw/movt` pairs, not literals.
- Next: disassemble with capstone over exec segments hunting
  `movw/movt` immediates for the string addresses
  (low16 `0x08a4`/`0x08b4`/`0xf2e4`/`0xf29c`/`0x7a40`, high16
  `0x108d`/`0x10af`/`0x1126`), then decompile hits with
  `DecompileAt`-style postScript.
- **LESSON (2.1 dead end, kept for method): raw pattern hunts failed twice.**
  First the prologue bytes were searched with swapped endianness
  (`b5f0...` instead of file order `f0b5...`); after fixing that, the
  `movw/movt` hunt drowned in dual-mode false positives (ARM decode of
  Thumb code, e.g. `ldr r4,[pc]`+`movs` misread as `movweq r4`). The fix
  was letting Ghidra (which knows instruction boundaries) do the hunt:
  `re/ghidra_scripts/Hunt61u.java` checks every instruction's outgoing
  refs against data windows. **Key trick: refs point at literal-pool
  CELLS (e.g. `0x108d08a0`), not at the strings** — that is why
  `getReferencesTo(string)` was empty.

## 2d. VERDICT — validation cluster decompiled (2026-09-27)

Decompilations: `re/decomp_61u_cluster.c` (7 functions, Ghidra 12.1).

| Function | Role |
|----------|------|
| `FUN_108d06ee` | File open/read helper (IFILEMGR-style vtable calls, 76B stack buffer) |
| `FUN_108d07a0` | Thunk passing key-path cell into BREW dispatcher |
| `FUN_108d08d0` | **Main validation**: alloc checks, event gate `0x97`/`0x10a`, AUXSETTINGS enable via vtable `+0x54`, cleanup |
| `FUN_108d0a96` | Config plumbing (vtable `+0x2c`/`+0x44`), selects event code `0x10a`/`0x97` by flag bits |
| `FUN_108d0c10` | Event-code switch (`0x6d 0x76 0x97 0xa9 0xcf 0xda 0x10a` + `0x10a`-family), vtable `+0x6c`/`+0x70` dispatch |
| `FUN_108d0d44` | Wrapper calling `0c10(..., 0x10a, 0x97, ...)` |
| `FUN_1014e902`/`e744` | Generic BREW dispatcher/forwarder (many callers, not key-specific) |

**2.4 ANSWER: NO key-content comparison exists.** Across all 7 functions:
no `memcmp`/`strcmp`, no byte loop over the 14 chars, no IMEI/serial/NV
read, no length-14 or charset check. Checks performed: null params, alloc
success, file open/read return codes, BREW event code in accepted set.
On pass → AUXSETTINGS enable DIAG (vtable `+0x54`, args `(2, ..., 0x7000, ...)`),
valid until reboot. **The 14-char content is never inspected —
validation is presence+readability-gated, secret is TecToy-side only.**
- Corroboration: 1.1.1's empty `usb.key` works; duplicate keys across IMEIs.
- Cheapest decisive experiment (needs locked console + SD): put 14 random
  alnum chars — even `AAAAAAAAAAAAAA` — in `/61u.key` on SD and boot. If DIAG
  enables, presence-only is proven on hardware.
- **RE stops here. Pivot to Phase 4 (TecToy tool hunt) + data collection.**

## 2e. ARM11↔ARM9: validation is ARM11-only (2026-09-27)

- Cluster callees fully identified: BREW dispatcher (`1014e902`),
  apps-heap alloc/free (`10d6f944`/`11155878`, both via `112f41c0`
  allocator family), memset-like (`107c5c54`), event utils
  (`1014e89c`/`e744`/`e5f2`), ISHELL/IFILE vtable calls. **No
  WMS/ONCRPC/SMD/QMI among them.**
- `oncrpc`/`smd_*`/`modem` strings (e.g. `oncrpcsvc_auth.c` @
  `0x101a8650`, `smd_bridge_mtoa_svc.c` @ `0x1017dc30`) are referenced
  only from modem-client code (e.g. `FUN_101a849a`) — zero refs from the
  `0x108d0xxx` cluster (`RefsTo.java` with caller-range filter).
- `/mcp` + `/card0` are apps-side EFS/SD; AUXSETTINGS is an ARM11 BREW
  applet; DIAG USB mapping is apps-side. The modem is not in the loop.
- Residual: vtable targets resolve at runtime, so this is strong
  static evidence, not a proof. But there is zero positive evidence of
  modem involvement.
- Consequence for Phase 5: binary-SMS delivery (modem→RPC→ARM11) remains
  a valid *delivery* path for a key file, independent of validation.

## 2c. Old slice details (superseded, kept for control-flow shape only)

- Below describes `thumb_61u_func1.asm` in its *own* numbering
  (`~0x1078c8d0`, base `0x10000000`). None of these addresses or bytes
  occur in `1.1.2_APPS.bin` — do not cite them as locations.
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
- Verdict (slice only, unconfirmed on 1.1.2): the function checks key
  **presence + format**, then enables DIAG USB SER1 until reboot. No
  RSA/ECDSA/HMAC verify visible — the key↔console binding (if any) lives
  in the TecToy-side keygen tool (not in firmware).

## 3. Dead end: `re/thumb_61u_validation.asm`

- Disassembly starting at `0x10bff2f5` is **misaligned garbage**
  (`movs r1,r1`, `strh r0,[r0,#32]` …) — that address is mid-instruction,
  not a function entry. The PLAN.md reference to `~0x10bff2f5` as a "second
  ref" should be re-derived from the `61u.key` string xrefs in Ghidra
  (see §2b — currently zero resolved xrefs).

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
