# RE Notes — 61u.key validation

## 1. String references (APPS.bin, `firmware/strings_1.1.2_APPS.txt`)

| String | Line(s) | Meaning |
|--------|---------|---------|
| `fs:/mcp/61u.key` | 94917 | internal NAND key path, checked first |
| `fs:/card0/61u.key` | 94918 | SD card key path, checked second |
| `lctsys/61s.dat` | 124178 | related file read in same function |
| `/61u.key` | 124179 | **CORRECTED 2026-09-29**: not a validation/suffix match — it is the LCT **write** target of the `+LCTUSBLOCK` AT command (§28) |
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
  | `/61u.key` | `0x10aff2e4` | `0xa3b2e4` | (§28: consumed via `adr` by `+LCTUSBLOCK`, unlike the validation cluster) |
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

### 2d-i. CORRECTION 2026-09-27 — content IS compared (SebaG20xx, GBAtemp)

External RE (SebaG20xx, GBAtemp post #9) found the function we missed:
Ghidra never created functions in `0x108d07b0–0x108d08d0`, and we never
looked there. Forced-Thumb disassembly (`DumpThumb.java`) confirms
byte-for-byte (`re/gap_108d07c0_thumb.txt` if saved):

```
108d081c  push {r4,lr}              ; check_61u_key
108d081e  adr r0,[mcp_path]         ; "fs:/mcp/61u.key"
108d0820  bl resolve_test
108d0826  beq card0_check           ; mcp resolves -> continue
          ; FAIL-OPEN: mcp missing:
108d0828  movs r1,#6 / movs r0,#0 / blx result_setter  ; SUCCESS(0,6,ptr)
108d0834  adr r0,[card0_path] / bl resolve ; card0 must resolve (bne fail)
108d083e  adr r0,[mcp]  / bl FUN_108d06ee  ; read mcp  -> [r4+4]
108d0848  adr r0,[card0]/ bl FUN_108d06ee  ; read card0 -> [r4+8]
108d0850  null-check both
108d085a  mov r1,r0(card0) / mov r0,r2(mcp)
108d085e  blx strcmp                ; CONTENT COMPARED mcp vs card0
108d0862  cmp / bne fail
108d0866  movs r1,#6 / blx result_setter  ; MATCH -> SUCCESS(0,6,ptr)
108d0870  movs r1,#0 / blx result_setter  ; all other failures
```

Consequences (our old "no content check" verdict was WRONG):
- Validation = SD content must STRCMP-equal internal content. Our
  `61u.key.bad` (`AAAAAAAAAAAAAA`) will FAIL (≠ internal key) — test
  still worth running as confirmation, expectation flipped.
- **Fail-open explains the Hospital**: missing internal key → SUCCESS
  path → removing `mcp/61u.key` = permanent DIAG. Mystery solved.
  **CONFIRMED at instruction level (§30e)**: an unresolvable `mcp/61u.key`
  makes the resolve helper return `0x0d`, and `check_61u_key` reports code
  **6** — the same code the strcmp-equal path reports. Only "opened but NULL"
  and "strcmp mismatch" report code 0. (§30e also records a false start here
  and what the full chain is.)
- Keygen algorithm STILL TecToy-side (compare is mcp-vs-card0, never vs
  recomputed value; provisioning code absent from firmware). Unchanged.
- Timing side-channel is REAL (strcmp bails at first mismatch byte;
  SD content fully attacker-controlled) but impractical (ns diffs inside
  full boot; needs electrical probing at the compare). Documented,
  not pursued.
- Minor discrepancies vs our decomp: Seba reports heap fileSize+1 reads;
  our `06ee` decomp shows 76B stack + small mallocs — decompiler
  imprecision or a second read path; structure (not allocs) is what
  matters and it matches.
- **Stress-test 2026-09-27 (ours): resolve = `OEMFS_Test(%s)`** (log
  string at `0x10af1648`; literals are OEMFS structs). Polarity
  CONFIRMED: Test→0 continues to card0; nonzero (unresolvable, `0x0d`)
  → early `report(0,6)` = **fail-open**, same code as a strcmp match. Call chain verified to import-stub level
  (`bl`→ARM veneer `109834c8`→wrapper `11155860`→PLT-like `11133a60`).
  `result_setter@1079e4a0` = import thunk (PLT slot → `0x103693e8`;
  semantics still structural: match → `(0,6,ptr)`, other fails →
  `(0,0,ptr)`; **what the receiver does with 0 vs 6 is what settles
  fail-open, and that is still undecoded**).

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

## 5. Data findings (10 pairs + 3 unpaired keys + 2 unpaired IMEIs)

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

## 6. Z-Wheel dead end (2026-09-27)

- `z-wheel-tt_game_info.db` / `z-wheel-asset_cache.db` (`~/.config/zeebx/cache/`):
  pure game catalog (`GAMEINFO(game_id, class_id, playcount, ...)`, 59 rows;
  `ASSETS(owner, dslid, type, version, path, ...)`, 114 rows). No keys,
  no unlock data.
- `tectoy.mod` (Z-Wheel binary, `mod/274755`, 2011): reads IMEI via
  `Util_GetConsoleIMEI(D)` and sends it as HTTP header `X-ZEEBO-IMEI:`
  (server-side account/DRM). **Zero `61u`/unlock/DIAG/AUXSETTINGS refs.**
  Z-Wheel never touches the key path — dead end for keygen, but confirms
  IMEI is readable from any BREW app (does not help: validation never
  reads it either).
- Modem EFS2 partition (5.5MB, 95 names via `nand.py nomes`): numeric NV
  items + `nvm`, **no `.db`, no `61u`/`61s`, no `lctsys`**. Nothing
  key-related on the modem side either — consistent with §2e (ARM11-only).
- Remaining SQLite on dumps (`tt_prefs.db` 401 gens, `tt_dlqueue.db` 400
  gens, both EFS2APPS): Z-Wheel prefs/queue family, same journal-replay
  blocker as `61s.dat`, low expected value. Not pursued.
- Live `tt_prefs.db` from zeebx emulation (`~/.config/zeebx/.../mod/274755/`):
  `PREFSINFO(name, strValue, dwValue, flags)` with UI prefs/alarms/points,
  no key material. Bonus artifact: `CreditServerURL =
  https://aquila.tectoy.com.br:8443/WSM/wsm?wsdl` (dead TecToy server).

## 7. Algorithm review — what we missed (2026-09-27)

Exhausted so far with NULL results: pairwise shared substrings ≥3 (none),
key-as-base62 vs IMEI numeric relation (random-looking mods), HMAC/SHA1
with 16 secrets, short salts, CRC32-substring probe, serial/IMEI prefix
grouping (falsified), Luhn (all pass, uninformative).

**The anomaly we overlooked: the key alphabet is NOT uniform.**
n=13 keys (182 chars): 40/62 symbols used vs 58.8 expected under uniform;
χ²=185 (df=61, 0.1% critical ≈100). Class split U/L/D = 101/47/34 vs
76.3/76.3/29.4 expected (χ²=20, df=2, 5% critical 6.0). Uppercase-heavy,
lowercase-starved. Missing: `57RSUXcdegijkmnoqrstvw`.
- NOT transcription bias: raw console files alone (n=3, 42 chars) show
  U/L/D = 26/10/6 (62% upper) — same direction, stronger.
- Positional (n=13): pos7 = 10U/0L/3D, pos12 = 11U/0L/2D (zero lowercase);
  P ≈ 0.001 each under uniform. pos1/pos6 lean lowercase. No fixed
  segments, no shared substrings — so NOT a structured multi-part format,
  just a biased draw.
- Rules out: uniform CSPRNG mod 62, uniform base64-filter, hex-digest
  remap (would lack G–Z/lowercase mix we DO see). Compatible with: custom
  PRNG with a biased/duplicate-heavy pool string, range-limited RNG +
  alnum filter (no exact range fits yet — digits present rules out pure
  A–y ranges), or factory tool quirk. Cause unknown.
- Does NOT advance IMEI→key derivation (no IMEI correlation found), but
  it is the first positive structural fact about the generator: any
  proposed algorithm must reproduce the uppercase bias. Confirm with more
  raw keys; the TecToy tool (Phase 4) would settle it instantly.

### 7b. Byte-domain analysis (2026-09-27, answers: timestamp? hash? strcmp?)

- Every key (13/13) decodes as base64 (`key+'=='`) to **exactly 10 bytes**.
  So a key = 80-bit value in a 14-char text encoding (padding stripped).
  Necessary-not-sufficient (any 14 alnum chars decode so), but it frames
  analysis in the byte domain.
- **Timestamp DEAD**: base62(key) as unix time (full/low32/high splits) →
  scattered dates 1976–2103, nothing in production years 2009–2011.
- **Byte stats = uniform random**: 65/130 high-bit bytes (50%), 0 zero
  bytes (n.s.), 101 distinct values ≈ 102 expected for 130 uniform draws.
  No CRC16 (CCITT-F/XMODEM) of first8 == last2. First bytes show no BCD
  IMEI structure. → **the 80-bit VALUE is uniform; the uppercase bias
  lives entirely in the ENCODING step** (bytes→chars).
- Encoding constraints collected: no `+/` ever (p≈0.003 if standard
  base64 → ruled out); first-char spread covers A–y (rules out base62 of
  the 80-bit integer, which forces first char ∈ A–F); per-chunk
  (base64-like, 6 bits/char) with a biased 64-entry table fits all
  observations, exact table unknown.
- Net: value = factory RNG 80 bits (+ DB, theory (b) strengthened);
  encoder = custom biased table. Neither is recoverable from firmware.
- **strcmp/file-lock in cluster: NONE.** Zero strcmp/strcpy/strlen/memcmp
  in all 7 decompiled functions. File ops are READS only
  (`FUN_108d06ee`: IFILEMGR-style open + 76B-stack-buffer read);
  **nothing in firmware WRITES `61u.key`** (factory-provisioned).
  ⛔ **REFUTED 2026-09-29 (§28): `+LCTUSBLOCK` writes `/61u.key` via the
  FS/RPC client at `0x10aff100`.** "Factory-provisioned" still holds for
  the *keygen* (no generator in the image) but not for the *write*.
  The only "lock/unlock" is the DIAG USB SER1 mapping via AUXSETTINGS
  (+0x54); no latch, no state file. Residual (thin): the read buffer is
  passed opaquely INTO the AUXSETTINGS call — AUXSETTINGS itself was not
  decompiled, so a content check there cannot be excluded statically;
  against it: 1.1.1 empty-`usb.key` precedent + no string ops anywhere
  in the cluster. Hardware garbage-key test settles it.
- User gut SUPERSEDED 2026-09-27: filename+location is NOT the whole
  trigger — SD content must strcmp-equal the internal key (§2d-i).
  Presence-only is DEAD; garbage-key test now predicts DIAG OFF.

## 8. zloader bypass analysis (2026-09-27)

## 9. DIAG race + unauthenticated-command fuzzing (2026-09-27)

Source: r/SBCGaming thread (UmaBatataFrita, ~2024):
`reddit.com/r/SBCGaming/comments/1c9y3po/...`
- RevSkills without key: crashes (expected — port not mapped).
- **DFS Port Manager occasionally "enters" the Zeebo at boot** (rare,
  timing-dependent) but yields no file access. Assessment: USB-level
  enumeration race (port visible before/while validation gates it), NOT
  authorization — the DIAG protocol layer still refuses. Still interesting:
  indicates a boot window where the port exists but the gate hasn't
  decided. A serial sniffer comparing failed vs "entered" sessions
  (commenter's suggestion) could reveal whether any command is honored
  pre-gate.
- Old Qualcomm drivers work (YUGA/Qualcomm naming irrelevant).
- Confirms independently: 1.1 + empty `usb.key` works, 1.2 doesn't,
  JTAG extracts or deletes the key.
- **New hardware-test avenue (no key needed, needs locked console + USB):**
  fuzz unauthenticated DIAG commands (VER, password/SPC-family with
  defaults like `000000`, EFS dir list) via QPST/QXDM or raw DIAG frames,
  especially inside the boot race window. CDMA-phones heritage (BitPim,
  LG VX9200 tools in `firmware-dumps/`) gives the command vocabulary.
  If any privileged command answers pre-gate or with default password,
  DIAG opens without keygen AND without JTAG.
- Modem evidence (AMSS strings): `SPCAuthKey`/`sPCAuthKey` NV items and
  "Password length mismatch between DIAG and CM" — SPC/password auth
  EXISTS in the modem DIAG; defaults untested. Also
  `gsdidiag_verify_pin` (SIM PIN via DIAG) present.
- Tool: `tools/diag_fuzz.py` (UNTESTED live): QCDM framing (CRC verified
  `0x29B1`, escape roundtrip self-tested), probes VERNO/ESN/0x3A +
  SPC/PASSWORD defaults (`000000 123456 654321 111111 123123`),
  `--dry-run` printable now, live mode needs pyserial + locked console.
  Response classes: valid vs `0x13` BAD-CMD vs TIMEOUT; anything else = lead.
- Fuzz-target shortlist (2026-09-27, verified 2026-09-27):
  `AT$QCDMG` on Modem interface (real Qualcomm cmd, DM-mode switch —
  generic, unconfirmed on Zeebo); DIAG SPC/password with `000000`/`123456`;
  `DIAG_VER_F`, EFS `opendir`/`readdir` pre-gate; download-mode `0x3A`
  (already known-good post-gate per KNOWLEDGE.md — try pre-gate).
- Tool inventory (verified): Zeebo-specific = RevSkills, Zeebx Emu,
  Open Zeebo Project (JTAG extraction). Generic Qualcomm/BREW ecosystem
  (usable vocabulary, not Zeebo tools): QPST/QXDM, `AT$QCDMG`,
  Brew-OS-Parser (forensics on BREW phone dumps), Brew Bot (API QA),
  Melange (Android BREW emu, no Zeebo GL support). Unrelated:
  `qualcomm_gbl_exploit_poc` (modern ABL/UEFI, not MSM7201A).

- zloader (`~/projects/zloader-build`, OpenZeebo 2012) = custom bootloader +
  NAND block patcher (`main.c`: find 16-byte pattern in flash → verify block
  SHA1 → `memcpy` patch → rewrite block; user confirms via power button/LED).
- Patch content (`zloader/patch/*.c`, per version incl. 1.1.2): 16-byte
  **code-signature-check bypasses** (conditional → unconditional branch,
  e.g. `\xc0\x46\x0e\xaa…` → `\x00\x25\x7d\xe0…`). No `61u`/DIAG/AUXSETTINGS
  refs anywhere in the tree (only unrelated `smem.h` DIAG-err defines).
- Conclusion: zloader neuters CODE SIGNING (run unsigned homebrew), it does
  NOT touch 61u.key validation. The Hospital's "DIAG always on" comes from
  elsewhere (patched APPS or key removal side-effect), not zloader. zloader
  is therefore **irrelevant to keygen** — closed as an avenue.

## 10. zeesms — Guilherme's SMS app (2026-09-27)

Source: `~/Downloads/Telegram Desktop/zeesms.zip` (287KB, src + status.md,
2026-09-26). Working BREW SMS send/receive (ISMS, `AEESMS_TYPE_TEXT`).
- Receives via `ISHELL_RegisterNotify(... AEECLSID_SMSNOTIFIER ...)` →
  `EVT_NOTIFY` → `ISMS_ReceiveMsg()`; handles `_SZ`/`_WSZ`/**`_BINARY`**
  payloads (`MSGOPT_PAYLOAD_BINARY` → raw bytes). **Binary-SMS receive
  at BREW level is proven working.**
- Writes files via IFILEMGR (`inbox.dat`, `smsdiag.txt`, app-relative;
  MIF privs `PLFile|PLNetwork|PLTapi`).
- **Phase 5 refined into two paths:**
  - (a) BREW-app receiver: binary SMS → app → `IFILEMGR_OpenFile(...,
    _OFM_CREATE)` the key file → reboot → DIAG. Needs the receiver
    INSTALLED → needs unlock/signing → useless against locked consoles
    (post-exploitation persistence at best).
  - (b) Modem-autonomous: special SMS (WAP-push, OTA, FOTA?) acted on by
    ARM9/AMSS itself, no app involved. Only path that works on LOCKED
    consoles. Requires AMSS WMS RE (`wms_msg_do_write` — what/where does
    it write? `wms_cfg_check_wap_push_message` behavior?). AMSS.bin
    imported + analyzed in `re/ghidra/` (same project); WMS targets
    (`wms_msg_do_write`, `wms_cfg_check_wap_push_message`, `SPCAuthKey`)
    strings located, xrefs pending.
- ONCRPC bridge (from zeebo-lle `data_services_net_rpc.md`, VERIFIED):
  WMS = `wms_svc.c`/`wms_clnt.c`, callback `0x31000003` (AMSS) / calls
  `0x30000003` (APPS) over SMD `RPCCALL`/`RPCRPY` channels. So APPS↔modem
  SMS transport exists both directions; incoming-SMS fan-out on a LOCKED
  console (which clients are registered besides stock apps?) is the open
  question for path (b). AMSS "unable to register" ONCRPC sites resolve
  in Ghidra (e.g. `FUN_16e4232e`); WMS log-string refs mostly absent
  (dead strings or computed refs) — deeper modem-task RE deferred until
  hardware exists to test against.

## 11. SDK cross-reference (2026-09-27)

SDK: `zeebo-emulator/testkit/shadow_inc/` (BREW 4.0.2) + `research/docs/sdk-extract/`.
- `DAT_108d089c` = `0x01001003` = **`AEECLSID_FILEMGR`** (`AEEClassIDs.h:64`).
  `FUN_108d06ee` creates the FileMgr instance — file-open helper confirmed
  by symbol, not just shape.
- ISHELL vtable mapped from `AEEIShell.h` (CreateInstance `+0x0C`,
  GetHandler `+0x84`, …). Cluster's `*(param_1+0x30)` calls at `+0x2c /
  +0x44 / +0x54 / +0x6c / +0x70 / +0x80` do NOT match ISHELL arg patterns —
  that object is a custom (LCT?) interface, identity open. REX/OKL4 sources
  (`zeebo-lle` notes reference) not yet mined for modem-task patterns —
  left for the AMSS round with hardware.

## 12. REX/OKL4 mining + non-ISHELL calls verdict (2026-09-27)

## 13. EMAPPLET + microkernel dumps (2026-09-27)

- Microkernel source (2nd copy, outside zeebo-lle):
  `~/projects/zeebo_weird_os/build/okl4-zeebo/okl4-2.1.1-fix7/`
  (6.8MB: `arch/ iguana/ pistachio/`; no REX inside — REX lives in
  zeebo-lle `refs/`). Same version as zeebo-lle notes. Infra, not target.
- **EMAPPLET confirmed in firmware** (`..\..\apps\EMApplet\EMApplet.c`,
  27 hits in APPS strings): `EMApplet_Memcpy` (incl.
  `CopyBrewAppletsIntoModEnand`), `EMApplet_Format Enand`,
  `EMApplet_CheckEnandFile/Test_SDCard`, LED/TV-out forms. Engineering
  applet reachable by button combo (ZL+Cima+3+Home per community; same
  combo shows IMEI per Moon Sarito) — NO key needed to OPEN it.
- **New hardware-test lead**: if `EMApplet_Memcpy` (SD→NAND,
  "Memory Copy installs unsigned apps" per briefing) skips signature
  verification, locked consoles accept unsigned content with NO key and
  NO DIAG. Test (Layo/OLX console): SD with `/mif`+`/mod/app` layout →
   EMAPPLET → Memory Copy → reboot → check. Caveat: briefing nests it
   under Field Test (DIAG-gated) — verify whether reachable directly.
- **Decompiled (2026-09-27): NO signature gate in the copy flow.**
  `FUN_10359fec` = pure byte-copy (open src mode 1 / dst mode 2-or-4,
  0x1e00-chunk read `+0xc` → write `+0x14`, byte-count verify, cleanup).
  Caller `FUN_1035a14a` = path builders + dir Test/MkDir (`+0x1c`/`+0x10`)
  → calls `59fec`. No crypto, no `.sig` handling in the flow. If the
  UI/form layer adds no check upstream, Memory Copy installs arbitrary
  SD content to NAND on a locked console — highest-value hardware test
  after the garbage-key test.
- LCT source: NONE on disk (openzeebo-repo has only zloader + python
  tools). Decompilation is the only source-level view; scripts:
  `WinHunt.java`, `RefsTo.java`, `DecompileAt/Raw.java` (all tracked in
  `re/ghidra_scripts/`).
- **Deep-dive (2026-09-27): literals resolved, no sig anywhere.**
  `DAT_1035a304` = `0x01001003` (FILEMGR again); `...308` = `0x1e01`
  (copy buffer size); `...30c/31c` = small event codes; `...310` = `'/'`
  (path builder); `...314/318` = log-string pointers. Callers of
  `1035a14a`/`59fec`: NONE (event-driven, like the key cluster).
  All 7 `.sig` occurrences in the binary resolve to UNRELATED functions
  (`1086893c`, `1098f380`, `10d4e9a4`) — zero in EMApplet code
  (`0x10359xxx–0x1035bxxx`). The copy engine AND its caller never touch
  signatures; a `.sig` gate could only hide in the event-driven form
  layer, untraceable statically without the event table. Hardware test
  stands as the decider.
- Briefing context (unverifiable locally, harmless): LCT=Longcheer ODM,
  internal names W800/Genie; JTAG = 10 pads, 2.6V dongle.

- REX RTOS surface fully known (`zeebo-lle/docs/rex-abstraction-layer.md`,
  from QSC1110 AMSS leak `refs/rex_qsc1110.h`): tasks (`rex_def_task`),
  signals bitmask (`rex_wait/set/clr_sigs`), timers, `oncrpc_rex.c` bridge.
  OKL4 2.1.1 source + ARM build in `refs/`. Relevance to keygen: NONE —
  validation lives at BREW level, above REX. Useful only for the deferred
  AMSS modem-task round (WMS dispatch runs as REX tasks).
- Non-ISHELL calls: `AUXSETTINGS`/`LCTUtility` absent from SDK headers AND
  `ZeeboDeveloperGuide0.97.md` — internal Longcheer OEM interface,
  unnameable from public sources. Slots stay structural
  (`+0x54` = DIAG-enable entry by behavior). Naming needs OEM source or
  runtime tracing on a live console (JTAG/DIAG) — parked.

## 14. SMS-hack proposal verdict (2026-09-27)

- Incoming SMS lands in modem NV store (`/sms/nv_gw_msg_data`,
  `/sms/nv_gw_msg_header` — modem EFS, NOT apps EFS) + client notify.
  No FOTA/OMA-DM/OTA-provisioning strings anywhere in AMSS.
- WAP push is detected and ROUTED (`WAP Push Message Detected! Routes
  Changed`, `wms_cfg_check_wap_push_message`) — to a push client
  (browser), never to a file write. No handler writes apps-EFS paths.
- **Verdict: modem-autonomous SMS→key-file has NO identified mechanism.**
  On locked consoles nothing converts an incoming SMS into
  `fs:/mcp|card0/61u.key`. Remaining theoretical: parser mem-corruption
  in SMS/WAP-push parsing (other phones had such CVEs) — needs deep RE +
  fuzzing + hardware + luck;   parked, not pursued.
- Standing remote/physical vectors (in value order): garbage-key SD test
  (FAIL predicts strcmp-confirm), EMAPPLET Memory Copy (unsigned install?),
  DIAG fuzz pre-gate, JTAG (certain, invasive).

## 15. Sibling baseband: HTC Dream radio (MSM7201A, 2026-09-27)

- Downloaded `ota-radio-2_22_19_26I.zip` (9.1MB) from archive.org
  (`HTC_Dream_Archive`; Dream = MSM7201A, same chip). `radio.img` 21MB
  raw + ELF@0x280080, AMSS strings present. Archived at
  `.../zeebo/firmware-dumps/ota-radio-2_22_19_26I.zip`.
- Same Qualcomm code family: `SPCAuthKey` + "Password length mismatch
  between DIAG and CM" verbatim as in Zeebo AMSS. No new SPC defaults
  visible in strings. NOT imported to Ghidra (same-family dup of our
  AMSS; burn the analysis time only if fuzzing stalls for vocabulary).
  Also available in same archive: `Radio_Dream_RC33`, `Radio_Sapphire`
  (HTC Magic = MSM7201A too).
- All three pulled + strings-compared (2026-09-27):
  `Radio_Sapphire_2_22_19_23.zip` + `Radio_Dream_RC33_1_22_14_11.zip`
  archived in `firmware-dumps/`. All share SPC machinery verbatim
  ("SPC CODE: Verified and valid" / "Not Verified", SPCAuthKey,
  password-mismatch). DIAG string diff Dream-vs-Zeebo = peripherals only
  (GPS diag, dancing-ports, QDSP) — no new unlock-relevant commands.
  No Ghidra import: same-family dup confirmed, diminishing returns.

## 16. Attack surface map (2026-09-27, post-correction)

Model: `check@081c` = resolve mcp → resolve card0 → read both (heap
fileSize+1, memset, bounded read — **no overflow**, verified in `06ee`
decomp; TOCTOU not exploitable, boot-time single-thread) →
`strcmp(mcp,card0)` → RDevMap RPC (`rdevmap_clnt.c`) → port map. ⚠ the
  "SUCCESS(0,6)" reading is **retired as a local code** (§32c/§33a): nothing
  branches on r1 here — it is RDevMap RPC argument 2.
  Fail-open iff mcp unresolvable — CONFIRMED: resolve failure yields report
  code 6, identical to a strcmp match (§30e).

| # | Vector | Needs | Status |
|---|--------|-------|--------|
| A1 | Correct key on SD | keygen/DB | BLOCKED (secret TecToy-side) |
| A2 | Garbage key (`61u.key.bad`) | locked console+SD | Predict FAIL; run as strcmp confirmation |
| A3 | Timing oracle via SD bytes | ns-precision boot timing | REAL but impractical; parked |
| A4 | Oversize/malformed key file | SD only | DEAD (bounded heap reads, verified) |
| A5 | EMAPPLET Memory Copy unsigned install | button access, Field-Test gating TBD | OPEN, high value |
| A6 | EMAPPLET overwrite `mcp/61u.key` + matching SD | dst-path control (form-built paths; shared builders `1079bff4/101d7f48`, form layer untraceable) | UNKNOWN, needs hardware |
| B1 | Delete/corrupt mcp key (fail-open) | EFS write (DIAG/JTAG/A6) | PROVEN structurally; needs a writer |
| C1 | DIAG fuzz pre-gate (race) | USB + locked console | OPEN (`diag_fuzz.py` ready) |
| C2 | SPC/password defaults | USB + locked console | OPEN (SPC machinery confirmed in AMSS) |
| D1 | zloader sig bypass | flash write (download/JTAG) | Works, but ≠ DIAG unlock |
| D2 | EDL 9008 (Seba #7) | USB cable + edl client | OPEN, cheap probe: if secure boot unfused → read/write NAND → patch strcmp directly (no keygen needed). Highest payoff-per-cost after A2 |
| D3 | Secure-boot fuse state | EDL probe or boot RE | UNKNOWN; qcsbl_auth entry located (§17) |
| E1 | TecToy tool/DB leak | luck/contacts | OPEN, highest payoff |
| E2 | More pairs (Layo/group) | people | OPEN |
| E3 | Duplicate `3ulp223` resolution | 03labs/Moon | OPEN (error vs reuse changes nothing structurally now) |
| F1 | SMS remote injection | — | CLOSED (§14: no modem-autonomous path) |
| G1 | JNE-crack (`bne@0864`→NOP, 2 bytes, file `0x80c864`) | NAND write to APPS code (download/JTAG/EDL); brick risk if APPS sig-verified | OPEN, exact bytes in §18 |
| G2 | Text Script auto-copy (`.dat` trigger) | SD + locked console; DIAG-gating TBD per wiki | OPEN, recipe in §19 |
| G3 | 1.1.x downgrade (empty `usb.key`) | 1.1.1 image + flash path (neither on disk) | PARKED |
| G4 | UART console (gpio45/46) | physical probing | OPEN for info/boot logs |

## 17. Boot chain: APPSBL/QCSBL/OEMSBL + auth entry (2026-09-27)

## 18. JNE-crack patch (2026-09-27, classic conditional-flip)

- Veneer `0x109834c8` is the SHARED libc strcmp (20+ callers) — do NOT
  patch it. Patch OUR call site only:
- **P1 (recommended, 2 bytes)**: `0x108d0864` (`bne →fail`) → NOP.
  File offset `0x80c864`: `04 d1` → `00 bf`. Effect: strcmp result
  ignored. ⚠ the "SUCCESS(0,6)" reading is **retired** (§32c) — the callee
  (`rdevmap_clnt.c`) does not *branch* on r1; it ships it as RDevMap RPC
  argument 2. 0 and 6 are different calls, just not a local pass/fail.
- P2 (1 byte, **assumption now dead — see §32c**): `0x108d0870` `movs r1,#0`
  → `movs r1,#6`. File `0x80c870`: byte `0x00`→`0x06`.
- P0 (4 bytes, equiv. to P1): `0x108d085e` BL-strcmp → `movs r0,#0; nop`
  (`b2 f0 34 ee` → `00 20 00 bf`). File `0x80c85e`.
- Single patch point suffices (one strcmp for both paths; gate at 08d0
  is event-only).
- **Delivery is the whole problem** (patch is trivial): needs NAND write
  to APPS code region — download mode / JTAG / EDL-unfused / EMAPPLET
  (only if it reaches raw APPS blocks, unlikely: app-level copy).
  Brick risk: if OEMSBL verifies APPS signature post-patch the console
  won't boot — zloader precedent (survives its own patches) suggests
  feasible, NOT proven for this spot. Test order on hardware: garbage-key
  (safe) → EDL probe → patch (last, JTAG recovery nearby).

- Partitions extracted (`nand.py`): APPSBL/QCSBL/OEMSBL1/OEMSBL2.
  APPSBL+QCSBL imported+analyzed in `re/ghidra/` (binary ARM LE base 0).
- APPSBL (384KB): secboot QCSBL flash-loader (`qcsbl_flash.c` debug paths,
  `0:APPS` labels); 97 strings, NO crypto/fuse strings — loader, not checker.
- QCSBL (256KB): **`qcsbl_auth.c` found**; `FUN_0000a41c` = auth entry
  (calls `FUN_0000d368` → `FUN_0000d220` verify, returns 0/1/2).
  Verify primitive + fuse gating NOT yet traced — that is a full
  secure-boot RE project of its own.
- OEMSBL1/2: "Skipped sbi verify since no callback provided" — verify
  skippable when callback NULL (worth remembering for EDL work).
- Scope verdict: boot-chain RE answers Seba #7's fuse question but does
  NOT advance keygen (validation is BREW-level, above secure boot —
  patching it never touches the boot chain). Parked; Ghidra programs kept
  for the EDL/fuse round if hardware arrives.

## 19. Text Script / factory auto-copy mechanism (2026-09-27)

Community claim (Moon Sarito + GBAtemp dev): a Notepad text script on SD
installs mifs+mods on ANY Zeebo, no key. Firmware says the skeleton is REAL:
- Trigger: `fs:/card0/longcheerzeebo/autocopysdcardinfotoenand.dat`
  (single occurrence, file `0xa1f09` → vaddr `0x10165efa`).
- Same struct: `/mif`, `/mod` dir names + data dwords + `LCT_DebugMemo` tag.
- Logs: `fs:/mcp/lctsys/sdautocopy.log` (+`_back.log`).
- Nearby: `FUN_10165dea` (log/notify helper, no callers — event-driven,
  like everything in this binary). Reader function unlocated (no code
  refs to the struct; the `0x10165630/58` dwords decode as data, not code).
- The dev's "add mifs and mods to the script" maps 1:1 onto this struct:
  the `.dat` is almost certainly a manifest (file list) the console
  consumes at boot to copy SD→NAND. Format unknown.
- Gating unknown (key/DIAG-gated? boot-phase unconditional?). NOT yet
  resolved statically.
- **Hardware recipe (cheap, decisive, needs locked console + SD):**
  SD with `/longcheerzeebo/autocopysdcardinfotoenand.dat` (try: empty;
  then with `mif/<name>.mif` lines) + `/mif` + `/mod/<app>/` content
  (e.g. zeetris) → boot → observe installs / `sdautocopy.log` traces.
  If anything installs without DIAG, this beats every other vector.
- **RESOLVED 2026-09-27 (wiki `carregando_seu_codigo`): the `.dat` is a
  TRIGGER, not a manifest (empty file works). Flow: SD with
  `/mif/<app>.mif` + `/mod/<app>/{.mod,.sig,.bar}` → Appmgr → EMAPPLET →
  Field Test (needs DIAG mapped, or OpenOCD `field` cmd) → Memory Copy
  (LEDs blink) → reboot → Unlock to RUN. Auto-copy fires seconds after
  insertion IFF DIAG is active. `.sig` files are required present and
  COPIED, but our decomp shows no verification at copy time → enforcement
  is at RUN time (the code-sig check zloader patches). Coherent full model:
  install-time = no check, run-time = sig check, DIAG = gate for both
  Field Test and auto-copy. **Text Script is therefore NOT a DIAG bypass:
  it chains BEHIND the key.** Universal part = same `.dat` works on any
  console once DIAG is on (dev consoles always are).

## 20. Binary-exploitation audit (2026-09-27)

- `check_61u_key` reads: heap `fileSize+1` + memset + bounded read.
  No overflow, no TOCTOU (single-threaded boot). DEAD.
- `strcmp` shared-libc veneer chain: no bug class here. DEAD.
- `FUN_101d7f48` = **unbounded strcat** (find-NUL + copy). Used in
  EMAPPLET path building (`auStack_148`, 128B stack) appending `'/'` +
  basename (capped <0x80 by `FUN_10359810`'s `4<len<0x80` gate).
  Overflow iff prefix+1+basename > 128 — arithmetically reachable
  (e.g. 14-char prefix + 127-char name = 141), BUT basename input
  (`local_38`, malloc 0x80) provenance unresolved in decomp (no visible
  writer; possibly dropped by decompiler) and the name source (form
  selection vs SD dir listing) unknown. CANDIDATE, unconfirmed —
  needs   live debugging or form-layer RE. If SD filenames flow in,
  malicious SD = stack smash at copy time (pre-DIAG? gate TBD).
- `FUN_1079bff4`/`101d7f48` shared builders: shape unknown, not audited.
- Verdict: no confirmed memory-safety bug; one overflow CANDIDATE in
  EMAPPLET path building with two open facts (input source, exact
  layout). This is the only binary-exploitation lead in the project.
- **Deeper 2026-09-27: `1079bff4` = word-at-a-time strcpy** (uqsub8
  NUL trick), unbounded, used 5× binary-wide. In `1035a14a`:
  `strcpy(auStack_148[128], param_2)` — overflow iff
  `strlen(param_2) ≥ 128`, no basename needed. Frame: `sub sp,#0x12c`.
  `param_2` arrives from the event-driven form layer (no callers).
  Plausible attacker control: 200+ char SD directory/filenames (FAT LFN)
  IF the form copies SD-derived names into this path. Unproven statically.
- **PROVEN 2026-09-27 (`tools/prove_overflow.py`, Unicorn Thumb, real
  firmware bytes): `strcat@101d7f48` + `strcpy@1079bff4` with 200B input
  smash a canary past a 128B stack buffer (+86/+72 bytes over); 8B input
  leaves it intact. MECHANISM confirmed executable — only the TRIGGER
  (long name reaching `param_2`) stays open. (ASU/AxéSec pwn-track
  primitives — stack smash → PC — apply verbatim here: no SSP/ASLR/NX.)
- Other techniques swept: format-string (log fmts are static DATs —
  safe shape), integer overflow in sizes (needs 4GB file — no), heap
  read bounds (size+1 — safe), vtable confusion (no evidence).
- Honest bottom line: ONE unconfirmed stack-smash shape whose trigger
  needs hardware to test (long filenames on SD → watch for crash via
  LEDs/behavior; needs Field Test/DIAG or auto-copy gating first).
  Even on crash, weaponization needs JTAG debugging. Rank: below EDL,
  above timing-oracle.
- **Exploitability landscape 2026-09-27 (no SSP, no ASLR, no NX):**
  zero `stack_chk` strings; no `PT_GNU_STACK`; fixed ELF load addrs
  (= runtime addrs, confirmed by Ghidra mapping); era-typical RWX.
  Epilogues are `pop {...,pc}` → smashed saved-LR = direct PC control.
  Boot-time code ⇒ deterministic stack addresses every boot (no ASLR
  to defeat, no info-leak needed). **ROP unnecessary; ARM/Thumb
  confusion (BX bit0) is a spare tool, not a requirement — plain
  stack shellcode suffices IF the trigger is real.** The ONLY missing
  link remains triggerability (long filename → `param_2`).
- **Trigger decomposed 2026-09-27 (4 hops, status each):**
  H1 attacker plants 200+ char LFN name on SD — TRIVIAL, full control.
  H2 console reads the name into a buffer — EXPECTED (hotplug scan,
  auto-copy listing, or form listing all enumerate SD dirs; exact
  function unlocated, event-driven binary).
  H3 name flows into `FUN_10359880`/`1035a14a` path building — PLAUSIBLE:
  `10359880` does `strcpy(auStack_10c[128], path+10)` (strips `fs:/card0/`
  prefix, NO length check; callers: none found = event-driven) then two
  strcats into `local_8c[128]`; `1035a14a` does `strcpy(auStack_148[128],
  param_2)` + strcat basename. Every hop unbounded; every buffer 128B.
  H4 smashed saved-LR → PC — PROVEN executable (Unicorn).
  Single experiment closes H2+H3 together: SD with 200-char names in
  `/mif`+`/mod`+root → boot/insert → watch for crash (LED freeze, reboot
  loop, silence where logs were). No crash after auto-copy attempt =
  names never reach the builders (gated/sanitized) → candidate dead.
  Non-hardware path to confirm: zeebo-lle LLE boots real firmware —
  in principle reachable with a crafted SD image + crash observability;
  proposal for emulator folks, not executable here.
- RAM model: ARM11 apps memory local to the target (BREW stack);
  ARM9/modem separate, SMD shared region irrelevant here. No
  cross-core aspect to this bug class.

## 21. 50-technique sweep (2026-09-27)

Memory corruption: (1) stack overflow classic — CANDIDATE (strcpy shape §20);
(2) strcat variant — same candidate; (3) heap overflow — DEAD (bounded);
(4) heap metadata/unlink — PARKED (needs heap bug; allocator = `112f41c0`
family, unstudied); (5) UAF — PARKED (none found); (6) double-free — PARKED;
(7) uninit read (`local_38` malloc-no-visible-writer — info-leak shape at
best) — NOTE; (8) int overflow sizes — DEAD (needs 4GB); (9) signedness in
`0x1e00` loop counters — DEAD (byte-count check catches); (10–11) format
string incl `%n` — DEAD (static fmts); (12) off-by-one NUL — PARKED
(`+1` allocs show awareness, none spotted); (13) wild copy — DEAD;
(14) null deref — N/A (DoS only); (15–16) type/vtable confusion, uninit
fn-ptr — PARKED (no evidence).
Protections/bypass: (17) ASLR defeat — N/A; (18) ROP/NX — UNNECESSARY;
(19) SSP — N/A; (20) GOT/import-table overwrite (`0x115384a0` table
exists!) — PARKED behind primary write primitive; (21) FORTIFY/PAC/CFI/
(24) stack-clash — N/A era; (22–23) PAC/CFI — N/A ARMv6.
Logic/state: (26/30) TOCTOU stat→read — DEAD (single-thread);
(27) dir traversal via SD names — LIKELY NEUTRALIZED (`10359810`
basename-after-last-`/`) but unproven end-to-end — NOTE;
(28) fail-open abuse — PROVEN, needs writer; (29) version DOWNGRADE to
1.1.x (empty `usb.key`!) — OPEN if 1.1.1 image + flash path found
(neither on disk); (31) event injection — PARKED (needs exec);
(32) MIF priv confusion — DEAD-ish (load-time sig check);
(33) sig-verify bugs — PARKED (separate RE); (34) rollback protection —
see 29.
Side channels: (35) timing oracle — REAL/impractical; (36) power/EM —
PARKED (lab); (37) error/log oracle (`sdautocopy.log` deltas?) — NOTE
(1-bit max, same as DIAG on/off); (38) cache timing — N/A.
Physical: (39) JTAG — OPEN/certain/invasive; (40) EDL-unfused — OPEN/cheap;
(41) glitching — PARKED (lab); (42) cold-boot RAM — PARKED;
(43) chip-off NAND read — OPEN/certain/invasive;
(44) UART console (zloader notes: uart1 gpio45/46!) — OPEN if pads
reachable, may give boot interrupt + logs; (45) USB-stack fuzz — PARKED;
(46) peripheral-as-host — SPECULATIVE.
Protocol: (47) DIAG pre-gate fuzz — OPEN (tool ready); (48) SPC defaults —
OPEN; (49) AT$QCDMG — OPEN/unconfirmed; (50) SMS/WAP remote — CLOSED;
(51) browser (reksio/rocketweb) vuln → file write — PARKED (big scope).
 actionable now without console: 29 (needs image), 44 (needs
probing); with console: A2/A5/A6/C1/C2/D2/EDL/1.1.x-downgrade/UART.

## 22. Flash/downgrade without physical access (2026-09-27)

Short answer: NONE exists. Every flash path needs something physical:
- FOTA (`fs:/shared/FOTA2.delta` + `.commit`, FOTA partition, apply code
  adjacent in APPS): carrier-delivered deltas, signed; network dead.
  Local planting needs EFS write (= DIAG). Circular.
- Download mode / QPST flash: needs DIAG (key) or EDL-USB (physical).
- JTAG / chip-off / EDL: physical by definition.
- SD autocopy / EMAPPLET: writes game partitions (`/mod`, `/mif`),
  never firmware partitions — no evidence otherwise.
- Remote (no-touch): SMS closed (§14); TecToy servers dead
  (`aquila.tectoy.com.br:8443`); WAP push → browser only.
- 1.1.x downgrade (empty `usb.key`) still needs a flash path + the
  1.1.1 image (neither on disk). The IDEA is alive; the DELIVERY is
  the same unsolved problem as everything else.
- Net: with zero physical access, only keygen/DB-leak works. All
  software vectors in §16/§21 assume at least SD+USB physical.

## 23. Other scenes: is physical really required? (2026-09-27)

Survey: every software-only console entry exploits a PARSER reachable
pre-auth — soundhax (m4a tags), bannerbomb (channel banners), savegames,
browsers, fonts. Phones same story: QPST/BitPim = USB physical; MSM7201A
Androids rooted via recovery/fastboot = buttons+USB physical.
- Zeebo's pre-DIAG SD surface is TINY: `61u.key` (bounded heap read +
  strcmp — safe) and `.dat` EXISTENCE check (no content parse).
  No media library, no browser, no savegame parsing at boot. Scene
  pattern says: nothing to bite on pre-gate.
- Parser-rich surfaces (`.mod` headers with sizes, `.mif`, images,
  fonts like `zeebosplash.rgb565.raw` — raw blit, unexploitable) all sit
  BEHIND install (= DIAG-gated copy) or in NAND games. Circular.
- The SOLE pre-gate exception candidates (both need hardware to test):
  (a) auto-copy/Text-Script running its copy WITHOUT DIAG (wiki says
  gated — unverified statically); (b) a latent bug in the two pre-gate
  readers (both audited safe).
- Verdict: YES, modding this console needs physical (SD+USB minimum;
  JTAG for certainty). No remote/software-only path exists or is
  likely. The realistic ladder: SD-trigger (garbage-key/autocopy) →
  USB (EDL/DIAG-fuzz) → JTAG. Budget effort accordingly.

## 24. Cross-scene class mapping (2026-09-27)

Surveyed: PS3 (CFW/HAN/HEN, HTAB glitch, qCFW), Wii (Twilight/Banner/BlueBomb),
3DS (soundhax/ninjhax/browserhax), Switch (Fusée/PicoFly), PS2 (FMCB/FreeDVDBoot),
PSP/Vita (TIFF/saves), PS4/5 (PPPwn/WebKit/BD-JB), Xbox (007/RGH/BadUpdate),
iOS (checkm8/unc0ver/TrollStore), Android (DirtyPipe/QuadRooter/Drammer/GBL).
- TRANSFERS: USB-boot-mode story (Fusée/EDL — strengthens our EDL probe);
  downgrade (PS3Xploit v1 — same as our 1.1.x idea, same missing pieces);
  CoreTrust≈our load-time sig check (already modeled); glitch-the-branch
  as alternative to timing-oracle (same lab bucket, deterministic-ish).
- PARKED BEHIND INSTALL: save-game/TIFF/image parsers (ChickHEN class) —
  Zeebo parses `.mod`/images/fonts, but all post-install (= post-DIAG).
  Circular until install primitive exists.
- N/A HERE: browser exploits (no WebKit — reksio is a socket client);
  kernel exploits (no Linux — REX/OKL4); PPPoE/WiFi (no such hardware);
  Rowhammer (needs exec first); BD-Java (nothing equivalent);
  QuadRooter-class (needs app context = unlock first).
- NET: survey confirms the map (§16/§21) instead of adding vectors.
  No scene has a software-only entry without a pre-auth parser, and
  Zeebo's pre-auth parser surface stays the two audited-safe readers.

## 25. FAT/LFN attack surface + CVE corroboration (2026-09-27)

- SD stack: HCC FAT LFN (`HCC_FAT_LFN_UNI ver:3.23`, `hfat_lfn.c`),
  hotplug handler (`fs_hotplug_sd.c`), fixed shortname buffers guarded
  by `Assertion pos + FS_SHORTNAME_PREFIX_LEN < sizeof(static_name_key)`
  (assertions compile out in release → the guarded overflow goes live).
  LFN buffer pool (`f_lfnint`) with alloc/free-failure strings.
- **CVE-2026-6688 (June 2026, runZero): FatFs LFN downstream-caller
  overflow** — 255-char LFN into short fixed buffers (CWE-120, CVSS 7.6,
  PoC exists, AV:P = malicious media). Different lib (ChaN vs HCC) but
  IDENTICAL bug shape to our §20 candidate (unbounded strcpy/strcat of
  names into 128B stack). Industry validation that this pattern delivers
  code exec from a crafted SD.
- Our EMAPPLET path builders are exactly the "downstream caller" role;
  LFN strings/hotplug refs unlocated in code (event-driven, same story).
- Kill-chain sketch (all-SD, pre-auth IF auto-copy runs w/o DIAG):
  crafted FAT (255-char LFN entries + deep dirs) → hotplug/key-open
  parses names → 128B stack smash (§20 shape) → no SSP/ASLR/NX → shellcode.
  Every link except the last data-flow hop is verified present.
- If auto-copy turns out DIAG-gated after all, same SD still works the
  moment ANY parsing runs (key open parses FAT structures regardless).

## 26. IMEI read/write paths (2026-09-27)

- READ, layered, all NV-sourced: NV items `NV_ESN_I` + `NV_UE_IMEI_I`
  via `esn_imei_read()`; SUPS consumer (`OEMSUPPS_IMEI Called`,
  dispatcher `FUN_1125548c` returning status 0–4); modem-side own copy
  (MMGSDI). Fallback cascade: `NVRead IMEI failed → use default`,
  `LCT_SIMCardCtl_CheckValidity, DEFAULT_IMEI`, down to `IMEI: 000000`
  — console boots without programmed IMEI.
- WRITE: none in firmware (reads + defaults only). Devkit IMEI changes
  were external (QPST NV write / JTAG / factory tool). Kills any
  remaining fused-ID theory input-side too.
- Moon's GBAtemp summary (5 points) archived:
  `docs/moon_gbatemp_summary_2026-09-27.md`. Compatible throughout;
  duplicate-pair stance agrees with spreadsheet-error theory.

## 27. OEMFS dead strings vs live call — injection smell check (2026-09-27)

Prompt: zeebo-lle `SDCC_FIRMWARE_MAP.md` (OEMFS strings + assert table with
zero code refs in APPS image) + suspicion of DIAG-time injected code.
- Verified: `OEMFS_Open/Read/NativePath` + `OEMFS.c` = genuinely
  unreferenced in APPS (our `FindStr` agrees: only hit is the log-adjacent
  area, no code refs). Dead metadata — or code living in another image.
- BUT the live `OEMFS_Test(%s)` call (`FUN_10af1534`, our resolve step)
  goes through veneer `0x109834cc` → wrapper `0x11155860` → import stubs
  (`0x11133a60` family) — the EXACT same shared-import dispatch as the
  strcmp call. Normal shared-lib mechanism, nothing injected-shaped.
- Caveat (our own lesson): ref-absence can mean undecoded regions, not
  absence — but two independent measurements (theirs + ours) + the live
  call resolving through standard imports = no positive evidence for
  injection. Closest real thing remains nand.py's absent BREW extension
  `.mod`s (UI widgets, not FS).
- Verdict: smell unfounded; OEMFS_Test is an ordinary import. The dead
  strings stay unexplained but inert.

## 28. `+LCTUSBLOCK` / AT command surface (2026-09-29, external analysis re-derived)

Trigger: Moon Sarito posted 4 photos of an LLM's read of a RAM/NAND/IMEI dump
("LCT USB LOCK", "comandos AT"). Everything below was **re-derived
independently from `1.1.2_APPS.bin`** (capstone, no Ghidra), then compared.

### 28a. Verdict per claim

| Claim from the external analysis | Verdict |
|---|---|
| `+LCTUSBLOCK` handler reaches a FS/RPC write routine through `0x10b96b70` | **CONFIRMED** — `blx #0x10b96b70` @ `0x10aff22a`; PLT slot → resolved stub `0x10333789` |
| That handler writes `/61u.key` | **CONFIRMED** — `adr r0,#0x14c` @ `0x10aff194` → `0x10aff2e4` = `"/61u.key"`; 3 more `adr` in the same function resolve to the same string |
| `+LCTSN` handler at `0x10AFF360` | **CONFIRMED**, address exact |
| `+LCTSN=…,5` reads SN, `…,7` reads IMEI | **CONFIRMED** — `cmp r0,#5`→`0x10b96ef4`, `cmp r0,#7`→`0x10b96efc`; response via `adr r1,#0x98` → `0x10aff45c` = `+LCTSN:"%s"` |
| That handler **removes** `/61u.key` | **REFUTED** — no `fs_remove` call in `+LCTUSBLOCK`; the `fs_remove is called` log string is a shared macro pool used by 3 functions, it does not prove a call |
| Provisioning interface, no keygen in the image | **CONFIRMED** (already our settled position, §2/§26) |

Its conclusion matches ours but the *evidence chain* is genuinely new: it is
an on-device **write primitive** for the key file, not just a read check.

### 28b. The AT command table (ATCOP)

The AT names at `strings_1.1.2_APPS.txt:235061+` are not a loose string list —
they are a **table of 0x2c-byte records** at foff `0x130c5bc`+ (vaddr
`0x113d05bc`+, segment `0x76000→0x1013a000`):

```
{ char name[16];
  u32 @+16 (0); u32 @+20 attrs; u32 @+24 (0);
  u32 @+28 param_tbl; u32 @+32 param_tbl2;
  u32 @+36 fn_ptr /* Thumb, bit0 set */; u32 @+40 }
```
stride `0x2c` (44 B). **The function pointer is at +36, not +32** — +28/+32
are param tables and reading +32 yields a plausible-looking `0x114503xx`
pointer, which is how two handler addresses in an earlier revision of this
table were wrong (see the correction below).

It is a stock **ATCOP/DSAT** command table — the LCT commands sit next to
`+FCLASS +ICF +IFC +IPR +CIMI +CGMR +GMI +GMM +GMR +GCAP +GSN +WS46 +DS +DR`.
So the AT processor lives in the **APPS image (ARM11)**, not the modem.

Extracted handlers. All of them read from **+36**; the five marked ✓ were
disassembled and confirmed instruction-by-instruction, the other six were
read from the table and each start-verified (`push {...lr}` at the address):

| Command | handler | | Command | handler |
|---|---|---|---|---|
| `+LCTUSBLOCK` | `0x10aff100` ✓ | | `+LCTSN` | `0x10aff360` ✓ |
| `+LCTSW` | `0x10aff33c` ✓ | | `+TESTINF2` | `0x10afeca4` ✓ |
| `+STORENEWPIN` | `0x10afef80` ✓ | | `+WRITEIMSIFILE` | `0x10afed2e` ✓ |
| `+DELETEIMSIFILE` | `0x10afee54` ✓ | | `+UIT` | `0x10aff318` |
| `+LCTUSBDISABLE` | `0x103611ee` | | `+LCTACTIVESIM` | `0x1036125c` |
| `+LCTSTOPTHESIM` | `0x1036128a` | | `+FCLASS` | `0x10afe796` |
| `+IFC` / `+DS` | `0x10afe650` | | `+GMI` / `+GSN` | `0x10360798` / `0x1036091c` |

**CORRECTION (2026-09-29, found by re-verification):** an earlier revision of
this table had `+TESTINF2 = 0x10aff3f4` and `+UIT = 0x10afeca4` — a one-row
shift from reading the fn pointer at +32. Both were wrong and are fixed above.
Nothing else in §28 depended on them.

`+TESTINF2` is worth a look: same shape as `+LCTUSBLOCK` (cmd id `0xb`, at
most one argument, takes one string of ≤ `0x80` bytes, then calls the same
FS/RPC family) — so it looks like a second file-writing command. Its target
path was not decoded.

The `0x10b96bXX` / `0x10b96efX` targets are **PLT slots** — ARM-mode
`ldr pc,[pc,#-4]` + inline offset (24 slots in `0x10b96b40`–`0x10b96c00`),
each loading an address relative to PC+8. Resolved targets:

| Call site | literal | → entry | prologue | used for |
|---|---|---|---|---|
| `0x10b96b98` | `0x10333d1d` | `0x10333d1c` | `push {r4,r5,r6,lr}` | fs nametest / status |
| `0x10b96bb8` | `0x10333b57` | `0x10333b56` | `push {r4,r5,lr}` | (error-path variant) |
| `0x10b96b40` | `0x1033368b` | `0x1033368a` | `push {r4,r5,r6,r7,lr}` | fs open |
| **`0x10b96b70`** | `0x10333781` | **`0x10333780`** | `push {r0..r7,lr}` | **fs write** (Moon's address, exact) |
| `0x10b96b50` | `0x103336f3` | `0x103336f2` | `push {r3..r7,lr}` | fs close |
| `0x10b965a8` | `0x1079c045` | `0x1079c044` | `push {r4,r5}` | strlen |
| `0x10b96edc` | `0x1079bcb9` | `0x1079bcb8` | `push {r0,r1,r2,r3}` | sprintf |
| `0x10b96ef4` | `0x10360f7b` | `0x10360f7a` | `push {r4,r5,r6,lr}` | SN read (mode 5) |
| `0x10b96efc` | `0x1036084b` | `0x1036084a` | `push {r0,r4..r7,lr}` | IMEI read (mode 7) |
| `0x10b96f04` | `0x10360ff5` | `0x10360ff4` | `push {r4,r5,r6,lr}` | SN write |
| `0x10b96f0c` | `0x10361135` | `0x10361134` | `push {r3..r7,lr}` | IMEI write |
| `0x10b96b30` | `0x10346b0d` | `0x10346b0c` | `push {r0,r1,r2,r4..r7,lr}` | FS resolve (used by `0x10aef9d0`) |
| `0x10b96e7c` | `0x1108d715` | `0x1108d714` | `push {r0,r1,r2,r4..r7,lr}` | AT number parser (LCTSN args) |
| `0x10b96e3c` | `0x1108d375` | `0x1108d374` | `push {r0,r1,r4,r5,r6,lr}` | token finalize |
| `0x10b96e44` | `0x1108d4ad` | `0x1108d4ac` | leaf | charset validator |

⚠ **All entries in this table were wrong until 2026-09-29 (§33a)** — the first
revision resolved them with a spurious `+8`, landing 6 bytes *inside* each
callee. Corrected here; 14 of 16 entries are start-verified against a `push
{...}` prologue, the other 2 (`0x1079c044` strlen, `0x1079bcb8` sprintf) also
have `push {r4,r5}` / `push {r0,r1,r2,r3}` prologues.

Same shape as §27's shared-import dispatch (`0x109834cc → 0x11155860` →
`0x11133a60` stubs): ordinary PLT indirection into the RPC/import region
around `0x1033xxxx`, nothing exotic. Note these are *PLT* slots, not the
long-branch veneers an initial Thumb-only scan suggested — that scan was
misdecoding the ARM half (exactly the caveat `tools/hunt_refs.py` documents).

The **slot encoding** is always ARM `ldr pc,[pc,#-4]`, but the **target's
mode comes from bit0 of (literal+8)**, not from the caller. Both PLTs
resolved land on Thumb (`0x10333780`, `0x103693e8`). I have assumed wrong
here three times — see §32a/§33a — so check the rule, don't trust the address.

### 28c. `+LCTUSBLOCK` decompiled semantics

```
[token+8] == 0xb           else → return 4
[token+0x40] <= 1          else → "Currently this is not supported" → return 4
arg = token+0xc; len = strlen(arg)
arg empty, or (arg[0] != '"' or arg[len-1] != '"')  → return 4
buf = malloc(len-1); memcpy(buf, arg+1, len-2)          // strip quotes
r0 = "/61u.key"                                        // 0x10aff2e4
  0x10b96b98(r0, 1, 0, resp)   // fs_nametest / status
  0x10b96bb8(r0, 0, resp)     // (error branch)
  fd = 0x10b96b40(r0, 0, &st, 0, &resp)
  0x10b96b70(fd, buf, strlen(buf), 0, &resp)   // ← the write (PLT → 0x10333780)
  if (written != resp.len) → return 4
  0x10b96b50(fd, 0, resp)                      // close
  free(buf)
```

So the command is `AT+LCTUSBLOCK="<content>"` → writes `<content>` verbatim
into `/61u.key`. **No key generation, no IMEI, no derivation** — a raw write.
Argument quoting is mandatory (0x22 at both ends) and max 1 argument.

### 28d. Path convention — the key inference

The same 5-RPC sequence appears in the sibling handlers, with **relative**
paths:

| Handler | path passed to the RPCs |
|---|---|
| `+WRITEIMSIFILE` ✓ | `lctsys/imsi.dat` (`0x10afef2c`) |
| `+STORENEWPIN` ✓ | `lctsys/61s.dat` (`0x10aff29c`) |
| `+LCTUSBLOCK` ✓ | `/61u.key` (`0x10aff2e4`) |

We already know the **absolute** form of the 61s.dat path is
`fs:/mcp/lctsys/61s.dat` (`0x11267a40`, §1). Therefore a relative path inside
this LCT subsystem resolves into the **internal `mcp` partition**, not `card0`.

**Strong inference (not proof): `+LCTUSBLOCK` writes `fs:/mcp/61u.key`** — the
file `check_61u_key` reads *first* (`0x108d08a4`). If that holds, the
validation is defeated without ever knowing a real key: write a chosen value
to the internal key and place the same value on the SD card, and
`strcmp(mcp, card0)` (§2d-i) matches. That converts the keygen problem into a
write problem — but only if the AT channel is reachable (§28f).

Caveat: `lctsys/61s.dat` is app-relative, `/61u.key` has a leading slash. A
leading `/` plausibly means "root of the current card" — same partition, but
worth confirming on hardware rather than assuming.

### 28e. Methodology fix: why §2b found zero refs

The `dsatparm_exec_*` log strings **do** have absolute references, just not
the kind we looked for. They are reached through a **log-record table** of
20-byte records at vaddr `0x111ddf00` (foff `0x1119f00`), indexed by
`{u32 line, u32 record_ptr}` 8-byte pairs in the function's literal pool:

```
… 0x10aff2d8: 00000948  111ddf5c      ← {line 0x948, rec}
  0x10aff2e0: 00000952  111ddf70
  0x10aff2e4: 2f363175 …                ← "/61u.key\0\0\0\0" INLINE here
  0x10aff2f0: 00000961  111ddf84      ← array resumes
record @0x111ddf70 = {0x13880961, 8, 0x108a5fbc, 0x108a5c6a, 1}
                     ^ runtime ptr   ^ msg     ^ "dsatparm.c" ^ ?
```

⛔ **CORRECTED 2026-09-29 (§36c): there is no code side at all.** The 20-byte
structures do contain pointers to the strings, but *nothing* points at the
structures — verified with zero references in the NAND image *and* in the
relocated 1.1.2 RAM dump. They are log-message tables left behind by a build
with logging compiled out. So these strings are **not** a route to code, in
principle rather than by scanner limitation.

### 28f. Open: AT channel reachability (blocking)

Everything above is gated on one unanswered question: **which physical port
carries this ATCOP/DSAT parser, and does it need DIAG unlocked?**

- If AT arrives on the DIAG port → circular, useless: DIAG is exactly what the
  key gates.
- If there is a pre-DIAG path (UART pads, boot/shell UART, a factory header)
  → the write primitive is reachable and §28d becomes an unlock path.

Evidence found, inconclusive: `Invalid DTR change: UART1`,
`diagcomm_assign_port_cb`, `fail to return DIAG port`,
`NV_HS_USB_DIAG_ON_LEGACY_USB_PORT`, and `..\..\data\atcop\src\dsatsms.c`
(ATCOP sources compiled into APPS). Nothing yet ties the parser to a specific
UART. **Do not assume either way** — this is the single highest-value unknown
and it is a hardware/port question, not a static one.

Cheap hardware test, if an AT-capable port exists: `AT+LCTUSBLOCK="AAAA"` then
check whether a new `/61u.key` appeared. Non-destructive if aimed at a
throwaway file first (e.g. `+LCTUSBLOCK` on a console whose key is already
removed, which is fail-open/DIAG-on anyway — that console is the safe test
subject).

### 28g. Scope boundary (legal)

`+LCTSN` read (IMEI/SN on your own device) is fine for this project.
**`+LCTSN` write mode alters a radio identifier** — in Brazil that is
Lei 12.735/2012 (confirm the exact article before citing it), and similar
elsewhere. It is explicitly **out of scope** here: we are not interested in
writing IMEI/SN, only in reading the command table. Recorded so nobody
"verifies" that path on a real cellular device.

## 29. AT channel reachability — investigation and its limit (2026-09-29)

Follow-up to §28f. Tried to settle statically whether the ATCOP parser is
reachable **without** DIAG. Could not. Recording what was established, what
was ruled out, and the best-fit model.

### 29a. The AT table is data-only reachable

The §28b sub-table (`0x113d05bc`, 0x2c-byte records) is pointed to by two
**data** structures:

| Structure | Layout | vaddr |
|---|---|---|
| master A | 16 B: `{name, id, param_tbl, fn}` — only 4 records valid at this stride (`D`, `S0`, `+FCLASS`, `+CBST`, ids `0x3b94`…`0x3bbe`) | `0x10568468` |
| master B | 32 B: `{name, fn, subtable, fn2}` — includes `+FCLASS` group, `+CBST` group, `$QCSIMSTAT` | `0x11452a60` |

The `id` values (`0x3b94`, `0x3ba2`, `0x3bb0`, `0x3bbe`, `0x3bde`) look like
dispatch IDs. Note `+LCTUSBLOCK`'s check was `[token+8] == 0xb` — a
*sub-argument* selector, **not** the command ID; don't conflate the two.

**Neither master is referenced by an absolute pointer from executable code.**
A raw LE32 scan for all four addresses returns one hit, at `0x10a6bba8`, and
that one is a **false positive** — a `switch` jump table
(`cmp r2,#0x58/0x70/0x80/0xa0/0xf4` + branches) that merely happens to contain
the bit pattern.

So access is via relocated/offset indirection — the same blind spot as §2b and
§28e. **Absence of an absolute code ref is not absence of a code ref** (the
§27 lesson again, now hit for the third time on this image). Chasing it
further needs relocation-aware analysis in Ghidra, not more raw scans.

### 29b. What the surrounding code says

- `..\..\..\..\platform\cs\src\OEM\OEMSerialPort\msm\OEMSerialPort.c` +
  `OEMSerialPort` + `Serial Port Profile` — a serial-port abstraction compiled
  into APPS. Candidate UART transport for the AT parser.
- `..\..\services\diag\diagcomm_sio.c`, `diagcomm_fwd.c`, and the
  `diagcomm_dancing_assign_port_cb` / `diagcomm_assign_port_cb called in IDLE`
  / `fail to return DIAG port` strings — the Qualcomm **DIAG port multiplexer**
  ("dancing" = dynamic port assignment). DIAG is a *logical* port bound to a
  *physical* transport at runtime, so this is where a USB/UART/TCP binding would
  be decided. Not decoded.
- `LCT_PEKTest` (`LCT_PEKTest Create AEECLSID_CONFIG`, `CFGI_MOBILEINFO`,
  `CFGI_SUBSCRIBERID`, `AEE_DEVICEITEM_CARD0_INFO` model/serial,
  `tDownloadInfo.bBKey/szServer/nAuth/nPolicy`, `CFGI_FIRMWARE_ID`) — a
  **factory test/provisioning applet**. This independently confirms the LCT
  command family is the manufacturer provisioning surface, and that `+LCTSN`
  (IMEI/SN) belongs to it, consistent with §26 (IMEI via NV + sysconfig files).

### 29c. Best-fit model (UNCONFIRMED — do not build on it)

```
USB (rear device port) ──► CDC "Modem" interface ──► modem AT (AMSS)
                                                        │ RPC
                                                        ▼
                                          APPS-side dsatparm.c (ATCOP)
                                          ├─ standard GSM commands
                                          └─ OEM LCT commands ──► FS/RPC
                                                (+LCTUSBLOCK writes /61u.key)
```

This explains why `dsatparm.c` is compiled into APPS (ARM11) while the standard
GSM command set is there too: the modem parses, OEM commands are proxied down
to the ARM11 side, which then does the filesystem work.

The catch: the wiki (`docs/tripleoxygen_wiki_diag_port.md`) says the rear USB
port is **disabled from factory** and offers the **Modem** interface only in
*Download* mode (Diag + NMEA + Modem); *Trace* mode gives Diag only. And the
port must first be mapped to **USB SER1** — via the `61u.key`, or via the
AUXSETTINGS applet (BREW Appmgr, itself a JTAG-only path per the wiki).

⇒ **On that model the Modem interface, and therefore `+LCTUSBLOCK`, is
downstream of the very key we are trying to obtain.** Circular. Both candidate
channels (UART via `OEMSerialPort`, USB Modem CDC) appear to sit behind the
gate. **No static evidence was found for a pre-DIAG AT path** — absence of
evidence, not evidence of absence (§29a).

### 29d. What settles it

Only hardware, and cheaply:

1. Does the console enumerate a **Modem** USB interface *before* any key is
   present? If no, §29c holds and the AT avenue is dead for pre-auth use.
2. Is there an accessible UART (pads) carrying AT at boot? (Notes already list
   UART pads as an unexamined avenue — this makes it a priority.)
3. If an AT-capable port exists at all: `AT+LCTUSBLOCK="AAAA"` then look for a
   new `/61u.key`. Best done on a console that is **already fail-open**
   (internal key removed ⇒ DIAG permanently on per §2/§4), so the test cannot
   brick anything and the console is already unlocked.

Do not burn more time on raw byte scans of this image for the table ref — §29a
shows that path is exhausted without relocation-aware tooling.

## 30. Validation control flow resolved; fail-open confirmed (2026-09-29)

Follow-up to §28/§29. Built `tools/find_str_refs.py` (§28e asked for it) and
it immediately closed the longest-standing open item in this project.

### 30a. §2b's "no code xrefs" — SOLVED

§2b reported `getReferencesTo()` empty and a zero-hit LE32 hunt for
`fs:/mcp/61u.key`, `fs:/card0/61u.key`, and left "re-derive from string xrefs"
as future work. They were never missing. They are loaded with a plain **Thumb
`adr`** — a PC-relative form that is neither an absolute dword nor a
`movw`/`movt` pair, so both earlier methods were structurally blind to it:

```
tools/find_str_refs.py firmware/1.1.2_APPS.bin --str "fs:/mcp/61u.key"
  adr @0x108d07ae  fn~0x108d07a0
  adr @0x108d081e  fn~0x108d081c
  adr @0x108d083e  fn~0x108d081c
```

Lesson (third instance, cf. §27 and §29a): on this image, "no reference
found" means "my method cannot see that addressing form", never "no
reference". Addressing forms actually observed here: absolute dword in a
data table, `adr`, `ldr`-literal, `movw`/`movt` pair. (Dropped from this list
in §36c: "pointer-to-record" — the record tables exist but are dead data with
no code referencing them.)

### 30b. The three key functions, and who calls them

| Function | Role | Direct callers |
|---|---|---|
| `0x108d06ee` | open one key file (76B stack buffer, vtable `+0xc` read, `+0x1c` seek/close) | 2 — both inside `0x108d081c` |
| `0x108d081c` | path-check both, open both, cache in a global, `strcmp`, report | **1** — `@0x108d2694` in `fn~0x108d25c2` |
| `0x108d07a0` | compare the *cached* buffers, free both, report | **0** direct callers found |

`0x108d07a0` having no caller is a lead, not proof: `find_callers` only sees
direct `bl`/`blx` (see its docstring), and an indirect call through a
function-pointer table would be invisible. The two functions are near-clones
— same compare, same report codes — which is what you expect from one being
reachable through a vtable and the other called directly.

### 30c. `strcmp` confirmed by disassembly

The compare call target `0x109834c8` is an **ARM-mode** tail branch
(`b #0x101d7ec8`), which is why a Thumb-mode scan of that region looks like
nonsense — the same ARM/Thumb confusion `tools/hunt_refs.py` warns about.
`0x101d7ec8` is the classic ARM optimized `strcmp`: `uqsub8` byte-difference
accumulator, big-endian word compare, `rrx`-based sign fixup. 24 call sites
across the image. **The §2d-i model is confirmed at instruction level.**

### 30d. `check_61u_key` control flow (`0x108d081c`)

```
0x108d081c  push {r4,lr}
0x108d081e  adr  r0, "fs:/mcp/61u.key"
0x108d0820  bl   pathcheck          ; 0x10af1534
0x108d0824  cmp  r0, #0
0x108d0826  beq  +0x10              ; mcp path ok -> continue
            report(code 6); return
0x108d0834  adr  r0, "fs:/card0/61u.key"
0x108d0836  bl   pathcheck
0x108d083a  cmp  r0, #0
0x108d083c  bne  FAIL
0x108d083e  adr  r0, "fs:/mcp/61u.key"    ; bl 0x108d06ee
0x108d0846  str  r0, [g,#4]                ; g.mcpbuf
0x108d0848  adr  r0, "fs:/card0/61u.key"  ; bl 0x108d06ee
0x108d084e  str  r0, [g,#8]                ; g.cardbuf
0x108d0850  ldr  r2, [g,#4]
0x108d0852  cmp  r2, #0
0x108d0854  beq  FAIL            ; <<< mcp MISSING lands here
0x108d0856  cmp  r0, #0
0x108d0858  beq  FAIL            ; card0 missing -> same place
0x108d085e  blx  strcmp(mcpbuf, cardbuf)
0x108d0862  cmp  r0, #0
0x108d0864  bne  FAIL
            report(code 6); return
FAIL:       report(code 0); return
```

Both files must open non-NULL **and** match. There is no length check, no
charset check, no crypto — consistent with §2/§30c.

### 30e. Fail-open: CONFIRMED — and an earlier draft of this section was wrong

This section went through one false start, and the correction is the useful
part, so the wrong reasoning is kept below rather than deleted.

**What I first wrote (WRONG):** "a missing `mcp/61u.key` branches to the same
FAIL label as a strcmp mismatch, so fail-open is refuted." That was true only
of one of the two "missing" cases — the one where the path resolves but
`open` returns NULL. I had not traced the *resolve* branch at all. Both
`README.md` and `HANDOFF.md` were downgraded on that basis; both are restored
below.

**Full chain, traced end to end:**

```
check_61u_key 0x108d081c
  adr  r0, "fs:/mcp/61u.key"
  bl   0x10af1534                       ; resolve/test helper
  cmp  r0, #0
  beq  0x108d0834                       ; ==0  -> continue to card0 + strcmp
  movs r1, #6 / report(0,6) / pop       ; !=0  -> report 6, return

helper 0x10af1534
  bl   0x10aef9d0                       ; the real path resolve
  mov  r4, r0
  cmp  r4, #0
  beq  0x10af1568                       ; resolve FAILED
  ... fs_nametest RPC 0x10b96b98 into [sp+4],[sp+5] ...
  [sp+4]=0x0d ; return 13               ; <- the resolve-failed path

0x10aef9d0 (resolve)
  blx  0x10b96b30                       ; FS resolve RPC
  cmp  r0, #0
  bne  -> logs error, returns 0         ; nonzero RPC result = failure
```

So for an **absent** `mcp/61u.key`: resolve fails → helper returns **0x0d** →
`check_61u_key` takes the `!= 0` branch → `report(0, 6, …)`.

**`0x0d` is exactly the code the strcmp-equal path reports** (`movs r1,#6` @
`0x108d0868`). Both "keys match" and "internal key does not resolve" report
code 6; only "opened but NULL" and "strcmp mismatch" report code 0
(`0x108d0870`). **That is fail-open, and it holds.** The Hospital behaviour
is explained by it after all — no rival explanation needed.

The single direct caller ignoring the return value is *consistent* with this:
the decision is delivered through the report/event channel, not the return,
so a call site that does not branch on the return is not evidence against
fail-open. That inference of mine was also wrong.

**The `61u.key.bad` prediction is unchanged and correct**: garbage content ≠
internal content → strcmp mismatch → code 0 → no unlock.

### 30e-bis. What is still open (unchanged, pre-existing)

1. **What report code 6 vs 0 actually does.** → **MOOT, see §32c.** The
   callee (`rdevmap_clnt.c`, §32b) does not *branch* on `r1`; it ships it
   as RDevMap RPC argument 2 (§32c, corrected). "SUCCESS(0,6)" as a *local*
   code is retired; 0 vs 6 is real payload, interpreted wherever the RPC is
   served.
2. **Why a present, non-empty `mcp/61u.key` short-circuits.** → **RESOLVED
   in §31**: the `ldrb` was reading the first byte of the *resolve result
   buffer*, not file content, and the status goes through a translation
   table. Both "absent" and "present non-empty" return nonzero and take the
   same early `report(0,6)`. The strcmp is a narrower path than §30e
   implied. See §31c/§31d.

### 30f. `usb.key` — real lead, still undecoded

The 1.1.2 image carries a second, parallel mechanism, and it is not dormant:

| String | vaddr | Referencing site | Kind |
|---|---|---|---|
| `cannot find card0 usb.key` | `0x104f43e5` | `0x10c4cdd8` | data table |
| `we found the usb.key in card0` | (adjacent) | — | — |
| `cannot create usb.key` | `0x1120e293` | `0x102d6b20` | data table |
| `/mmc1/usb.key` | `0x10763d70` | `adr @0x10763af0` in `fn~0x107638ec` | **instruction** |
| `/usb.key` | `0x1120e2a1` | — | — |

`fn~0x107638ec` is in `fs_hotplug.c` (the `Assertion hdev->dev_state ==
DEV_UNMOUNT` / `fs_hotplug` strings are in that function) and builds
`/mmc1/usb.key` — a **raw block-device** path, so the hotplug path touches
`usb.key` directly, below the BREW filesystem. The two `data`-table hits sit
in what turned out to be branch/data tables whose indexing code is not
identified (`0x102d6b20` decodes as a table entry, not an instruction).

Why it matters: per the wiki an **empty `usb.key`** on the SD enabled the
diagnostic port on 1.1.1. If 1.1.2's check is presence-only, that is an
unlock needing no key at all. Our notes treat `usb.key` only as a
"parallel mechanism" (line 15) and the "presence-only" avenue as dead — but
that dead-ness argument was made about `61u.key`'s `strcmp`, never about
`usb.key` itself. **Untested, and cheap to test**: empty `usb.key` at the SD
root on a locked console. Recorded as open, not as a claim.

## 31. The status translation table — and why the strcmp is a *narrow* path (2026-09-29)

Follow-up to §30e-bis, which asked what `0x10af1534` actually returns. It does
**not** return the raw status: the return value goes through a translation
table, and decoding it changes the picture.

### 31a. `0x10aef9d0` (path resolve) — real contract

```
0x10aef9d0  push {r3,r4,r5,r6,r7,lr}
            r6 = path string
            r4 = global; r5 = r1 + [r4+4]*0xfc     ; rotating pool, 8 slots
            blx 0x10b96b30                          ; FS resolve RPC(path, slot, &st, 0xfc)
            cmp  r0, #0 ; beq 0x10aefa0c             ; RPC nonzero == FAILURE
            ...log... movs r0, #0 ; pop              ; -> returns 0
0x10aefa0c  rotate counter, log
0x10aefa30  mov r0, r5 ; pop                        ; -> returns pointer to 0xfc-byte slot
```

So: **returns 0 on failure, a pointer to a result buffer on success.** The
`ldrb r0,[r4]` test in the helper therefore reads the first byte of the
*resolve result buffer* — a device/type/handle byte, **not** file content.
That kills the reading in §30e-bis-2 that "a present, non-empty key
short-circuits", which had `ldrb` reading as if it were content.

### 31b. `0x10aefaa4` — the status → EE-code table

```
0x10aefaa4  movs r1, #0
            ldr  r2, [pc, #0x1f8]      ; table base = 0x11425440
loop:       lsls r3, r1, #3 ; adds r3, r3, r2 ; ldrb r3, [r3, #4]   ; key
            cmp  r3, r0 ; bne next
            ldr  r0, [r2, r1*8]         ; result dword            ; -> return it
next:       cmp  r1, #0x11 ; blo loop
            movs r0, #1 ; bx lr         ; default
```

Entry layout `{u32 result; u8 key; u8 pad[3]}`, 17 entries, scanned linearly.
Decoded values (all verified by reading the table at `0x11425440`):

| key | → result | | key | → result |
|---|---|---|---|---|
| `0x00` | 0 | | `0x13` | 261 `0x105` |
| `0x04` | 263 `0x107` | | `0x16` | 262 `0x106` |
| `0x05` | 256 `0x100` | | `0x07` | 256 `0x100` |
| **`0x06`** | **257 `0x101`** | | `0x0b` | 266 `0x10a` |
| `0x08` | 265 `0x109` | | `0x0a` | 266 `0x10a` |
| `0x09` | 258 `0x102` | | `0x03` | 266 `0x10a` |
| `0x0c` | 14 `0x0e` | | `0x1c` | 261 `0x105` |
| **`0x0d`** | **259 `0x103`** | | `0x1e` | 267 `0x10b` |

The `0x10x` values are **BREW `EE_*` error codes**, not small enums. This is
almost certainly the "event gate `0x97`/`0x10a`" the older notes (§2d-i)
referred to — `0x10a` is right here in this table, reached from keys `0x03`,
`0x0a`, `0x0b`. So that old "event gate" label was pointing at *this*
mechanism all along.

### 31c. Consequence: the strcmp is a narrow path, not the main one

`0x10af1534` returns `map(raw)` where raw is:
- `0x0d` when the resolve RPC failed → **returns 259**
- `6` when resolve OK, open status 0, nametest status 0, and the resolve
  buffer's first byte nonzero → **returns 257**
- `0` only when the resolve succeeded and all of those were zero → **returns 0**

Back in `check_61u_key`:

```
bl 0x10af1534 ; cmp r0,#0 ; beq continue
                -> report(0,6) ; return          ; r0 = 257 OR 259
continue:  ... card0 resolve, open both, strcmp ...
           equal -> report(0,6) ; return
           else  -> report(0,0) ; return
```

**Both an absent internal key (259) and a present non-empty one (257) take
the same early `report(0,6)` branch.** So the mcp key's *presence* is not
what selects the strcmp — only the narrow "resolve succeeded with an
all-zero status" state reaches the comparison at all.

§30e's conclusion survives and gets sharper: an absent `mcp/61u.key` and a
matching pair both report code 6, while a genuine mismatch and an
open-NULL report code 0.

### 31d. Interpretation, and the one thing still not known

If `report(0,6)` meant "unlock", then *every* console with a present non-empty
internal key would unlock without the SD key ever being compared — which
contradicts the entire premise of the project. So `report(0,6)` almost
certainly does **not** mean "unlock". The coherent reading:

> code 6 = *no comparison was performed* → the port state is whatever the
> persisted AUXSETTINGS Port Map says. The `61u.key` strcmp is a **narrow
> extra path** that only runs in the all-zero-status case, and code 0 =
> *compared and rejected*.

This is inference, not proof. It rests on (b) being untenable, which is an
argument from the project's own premise rather than from the code. Two things
would settle it:

1. **The consumer of the report codes** — `0x1079e4a0` is a PLT slot →
   `0x103693e8`; it ships `r1` ∈ {0,6} as RDevMap RPC arg 2. The open item
   is the *server* side of that RPC, not this function.
2. **The `0x97`/`0x10a` event gate** named in §2d-i — now localised to this
   table, so the consumer of `0x10a` is the same place to look.

If (1) shows code 6 → enable, then the strcmp is near-dead and the real
mechanism is the persistent Port Map, and the whole "needs the key" story
becomes a question about which path a given console takes. That would be a
larger rewrite than anything in §28–§31, and it is exactly why this stays
flagged as open rather than concluded.

## 32. `result_setter` is the **RDevMap RPC client** (2026-09-29; §32c corrected by §33a)

Closes most of §30e-bis-1 / §31d-1. The "result setter" the old notes
invented a meaning for is an identifiable Qualcomm service, and the success
code that was carried through every document turns out not to be a code.

### 32a. PLT resolution, done correctly this time

`0x1079e4a0` is an ARM PLT slot: `ldr pc,[pc,#-4]` + inline literal. The
literal is loaded **into PC directly** — it is not PC-relative, so there is
**no `+8`** (that form belongs to `add pc, pc, #imm`, a different PLT
variant). bit0 of the loaded value selects the target's instruction set:

```
0x1079e4a0  04 f0 1f e5   ldr pc,[pc,#-4]     ; loads from 0x1079e4a8
            e9 93 36 10   value  = 0x103693e9  ; bit0 set -> THUMB
            -> entry 0x103693e8  (push {r0,r1,r2,r4,r5,r6,r7,lr})
```

⚠ **I got this wrong three times in one session**, and the errors compounded:
1. assumed every PLT target is ARM (§28b);
2. assumed a Thumb caller keeps the target in Thumb;
3. added a spurious `+8`, which put **every** resolved address 6 bytes
   *inside* its callee — so §28b's whole table was wrong, and §32c's
   conclusion was drawn from the middle of a function.

Correct rule, one line: **`entry = literal & ~1`, mode = Thumb if `literal & 1`.
No offset at all.** Always start-verify the result against a `push {...lr}`
prologue; 17 of the 21 PLTs resolved in §33a land exactly on one, and the
other 4 are leaf functions. If your address is a few bytes into a function,
you have the `+8` bug.

### 32b. The function is `rdevmap_clnt.c`

`0x103693e8` loads the filename literal `rdevmap_clnt.c` for its error
logging. The whole `rdevmap` string inventory in the image:

```
rdevmap_null: No client for task %d
rdevmap_null: RPC call rejected, reject status = %d
rdevmap_null: Error on server side, error status = %d
rdevmapcb_null_0: XDR_MSG_SEND failed
```

`rdevmap` = **RDevMap**, Qualcomm's remote *device map* service: the RPC
service that maps SIO/port devices (DIAG, NMEA, modem/AT) onto transports.
`rdevmap_null:` is the client-side null-RPC stub, the same shape as the
`pm_strobe_*` RPC strings elsewhere in the image.

**This is the same subsystem the wiki's AUXSETTINGS path drives** ("SIO
Configuration > Port Map > Diag → USB SER1"). So `check_61u_key` does not
end in a local "set result" — it ends in an **RPC to the port-mapping
service**. That makes §31d's "the port state comes from the persisted Port
Map" hypothesis concrete rather than speculative.

### 32c. ⚠ `r1` is NOT dead — the tuple is the RDevMap RPC argument list

**This section originally claimed the opposite and was wrong.** It was written
against `0x103693f0`, which — per §33a — is *six bytes inside* the real entry.
The real entry is `0x103693e8`, and it saves the caller's arguments:

```
0x103693e8  push {r0, r1, r2, r4, r5, r6, r7, lr}
0x103693ea  sub  sp, #0x30
0x103693ec  mov  r7, r2          ; caller's r2 (the fmt string) -> r7
0x103693ee  mov  r6, r1          ; caller's r1 (0 or 6)         -> r6
0x103693f0  blx  0x101da0c0      ; <- what I mistook for the entry
...
0x1036942a  ldr  r5, [pc, ...]   ; RPC program/interface id
0x10369438  movs r3, #2
0x1036943c  blx  0x101da0d0      ; RPC begin, 2 args
0x10369440  ldr  r1, [sp, #0x30] ; the caller's r0
0x10369444  blx  0x101da0d8      ; append arg 1
0x10369448  mov  r1, r6          ; <<<< the caller's r1: 0 or 6
0x1036944c  blx  0x101da0d8      ; append arg 2
0x10369450  mov  r0, r7          ; the caller's r2 (fmt)
0x10369452  blx  0x101da140      ; append string
```

`0x101da0c0/0x101da0d0/0x101da0d8/0x101da140` are themselves ARM import
thunks (`0x101daXXX` → tail-branch region `0x101d9bXX`) and resolve to
`0x10b2e85a` / `0x10b2d680` / `0x10b2d46c` / `0x10b2e874` — a lock, an
RPC-begin, an RPC-append-arg and an RPC-append-string. Classic XDR
marshalling.

**Corrected conclusion, in two parts:**

1. **"SUCCESS(0,6)" is still not a local success code.** Nothing on this
   side branches on 0 vs 6; the function is a marshaller. So the old reading
   "match → SUCCESS(0,6) → event gate" remains wrong as a *control flow*
   description.
2. **But 0 vs 6 is not meaningless either.** It is the **second argument of
   the RDevMap RPC**. The distinction between "keys match" and "internal key
   unresolvable" is carried into the service call, and the decision is made
   wherever the RPC is served.

So the honest statement is narrower than either of my previous two: the
caller-side tuple is RPC payload, not a return code and not dead. The
0-vs-6 semantics are still unknown — but they are now known to *be sent*,
which is progress over both earlier claims.

### 32d. What this leaves open (and it is now a *different* open item)

`r0` is 0 on the early and FAIL paths and the strcmp result (0) on the match
path, so `r0` is 0 in all three — but `r1` is 6 / 6 / 0, and per §32c that
*is* shipped as RPC argument 2. So the three calls differ in the payload even
though the first argument is uniformly 0.

Next step is the RDevMap RPC interface id loaded at `0x1036942a` and the
server side of it, to learn what argument 2 = 6 vs 0 does. Note the server
may not be in this image at all: the `rdevmap_null:` strings are the
*client-side null-RPC* stubs, so the service may be a different process
entirely — which would also explain why the decision has never been visible
from the APPS side.

**Do not restate "event gate 0x97/0x10a" as a mechanism until that is
decoded.** `0x10a` is real (§31b, an `EE_*` code in the FS-status table), but
whether it gates the DIAG enable is still unestablished.

## 33. `+LCTSN` decoded, and a PLT bug that had corrupted §28/§32 (2026-09-29)

Two things: the `+LCTSN` investigation requested, and a methodology bug that
invalidated part of §28b/§32c. The bug is documented first because it changed
conclusions, not just addresses.

### 33a. The PLT resolution rule (and how I got it wrong)

`ldr pc, [pc, #-4]` loads the following word **into PC directly**. There is
**no `+8`** — that offset belongs to the `add pc, pc, #imm` PLT variant, a
different encoding. I used `literal + 8`, which put every resolved address
**6 bytes inside the callee** and produced three separate wrong conclusions:

- §28b's whole resolution table (now corrected, every entry start-verified);
- §32a's "the bit0 of literal+8 selects the mode";
- **§32c's "r1 is a dead argument"**, which was read off the middle of a
  function and is retracted.

The rule, verified on 21 PLTs:

> `entry = literal & ~1`; mode is Thumb if `literal & 1`.
> No offset. Always start-verify: of the 21 PLTs resolved in §33a, **19**
> begin with a `push {...}` prologue and 2 (`0x10b96e44 → 0x1108d4ac`,
> `0x101da0c0 → 0x10b2e85a`) begin with other instructions.

If a resolved address looks like the middle of a function, you have the `+8`
bug — which is exactly how it was caught. Third distinct PLT/veneer mistake
this session, after §28b and §32a. **The lesson is not "be careful with
PLTs"; it is that any indirection layer needs a positive verification step
(prologue check), not a plausible-looking decode.**

### 33b. `+LCTSN` structure

Handler `0x10aff360`, entry `push {r4,r5,r6,lr}`:

```
r6 = token (r2), r5 = response buffer (r3), r4 = 0
switch (token[8]):
  case 0xb:  mode-11 path
  case 7:    -> 0x10afe650  (tokenizer dispatch, see 33d)
  default:   return 4
```

Mode-11 path:

```
memset(global, 0, 0x43)              ; 0x43 = 67-byte global value buffer
r4 = parse_args_0x10afe6b0(token, &buf, &state)
if r4 != 0 -> return r4
if state[4] != 0:  WRITE path   (see 33c)
else:              READ path
   mode = state[0]
   if mode == 5: r4 = SN_read (0x10360f7a)      ; entry 0x10b96ef4
   if mode == 7: r4 = IMEI_read (0x1036084a)    ; entry 0x10b96efc
   if r4 == 0: sprintf(resp + used, '+LCTSN:"%s"', global)
```

All seven `ldr rX,[pc,#imm]` in the handler resolve to the **same** literal
`0x10aff458`, whose value `0x1434d881` is **outside every LOAD segment** — a
load-time-relocated pointer to the 67-byte global. So read and write share one
value buffer, and the only thing distinguishing SN from IMEI is *which of four
functions* is called. The U610 doc's `AT+LCTSN=0,5` (SN) and `AT+LCTSN=0,7`
(IMEI) match the mode selectors exactly; the leading `0` is not consumed here,
so it is handled by the generic tokenizer at `0x10afe6b0`.

Response format string `+LCTSN:"%s"` at `0x10aff45c` (confirmed by
`adr r1, #0x98` @ `0x10aff3c2`).

### 33c. The write path exists — documented, not pursued

`state[4] != 0` (i.e. an extra argument was supplied) routes to:

```
if mode == 5: SN_write    @ 0x10360ff4   (PLT 0x10b96f04)
if mode == 7: IMEI_write  @ 0x10361134   (PLT 0x10b96f0c)
```

Both are ordinary functions with normal prologues. **That is as far as this
goes, deliberately.** Writing a device's IMEI/SN alters a radio identifier,
which is a separate legal category from reading it (Lei 12.735/2012 and
equivalents elsewhere — confirm the exact article before citing). §28g keeps
this out of scope and that stands: the useful product of this section is that
the path *exists* in the image and is reachable by the same command, which is
a reason to keep the scope boundary, not to remove it.

### 33d. `0x10afe650` is a tokenizer, not a write path

Earlier (§28b) I noted `+DS`/`+DR`/`+LCTSN` share a pointer to `0x10afe650`
and guessed it was a shared sub-command. It is not specific to LCTSN: it
re-reads `token[8]` and dispatches on `1 / 0xb / 5 / 7` to four different
tokenizers (`0x10afe5ac`, `0x10afe484`, `0x10afe226`, `0x10afe10a`). The
`token[8] == 7` route lands in `0x10afe10a`, which validates input against a
character class — the literal `'(20,21,23-7E)'` at `0x10afe156`'s pool — and
appends a NUL terminator. **Generic AT argument tokenizing.** So
`AT+LCTSN` with `token[8] == 7` is not a hidden third mode.

## 34. RDevMap is cross-image; and `usb.key` is written by the AT layer (2026-09-29)

Two answers to open questions: where the RDevMap *server* lives (§32d), and
who creates `usb.key` (§30f).

### 34a. RDevMap: client in APPS, service in AMSS

§32d asked whether the port-mapping service is in this image. Split answer,
both halves verified:

| | image | evidence |
|---|---|---|
| client | **APPS** | `rdevmap_clnt.c`, `rdevmap_null:*`, `rdevmapcb_null_0: XDR_MSG_SEND failed`, `unable to register (RDEVMAPCBPROG, RDEVMAPCBVERS, sm)` |
| service | **AMSS** | `rdevmap_svc.c`, `rdevmap.c`, `sdevmap.c`, `unable to register (RDEVMAPPROG, RDEVMAPVERS, sm)` |

So `check_61u_key` → APPS `rdevmap_clnt.c` marshals the tuple → **RPC crosses
into the modem image** → AMSS `rdevmap_svc.c` serves it. The decision the
project has been unable to see from the APPS side is on the other side of
that RPC. (AMSS is also where `rex_*` assertions and the QMI/WMS stack live,
consistent with §2e's ARM11-only finding for the *key check* while the
*effect* is not ARM11-only.)

What the AMSS side says the service does — `rdevmap.c` strings:

```
rdm_assign_port called in ISR      rdm_notify called in ISR
rdm_close_device called in ISR     BT SPP
Invalid cmd: %d      wrong device: %d     wrong service: %d
Invalid DEVMAP State: %d                  wrong srv: %d
can't create efs file, %d        can't update mapping, %d
```

RDevMap is a **device → service → transport map, persisted in EFS** with
`rdm_assign_port` / `rdm_notify` as the mutators. That is precisely the
wiki's AUXSETTINGS "SIO Configuration > Port Map > Diag → USB SER1".

The validation strings matter: the RPC payload is validated as
**(cmd, device, service)**. So the APPS-side `r1` ∈ {0, 6} is far more
likely to be a **command selector** interpreted in AMSS than a boolean — which
fits §32c (it is shipped as argument 2 and nothing branches on it locally)
without needing the `SUCCESS(0,6)` reading that was retired. **Still an
inference**: pinning it down means finding the `cmd` switch in AMSS
`rdevmap.c`, which is the next task (§34c).

### 34b. `usb.key` is *created* by the AT layer

§30f found `cannot create usb.key` sitting in a data table and left the
consumer unidentified. The log records identify it:

| record | message | file | meaning |
|---|---|---|---|
| `0x102d6b0c` | `AT disable usb` | **`dsatact.c`** | an AT command that disables USB |
| `0x102d6b20` | `cannot create usb.key ` | **`dsatact.c`** | the AT layer creates `usb.key` |
| `0x102d6b34` | `AT active sim card` | **`dsatact.c`** | (neighbour) |
| `0x10c4cdd8` | `cannot find card0 usb.key ` | `fs_hotplug.c` | the **check**, on card0 |
| `0x10c4cdec` | `we found the usb.key in card0` | `fs_hotplug.c` | ditto, success branch |

`dsatact.c` is the DSAT **action** dispatcher — the same DSAT/ATCOP family as
`dsatparm.c` and the §28b command table. Its surrounding string pool is
unambiguously the GSM 27.007 interpreter:

```
Problem reading IMEI from NV       Problem reading ESN from NV
Problem reading sn from NV        IMEI not programmed in NV
sn not programmed in NV           Storing S registers & V.250 registers into NV
ATH cmd not in online_cmd_mode and +CVHU != 1
Processing command -- ATDI / ATDL        AT&S0 setting failed / AT&S1
Response too long for one DSM item       Dial string invalid in restricted mode
```

So there are **two** halves to `usb.key`, in different files:
`fs_hotplug.c` **checks** it on card0 and builds the raw block path
`/mmc1/usb.key` (the only *instruction* reference to any `usb.key` string,
`adr @0x10763af0` in `fn~0x107639da`), and `dsatact.c` **creates** it from an
AT command.

Two consequences:

1. The §30f question — is the 1.1.2 `usb.key` check presence-only? — is still
   open, but the check is now localised to `fs_hotplug.c` around the log
   records at `0x10c4cdd8` / `0x10c4cdec`, and the create path to
   `dsatact.c` around `0x102d6b20`.
2. **The AT surface is bigger than §28b showed.** Those 17 records were one
   sub-table; the master structures at `0x10568468` / `0x11452a60` point at
   least two (`0x113d05bc`, `0x113d507c`). `AT disable usb` is not among the
   17, so there are more command groups to map. The §28b "full AT surface"
   framing was too strong.

### 34c. Next tasks, in order

1. **AMSS `rdevmap.c` cmd switch** — the highest-value item: it decides
   whether `r1` = 6 vs 0 means "assign port" or "no-op", i.e. whether the key
   check *actively* enables DIAG. Needs the same log-record-table hop as
   §30a, on the AMSS side.
2. **`fs_hotplug.c` `usb.key` check** — presence vs content. Cheap once the
   function is located, and it is the test most likely to hand us a keyless
   unlock on 1.1.2.
3. **`dsatact.c` usb.key creator** — which AT command, and what it writes.
   Not pursued if it means writing identifiers; `usb.key` is not an identifier,
   so unlike §33c this one is in scope.
4. **Remaining AT sub-tables** — `0x113d507c` and whatever else the master
   structures reference.

## 35. `usb.key` reaches the SAME RDevMap state as a valid key — and one unknown remains (2026-09-29)

This is the most decision-relevant result of the session, and it is *almost*
complete. One value interpretation stands between it and a keyless unlock.

### 35a. The `usb.key` check, in `fs_hotplug.c`

`fn~0x107639da`, reachable and start-verified (`push {r4,lr}` @ `0x107639da`):

```
0x107639dc  ldr  r0, [pc,#0x108]     ; a relocated state struct
0x107639de  ldrb r1, [r0, #4]        ; a one-shot flag
0x107639e0  cmp  r1, #0
0x107639e2  bne  0x107639e8
0x107639e4  movs r0, #0 ; pop {r4,pc} ; not armed -> do nothing
0x107639e8  b    0x10763aec
...
0x10763aec  movs r1, #0
0x10763aee  strb r1, [r0, #4]         ; disarm (runs once)
0x10763af0  adr  r0, #0x27c           ; 0x10763d70 = "/mmc1/usb.key"   raw block path
0x10763af2  blx  0x105c2f7c           ; fs open        (PLT 0x112a116a)
0x10763af6  mov  r4, r0
0x10763af8  cmp  r4, #0
0x10763afa  bge  0x10763b0a           ; opened OK -> continue
0x10763afc  ... log ...
0x10763b08  pop  {r4,pc}              ; <<< NOT OPEN: return, no RDevMap call
0x10763b0a  ... log ...
0x10763b16  blx  0x105c2f84           ; fs close       (PLT 0x112a145a)
0x10763b1c  movs r1, #2
0x10763b1e  adr  r0, #0x268           ; 0x10763d88 = "/usb.key"        BREW path
0x10763b20  blx  0x105c2f7c           ; fs open
0x10763b24  cmp  r0, #0
0x10763b26  blt  0x10763b08
0x10763b28  blx  0x105c2f84           ; fs close
0x10763b2c  movs r2, #0
0x10763b2e  movs r1, #6               ; <<< arg2 = 6
0x10763b30  movs r0, #0
0x10763b32  blx  0x1079e4a0           ; RDevMap client
0x10763b36  movs r2, #0
0x10763b38  movs r1, #4               ; <<< arg2 = 4
0x10763b3a  movs r0, #1
0x10763b3c  blx  0x1079e4a0           ; RDevMap client
0x10763b40  pop  {r4,pc}
```

The two log arguments are relocated pointers `0x10c4cdd0` / `0x10c4cde4` (seen
at `0x10763d80` / `0x10763d84`), immediately adjacent to the §34b log records
at `0x10c4cdd8` = `cannot find card0 usb.key` and `0x10c4cdec` = `we found the
usb.key in card0`. So this is unambiguously the card0 `usb.key` check, and it
probes **both** the raw block path and the BREW path.

### 35b. The asymmetry that matters

| condition | RDevMap calls |
|---|---|
| `usb.key` **absent** (open fails) | **none** — early `pop` at `0x10763b08` |
| `usb.key` **present** | `report(0, 6)` **then** `report(1, 4)` |
| 61u.key: strcmp match | `report(0, 6)` |
| 61u.key: mismatch | `report(0, 0)` |
| 61u.key: mcp unresolvable | `report(0, 6)` |

**`usb.key` being present drives argument 2 = 6 — the same value a valid
`61u.key` match produces.** And the three distinct values observed across the
image (0, 4, 6) confirm §34a's inference: argument 2 is a **state/command
selector**, not a boolean.

So the two unlock routes converge on one RDevMap state. The wiki says an
empty `usb.key` opened the diagnostic port on 1.1.1, and the firmware that
implements that route is still in 1.1.2.

### 35c. The one thing that is not yet proven

Everything above is verified at instruction level. What is **not** established
is what the RDevMap service does with argument 2 = 6 — i.e. whether 6 is the
"port enabled" state. That is the same single unknown as §32d/§34c, and it is
the *only* thing between this section and a documented keyless unlock on
1.1.2.

Two ways to close it:

1. **AMSS `rdevmap.c`** — decode the `cmd` switch behind
   `Invalid cmd: %d` / `wrong device: %d` / `Invalid DEVMAP State: %d`.
2. **Hardware, and it is one file.** An empty `usb.key` at the SD root of a
   **locked** 1.1.2 console. If the port appears, the whole chain is confirmed
   end to end and no key is needed. If it does not, then argument 2 = 6 is not
   the enable state and the two routes only look similar.

Option 2 is the cheapest experiment the project has — cheaper than the
`61u.key` work, because it needs no valid key, no JTAG, and no AT channel.

### 35d. The AMSS side cannot be reached by raw scan (method note)

Tried and failed to reference the `rdevmap.c` log records at `0xd568f8`–
`0xd569c8` in AMSS: absolute dword over the whole file, Thumb `adr`, ARM
`add pc`, ARM `ldr [pc]`, and Thumb-2 `movw`/`movt` pairs. **All zero** — even
the whole-file data-pointer search, while the *string* addresses in the same
records do have data pointers. So the record table is reached through a
load-time-relocated base that is not present in the file.

⛔ **DISPROVED 2026-09-29 by the RAM dump (§36c).** It is *not* a relocated
base: the AMSS RAM is byte-identical to the AMSS image in every segment in
range — zero relocations. The real explanation is that these are log-message
tables from a build with logging compiled out, so the tables are dead data
that no code references. The Ghidra-import plan is unnecessary for this
question, and the log strings are a dead end in principle, not just for my
scanners.

## 36. TripleOxygen 1.1.2 RAM dump — acquired, and it DISPROVED two of my claims (2026-09-29)

Fausto (OpenZeebo / TripleOxygen) had a RAM dump from a 1.1.2 console
published. Got it, verified it, and it was worth more as a **disproof** than as
a source of pointers.

### 36a. What was downloaded

`https://www.tripleoxygen.net/files/devices/zeebo/dump/` →
`~/projects/zeebo-lle/dump/`, extracted with `7z`. Both RAM MD5s match
`ram/1.1.2/md5.txt` exactly:

| file | size | md5 | verified |
|---|---|---|---|
| `ram/1.1.2/0x00000000_0x01ffffff.7z` | 32 MB | `84490c487e2579c1ca6c1440491aecbf` | yes |
| `ram/1.1.2/0x10000000_0x17ffffff.7z` | 128 MB | `b5c747718e9b5dd2c8c1c70f999e3517` | yes |
| `regs/*` (5 files) | 268 KB | — | — |

Extracted timestamps are **2011-07-16**, matching the NAND images dated
2011-07-18 — same era, same device class.

**NAND not downloaded:** `zeebo-lle/nand/md5.txt` already contains exactly the
remote `dump/nand/1.1.2/md5.txt` hashes (`057fd078…`, `4027ffa2…`), so that
dump was already fetched and verified. Note the rendered directory listing
*truncates filenames* (the date column concatenates onto the name) — the real
names are `0xa8600000_34c` and `0xfffef000_fff`, not `…_34c2` / `…_fff2`.

### 36b. The relocation map (APPS)

The RAM slice maps 1:1 onto the ELF paddr space, so byte-comparing RAM against
`1.1.2_APPS.bin` yields the load-time relocations for free. Result:

| segment | paddr | diffs | reloc-looking |
|---|---|---|---|
| `0x1140c000` RWE | data/relro | 5691 | **483** |
| `0x1001c000` RW | | 54 | 20 |
| `0x10000000` RWE | | 359 | 2 |
| `0x1013a000` RE | **the big code/rodata segment** | **0** | 0 |
| all other code segments | | 0 | 0 |

**Every code segment is byte-identical to the file.** The ELF *is* what
executes. Relocations live only in `0x1140c000`+, and 154 of the 483 point
into `0x14300000` — an address range that exists in RAM but is **outside every
ELF segment**, i.e. `.bss`/heap allocated at runtime. Those are the live
objects the static image cannot see.

### 36c. ⛔ Disproof 1: the log-record tables are DEAD DATA

§28e claimed the `dsatparm` log strings are reached through a 20-byte
log-record table indexed by `{line, record_ptr}` pairs in the function's
literal pool. §30a then listed "pointer-to-record tables" as one of the five
real addressing forms on this image, and §35d guessed the tables were reached
via a load-time-relocated base that is absent from the file.

**All three are wrong.** With the relocated RAM in hand:

| target | ptrs in NAND image | ptrs in live RAM |
|---|---|---|
| the *string* `dsatparm_exec_lctusblock_cmd: fs_write success` (`0x108a5b4e`) | 1 (`0x1119fb4`) | 1 |
| the *record table* at `0x1119fb4` | **0** | **0** |
| the *string* `cannot find card0 usb.key` (`0x104f43e5`) | 1 (`0x10c4cdd8`) | 1 |
| that record (`0x10c4cdd8`) | **0** | **0** |
| record `0x102d6b20` (`cannot create usb.key`) | **0** | **0** |

The chain is `string ← record table ← nothing`. The record tables are the
terminus. Same on the modem side: the AMSS `rdevmap.c` record run
`0xd568f8`–`0xd569c8` has **zero** pointers into it anywhere in the 32 MB modem
RAM — while the strings inside those records *do* have their pointers (53 of
them, to `0x143bd00`–`0x143be00`).

This is the signature of **logging compiled out of the release build**: the
message tables and their strings stay in `.rodata`, but the code that would
index them is gone. So:

- The log strings are **not** a path to code. They are dead data with a
  filename and a message, and nothing more.
- §30a's list of addressing forms must drop "pointer-to-record"; what exists is
  pointer-to-record *as a data layout*, with no code side.
- §35d's "load-time-relocated base" is dead — the RAM dump, which was supposed
  to prove it, disproves it. **AMSS RAM is byte-identical to the AMSS image in
  every segment in range: zero relocations, zero diffs.**

That is the fourth and last of these corrections, and the most useful, because
it means the log strings that kept looking like breadcrumbs (§26, §28e, §30a,
§34b) are a dead end *in principle*, not just for my scanner.

### 36d. `usb.key` state, live

The one-shot state struct the check dereferences (`ldr r0,[pc,#0x108]` @
`0x107639dc`) is at paddr `0x1145982c` and is **live and armed**:

```
+00: 0x301  0x1  0x1  0x1388          (0x1388 = 5000, a timeout in ms)
+10: 0x1    0x104f4424  0x10000  0x11459b08
+20: 0x0    0x0  0x2  0xdead
+30: 0xdeaf 0x4  0x0  0x0
```

`0x104f4424` is the string **`/mmc1`** — so `/mmc1/usb.key` is *composed at
runtime* from the device prefix held in the struct, not hardcoded (the literal
`/mmc1/usb.key` in `.rodata` is a template). `0x11459b08` is a **function
pointer table** whose entries include `0x10763931` and `0x10763b91/95` — the
same `fs_hotplug.c` region as the check itself, so the `usb.key` check is a
*method on a mount/device object*, which is what §35a decoded it as.

`check_61u_key`'s cached open results (`g` at `0x1141e4f8`, `g+4` = mcp,
`g+8` = card0) are **both 0/NULL** in the live dump — the check had not run, or
neither key file existed, at dump time.

### 36e. The LCT/AT path never ran on this console

The 67-byte LCT value buffer (§33b) lives at `0x1434d881` — a runtime address
in the `0x14300000` region, present in RAM though outside the ELF. All 67 bytes
are **zero**. Combined with §29c's negative reachability result: the
`+LCTUSBLOCK` write primitive and the `+LCTSN` read path are present in the
image but **inert on this console**. That is consistent evidence for §29d's
"circular" reading, obtained independently of any hardware.

(Content deliberately not read: that buffer is the device's SN/IMEI, which is
out of scope per §28g. Population status is all this needed.)

### 36f. What the dump did *not* settle

The §35c question — whether RDevMap argument 2 = 6 means "port enabled" — is
still open, and this dump does not answer it. The APPS side is now fully
understood (client marshals the tuple, §32c) but the service state lives on
the modem side, and the modem RAM is identical to the AMSS image, so there is
no extra runtime state to read. §35c's hardware test (empty `usb.key` on a
locked 1.1.2) is still the cheapest way to close it.
