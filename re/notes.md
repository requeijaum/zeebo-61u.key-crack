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
  CONFIRMED: Test→0 (exists) continues to card0; nonzero (missing) →
  fail-open SUCCESS. Call chain verified to import-stub level
  (`bl`→ARM veneer `109834c8`→wrapper `11155860`→PLT-like `11133a60`).
  `result_setter@1079e4a0` = import thunk (semantics structural:
  match/missing → `(0,6,ptr)`, all other fails → `(0,0,ptr)`).

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
`strcmp(mcp,card0)` → SUCCESS(0,6) → event gate → AUXSETTINGS+0x54.
Fail-open iff mcp unresolvable.

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
  ignored, always falls into SUCCESS(0,6). No semantic assumptions.
- P2 (1 byte, relies on (0,6)=success): `0x108d0870` `movs r1,#0`
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
{ char name[16]; u32 flags_a; u32 flags_b; u32 param_tbl; u32 param_tbl2;
  u32 fn_ptr /* Thumb, bit0 set */; u32 fn_ptr2; }
```

It is a stock **ATCOP/DSAT** command table — the LCT commands sit next to
`+FCLASS +ICF +IFC +IPR +CIMI +CGMR +GMI +GMM +GMR +GCAP +GSN +WS46 +DS +DR`.
So the AT processor lives in the **APPS image (ARM11)**, not the modem.

Extracted handlers (record scan; the five marked ✓ were disassembled and
confirmed instruction-by-instruction):

| Command | handler | | Command | handler |
|---|---|---|---|---|
| `+LCTUSBLOCK` | `0x10aff100` ✓ | | `+LCTSN` | `0x10aff360` ✓ |
| `+LCTSW` | `0x10aff33c` | | `+TESTINF2` | `0x10aff3f4` |
| `+STORENEWPIN` | `0x10afef80` ✓ | | `+WRITEIMSIFILE` | `0x10afed2e` ✓ |
| `+DELETEIMSIFILE` | `0x10afee54` ✓ | | `+UIT` | `0x10afeca4` |
| `+LCTUSBDISABLE` | `0x103611ee` | | `+LCTACTIVESIM` | `0x1036125c` |
| `+LCTSTOPTHESIM` | `0x1036128a` | | | |

The `0x10b96bXX` / `0x10b96efX` targets are **PLT slots** — ARM-mode
`ldr pc,[pc,#-4]` + inline offset (24 slots in `0x10b96b40`–`0x10b96c00`),
each loading an address relative to PC+8. Resolved targets:

| Call site | → resolved | used for |
|---|---|---|
| `0x10b96b98` | `0x10333d25` | fs nametest / status |
| `0x10b96bb8` | `0x10333b5f` | (error-path variant) |
| `0x10b96b40` | `0x10333693` | fs open |
| **`0x10b96b70`** | **`0x10333789`** | **fs write** (Moon's address, exact) |
| `0x10b96b50` | `0x103336fb` | fs close |
| `0x10b965a8` | `0x1079c04d` | strlen |
| `0x10b96edc` | `0x1079bcc1` | sprintf |
| `0x10b96ef4` | `0x10360f83` | SN read (mode 5) |
| `0x10b96efc` | `0x10360853` | IMEI read (mode 7) |
| `0x10b96f04` | `0x10360ffd` | SN write |
| `0x10b96f0c` | `0x1036113d` | IMEI write |

Same shape as §27's shared-import dispatch (`0x109834cc → 0x11155860` →
`0x11133a60` stubs): ordinary PLT indirection into the RPC/import region
around `0x1033xxxx`, nothing exotic. Note these are *PLT* slots, not the
long-branch veneers an initial Thumb-only scan suggested — that scan was
misdecoding the ARM half (exactly the caveat `tools/hunt_refs.py` documents).

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
  0x10b96b70(fd, buf, strlen(buf), 0, &resp)   // ← the write (PLT → 0x10333789)
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

The code never loads a string address — it loads a *record* address and
indexes. So `getReferencesTo()` and the `movw/movt` scan in §2b were
structurally blind to it. Any future ref hunt must also scan for
**pointer-to-record** patterns and inline data inside literal pools. Same
lesson as §27's "absence of refs can mean undecoded regions".

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
