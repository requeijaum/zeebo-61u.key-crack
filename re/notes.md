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
  (presence-only proof), EMAPPLET Memory Copy (unsigned install?), DIAG
  fuzz pre-gate, JTAG (certain, invasive).

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
| D2 | EDL 9008 / secure-boot fuse state | hardware | UNKNOWN (Seba #7's question) |
| E1 | TecToy tool/DB leak | luck/contacts | OPEN, highest payoff |
| E2 | More pairs (Layo/group) | people | OPEN |
| E3 | Duplicate `3ulp223` resolution | 03labs/Moon | OPEN (error vs reuse changes nothing structurally now) |
| F1 | SMS remote injection | — | CLOSED (§14: no modem-autonomous path) |

## 17. Boot chain: APPSBL/QCSBL/OEMSBL + auth entry (2026-09-27)

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
