# Zeebo 61u.key Crack — Project Plan

## Objective (revised 2026-09-27)

Reverse-engineer the **61u.key generation algorithm** used by TecToy/Qualcomm to unlock the Zeebo diagnostic port, enabling:
- DIAG port activation without JTAG
- ~~Remote unlock via binary SMS~~ — CLOSED (§14: no modem-autonomous path)
- ~~Permanent unlock via zloader bootloader mod~~ — CLOSED (§8: zloader neuters code signing, not DIAG unlock)

Current standings: validation fully decompiled (strcmp mcp-vs-card0 +
fail-open, `re/notes.md` §2d-i/§16); keygen secret is factory-side only.
Remaining bets, in value order: TecToy tool/DB leak, EMAPPLET Memory Copy,
DIAG fuzz, more pairs, garbage-key confirm test.

---

## Background

| Fact | Source | Status 2026-09-27 |
|------|--------|-------------------|
| 61u.key = 14-char alphanumeric (A-Za-z0-9), case-sensitive | TripleOxygen wiki | confirmed |
| Enables DIAG port via SD card at boot (valid until reboot) | TripleOxygen wiki | confirmed, mechanism decompiled |
| Only extractable via JTAG (force Appmgr → enable DIAG → read file) | TripleOxygen wiki | confirmed |
| Generation logic unknown; suspected IMEI-based | Wiki + TecToy insider (Moon Sarito) | open; internal Windows tool lost |
| Public spreadsheet: 10 IMEI→Key pairs (+3 unpaired keys, +2 unpaired IMEIs) | Google Sheet + Telegram | collected |
| Validation = `check_61u_key@0x108d081c`: resolve mcp → resolve card0 → read both → **strcmp** → SUCCESS(0,6) → event gate → AUXSETTINGS+0x54 | Ghidra decomp (`re/decomp_61u_cluster.c`) | VERIFIED (via GBAtemp SebaG20xx lead) |
| Fail-open on missing internal key → explains Hospital key removal | structural, decompiled | VERIFIED |
| Spreadsheet duplicate key for 2 IMEIs | 03labs / Moon Sarito (possible error) | open, structurally moot |
| Batch/lot hypothesis | 03labs | falsified at available granularity |
| Key alphabet non-uniform (uppercase bias); 80-bit uniform value | repo stats (§7) | VERIFIED, cause unknown |
| `61s.dat` = SIM PIN, unrelated | wiki mirror | corrected |
| Layo / Telegram groups — key/pair sources | Moon Sarito | open contact |

---

## Attack Vectors (with verdicts)

### 1. Statistical / Cryptanalytic (DEMOTED — cannot recover a factory secret)
- Batch falsified; HMAC/SHA1/CRC probes: 0 matches; no IMEI correlation.
- Remaining value: constrain generator family (uppercase bias must be
  reproduced); test new pairs if they arrive. (`tools/stats.py`,
  `tools/bruteforce.py`)

### 2. Reverse Engineering Validation (DONE — verdict recorded)
- Was at `~0x10bff2f5` (garbage) / `~0x1078c8d0` (other version); real
  cluster at `0x108d06ee–0x108d0d80`, fully decompiled. No RSA/ECDSA/HMAC —
  plain strcmp(mcp, card0) + fail-open. Keygen NOT in firmware. Closed.

### 3. TecToy Tool Recovery (OPEN, highest payoff, blocked on access)
- Searched locally: openzeebo-repo has only zloader + python tools; no
  Aldebaran manager on disk. Needs leak/contacts/Wayback effort.

### 4. Binary SMS Injection (CLOSED as remote vector)
- Split: BREW-app receiver needs install (= unlock, useless locked);
  modem-autonomous path does not exist (NV store + push routing only).
  AMSS WMS/ONCRPC mapped for the record. (`re/notes.md` §10/§14)

### 5. Unsigned install via EMAPPLET Memory Copy (OPEN, testable w/o key)
- Copy flow decompiled: no signature gate. Needs locked console + SD.
  If reachable without DIAG → arbitrary NAND content. Highest-value
  hardware test alongside garbage-key confirm.

### 6. DIAG fuzz pre-gate + SPC defaults (OPEN, tooling ready)
- `tools/diag_fuzz.py` (framing self-tested); SPC machinery confirmed in
  AMSS; sibling MSM7201A basebands archived (same family). Needs USB +
  locked console.

---

## Repository Structure

```
zeebo-61u.key-crack/
├── PLAN.md                    # This file (phases + verdict log)
├── README.md                  # Status + findings
├── HANDOFF.md                 # Session snapshot
├── 61u.key.bad                # 14xA negative control (hardware test)
├── data/
│   ├── spreadsheet.csv        # 10 pairs (gitignored, Google Sheet export)
│   ├── unpaired_keys.txt      # 3 keys, IMEI unknown (Telegram)
│   └── unpaired_imeis.txt     # 2 IMEIs, key unknown (Telegram)
├── re/
│   ├── notes.md               # RE findings (§1–§17)
│   ├── decomp_61u_cluster.c   # Decompiled validation cluster
│   ├── ghidra_scripts/        # Headless Ghidra scripts
│   ├── thumb_61u_func1.asm    # Old slice (other version; ref only)
│   └── strings_61u_*.txt      # Filtered strings
├── tools/
│   ├── validate.py            # Format check + legacy hypothesis tests
│   ├── stats.py               # Entropy/positional/batch stats
│   ├── bruteforce.py          # HMAC/SHA1/CRC harness
│   ├── hunt_refs.py           # movw/movt encoding scan
│   ├── diag_fuzz.py           # QCDM fuzzer (UNTESTED live)
│   └── gen_61u.py             # Generator STUB (contract only)
├── firmware/                  # Symlinks to NAND images + strings
└── docs/                      # TripleOxygen wiki mirrors
```

---

## Phase 1: Data Collection & Setup (DONE 2026-09-27)

### 1.1 Spreadsheet Data (done)
- [x] Exported to `data/spreadsheet.csv` (10 pairs; sheet holds no more)
- [x] Format verified: 14 chars, alnum, case-sensitive
- [x] Duplicates checked: 1 duplicate key (2 IMEIs), 0 duplicate IMEIs
- [x] 9 unique keys / 10 pairs; grouped by key, batch patterns tested
- [x] +3 unpaired keys +2 unpaired IMEIs archived (Telegram)

### 1.2 Firmware Extraction (done)
- [x] APPS/AMSS symlinked from `~/projects/zeebo-lle/nand/`; strings extracted
- [x] 61u.key/61s.dat/IMEI refs catalogued; `61s.dat` corrected to SIM PIN
- [x] EFS2 + EFS2APPS + modem-EFS2 extracted/listed via zeebx `nand.py`

### 1.3 Ghidra Project Setup (done)
- [x] `re/ghidra/Zeebo61u` (gitignored, 673MB+): APPS (ELF, ARMv8 LE,
  auto-analysis) + AMSS + APPSBL + QCSBL + Dream radio.img (raw, unanalyzed)
- [x] Validation cluster found via literal-pool-cell refs; old addresses
  (`0x1078c8d0`, `0x10bff2f5`) retired (other version / garbage)
- [x] Scripts in `re/ghidra_scripts/`, decomp in `re/decomp_61u_cluster.c`

---

## Phase 2: Validation Logic RE (Week 1-2)

### 2.0 Constraints (established 2026-09-27, read before touching Ghidra)
- ELF has **program headers only, no sections, no .debug/.symtab** — no free
  function names. All function discovery is by code-pattern hunting.
- `thumb_61u_func1.asm` (~0x1078c8d0) has **0 byte-hits** in 1.1.2 — other
  version/slice. Structural reference only.
- Key strings have **zero absolute-pointer refs** in the file — addresses are
  materialized split (`movw/movt`) or via struct offsets.
- `61s.dat` = SIM PIN (wiki). NOT validation data — do not chase it.

### 2.1 movw/movt hunt (capstone, ~15 min) — DO FIRST
- New script `tools/hunt_refs.py`: disassemble exec LOAD segs (Thumb-2 + ARM),
  collect `movw/movt/adr/ldr-literal` immediates, flag values equal to string
  vaddrs (`0x108d08a4 0x108d08b4 0x10aff2e4 0x10aff29c 0x11267a40`) or within
  ±4KB (table bases).
- Success = code vaddrs → decompile each in Ghidra (`DecompileAt` pattern in
  `re/ghidra_scripts/`) → validation function found → go to 2.4.
- Failure → go to 2.2.

### 2.2 Anchor from the far end (~30 min)
- Validation ENDS in AUXSETTINGS DIAG enable. Hunt refs to `AUXSETTINGS`,
  `SIO Configuration`, `Port Map` strings (same hunt script, more targets).
- In Ghidra: list callers of `IFILEMGR_OpenFile`/`IFILE_Read` imports
  (imports have xrefs by construction), intersect with functions near
  `OEM_LCTSystemCtl.c` debug string (`0x10e9fc4a`).
- Success = candidate function(s) → go to 2.4. Failure → go to 2.3.

### 2.3 Falsify-per-location sweep (~30 min, last RE resort)
- Ghidra script: iterate all functions, flag those containing BOTH a file-API
  call AND a reference into the `0x108d0800–0x108d0900` / `0x10aff200–0x10aff300`
  data windows (any ref type: literal, movw/movt, pc-rel).
- If still nothing: accept that 1.1.2's check may be a different function
  shape (inlined into boot, table-driven) → go to 2.4 with best candidates.

### 2.4 THE DECISION POINT (this is the whole point of Phase 2)
In the candidate function, answer ONE question: **does any instruction compare
key bytes against console data (IMEI/serial/NV)?**
- Look for: byte-compare loops over a 14-byte buffer, `memcmp`-like calls,
  reads of IMEI/ESN NV items in the same function.
- **If NO compare exists → validation is presence+format-only.** The keygen
  secret lives ONLY in the TecToy tool. STOP all RE, pivot 100% to Phase 4
  (tool hunt) + data collection. This is the expected outcome (evidence:
  1.1.1 `usb.key` = empty file works; duplicate keys across IMEIs).
- **If a compare exists →** document the compared source (IMEI? serial?
  provisioned blob?) → that source becomes the hypothesis input for Phase 3.

### 2.5 Old items (kept)
- [x] `tools/validate.py` reimplements format check
- [ ] Confirm on hardware: does ANY 14-char alnum key enable DIAG? (needs
  locked console + SD card — cheapest decisive experiment in the project)

### 2.6 Key Observations from Strings (corrected)
```
fs:/mcp/61u.key          → checked first (internal NAND)
fs:/card0/61u.key        → checked second (SD card)
lctsys/61s.dat           → SIM PIN, unrelated to key check (wiki)
OEM_LCTSystemCtl.c       → source file, debug string @ 0x10e9fc4a
AEECLSID_AUXSETTINGS …   → DIAG enable path (far-end anchor for 2.2)
```

---

## Phase 3: Cryptanalytic Attack (Week 2-4)

### 3.1 Hypothesis Testing Framework
`tools/bruteforce.py` — modular test harness:
```python
def test_hypothesis(imei: str, key: str, hypothesis_fn) -> bool:
    return hypothesis_fn(imei) == key
```

### 3.2 Hypotheses to Test (Priority Order)

| # | Hypothesis | Description | Test |
|---|------------|-------------|------|
| 1 | **Production batch/lot ID based** (NOT IMEI) | 03labs found duplicate keys for different IMEIs; key may derive from manufacturing batch | Group IMEIs by key, check for sequential IMEI ranges, date codes |
| 2 | `HMAC-SHA1(IMEI, secret)[:14]` | Standard Qualcomm provisioning | Need secret; try known Qualcomm keys |
| 3 | `AES-ECB(IMEI, key)[:14]` | Symmetric encryption | Need key; try all-zero, all-FF, IMEI-derived |
| 4 | `SHA1(IMEI + salt)[:14]` | Simple hash + salt | Brute salt if short (< 4 bytes) |
| 5 | `CRC32(IMEI) + IMEI` encoded | Checksum + data | Test base64/base32/alphanum encoding |
| 6 | `PRF(IMEI, carrier_secret)` | Carrier-specific | Test Claro/TecToy known secrets |
| 7 | Custom LFSR/PRNG seeded with IMEI | Qualcomm proprietary | RE validation for clues |
| 8 | **Key derived from NV item / EFS2 provisioning data** | Modem stores provisioning info in NV/EFS | Check AMSS for NV_IMEI, NV_ESN, provisioning NV items |

### 3.3 Statistical Analysis (`tools/stats.py`)
- [ ] Character frequency analysis (per position)
- [ ] IMEI→Key correlation (bit-level)
- [ ] Entropy measurement
- [ ] Check for: fixed prefixes, position-dependent mappings
- [ ] **Group by key → analyze IMEI ranges, check for batch clustering**
- [ ] **Check if duplicate-key IMEIs share prefix/range (manufacturing batch)**

### 3.4 Qualcomm Prior Art
- Research: `qmi-go` WMS, `libqmi`, BitPim (CDMA phone management)
- Check: How do other Qualcomm devices (LG VX9200, etc.) generate unlock codes?
- Search: "Qualcomm 61u.key", "Qualcomm diag unlock code generation", "Qualcomm batch unlock code"

---

## Phase 4: TecToy Tool Hunt (Parallel)

### 4.1 Search Locations
- [ ] `~/projects/zeebo/research/openzeebo-repo/vendor/tripleoxygen/`
- [ ] `~/projects/zeebx-emu/vendor/` (SDK tools)
- [ ] TripleOxygen file vault: `https://www.tripleoxygen.net/files/devices/zeebo/`
- [ ] Wayback Machine: `openzeebo.org`, `openzeebo.forumeiros.com`

### 4.2 If Found
- [ ] .NET → decompile with dnSpy/ILSpy
- [ ] Native → Ghidra
- [ ] Extract algorithm + secret

---

## Phase 5: Binary SMS Injection (Post-Crack)

### 5.1 Prerequisites
- [ ] Guilherme's modem SMS send/receive working
- [ ] QMI/WMS (service 0x12) implemented in zeebx-emu or standalone
- [ ] ARM9→ARM11 RPC mapping for "write 61u.key to EFS2"

### 5.2 ARM9 ↔ ARM11 Communication (Critical for SMS→Filesystem Path)
- **Interface**: ONCRPC over SMD (Shared Memory Driver) — not UART
- **Channels**: SMD provides multiple logical channels over shared memory
- **No signal tap needed** — SMD is memory-mapped, can be monitored via JTAG or emulator
- **DMA**: SMD uses shared memory buffers, not traditional DMA between chips
- **RPC services**: Modem (ARM9/AMSS) exports RPC services; Apps (ARM11/BREW) calls them
- **Key insight**: Binary SMS arrives at WMS on ARM9 → WMS handler can call RPC to ARM11 to write file

### 5.3 Attack Flow
```
Attacker → Binary SMS (WMS PDU) → Zeebo Modem (ARM9/AMSS)
    → WMS handler → ONCRPC/SMD → ARM11 (BREW)
    → RPC handler writes 61u.key to /fs/mcp/61u.key or /fs/card0/61u.key
    → DIAG port enabled on next boot (or immediately via AUXSETTINGS RPC)
```

### 5.4 Permanent Unlock
- Flash `zloader_sig_p.bin` (homebrew mod bootloader) via DIAG
- Removes 61u.key requirement permanently (DIAG always on)

---

## Success Criteria

| Milestone | Definition |
|-----------|------------|
| **Data Ready** | ≥30 IMEI→Key pairs in CSV, validated format |
| **Validation RE'd** | Full pseudocode of 61u.key check in `re/notes.md` |
| **Algorithm Cracked** | `generate_key(imei) == key` for all known pairs |
| **Tool Built** | `tools/gen_61u.py <imei>` outputs valid key |
| **SMS Demo** | Binary SMS sent → DIAG enabled on target console |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Algorithm uses HSM/secret not in firmware | Focus on finding TecToy tool; statistical attack on pairs |
| Validation uses RSA verify (public key in firmware) | RE validation — if pubkey found, need private key (impossible) → look for signing oracle |
| Spreadsheet has <10 pairs | Request more from TripleOxygen community; use JTAG on own consoles |
| Binary SMS path blocked by modem firmware | Test with Guilherme's setup; may need AMSS patch |

---

## Resources

- **TripleOxygen Wiki**: `https://www.tripleoxygen.net/wiki/console/zeebo/61u.key`
- **Spreadsheet**: `https://docs.google.com/spreadsheets/d/1Rd9UGbUBCqipReINDDyM0gFQITxU_hE3l5IxNtlvLV8`
- **OpenZeebo Repo**: `~/projects/zeebo/research/openzeebo-repo/`
- **NAND Images**: `~/projects/zeebo-lle/nand/1.1.2_APPS.bin`, `1.1.2_AMSS.bin`
- **zeebx-emu** (for QMI/WMS): `~/projects/zeebx-emu/`
- **Aldebaran Manager**: Z-Wheel gerenciador (C#) — check for keygen code

---

## Log

| Date | Action |
|------|--------|
| 2026-09-26 | Project created, PLAN.md written, git initialized |
| 2026-09-26 | Added spreadsheet (10 pairs). **Duplicate key `3ulp223EpFKhDT` for IMEIs `355800020098020` & `355800020084657` sharing IMEI prefix `35580002` and serial batch `BQAAF0150B215810` (16 chars)** — but 3 other consoles in same sub-batch `24` have different keys. Pattern suggests factory provisioning data, not simple batch mapping. |
| 2026-09-27 | Split tools: `stats.py` (entropy/positional/batch-falsification), `bruteforce.py` (hmac/sha1/crc harness, --input imei\|serial), `gen_61u.py` (stub, refuses to guess). Wrote `re/notes.md`. Batch hypothesis falsified at 2-char unit granularity (24->4 keys, 18->2 keys). HMAC-SHA1/SHA1-salt: 0 matches. `thumb_61u_validation.asm` (0x10bff2f5) identified as misaligned garbage. EFS2: 18x `61s.dat` dirents all ref 0x1bff8 -> page table 0xffffffff (deleted). SD-card `debug_nand/_efs2_recovered` checked: lctsys node w/o children, mcp/card0 empty. Wiki mirrors archived in docs/; 61s.dat corrected to SIM PIN; Hospital removes key on unlock (scarcity explained). |
| 2026-09-27 | **2.4 VERDICT: validation decompiled, NO content check.** Ghidra Hunt61u.java (instruction-ref windows) found the cluster via literal-pool cells (refs point at cells, not strings — that was the xref mystery). Validation fn `FUN_108d08d0` + helpers (`06ee/07a0/0a96/0c10/0d44`) in `re/decomp_61u_cluster.c`: open/read/event-gate(0x97/0x10a)/AUXSETTINGS+0x54. No memcmp, no IMEI/serial read, no length/charset check. **Secret is TecToy-side only. RE stops; pivot to Phase 4 + data.** Telegram: 3 unpaired keys + 2 unpaired IMEIs (Michael Marostega: unlocked 355800020047357, locked 355800020109017); locked owner's key is JTAG-only. |
| 2026-09-27 | **ARM11-only confirmed (2e).** Cluster callees = BREW dispatcher + apps-heap + vtable calls; oncrpc/smd/modem strings referenced only from modem-client code (e.g. FUN_101a849a), never from 0x108d0xxx cluster. Validation never leaves ARM11. `61u.key.bad` (14xA) generated for Layo hardware test. || 2026-09-27 | **CORRECTION via GBAtemp (SebaG20xx post #9): content IS compared.** Missed gap fns `0x108d07c0-0x108d087a` (Ghidra never created them; forced-Thumb via `DumpThumb.java`): `check_61u_key@081c` = resolve mcp → resolve card0 → read both → **strcmp(mcp, card0)** → SUCCESS(0,6). **Fail-open if internal key missing → explains Hospital key-removal.** Garbage-key test prediction FLIPPED (FAIL = confirms strcmp). Timing side-channel real but impractical. Keygen still TecToy-side. Sibling basebands (Dream/Sapphire/RC33 radios): same SPC family, peripheral DIAG diffs only. |
| 2026-09-27 | Ex-dev emails (Moon): external online provisioning, NV-changeable IMEI, "lookup file". Archived `docs/ex_dev_emails_2026-09-27.md`. Kills e-fuse theories input-side too. |
| 2026-09-27 | Stress test: resolve=`OEMFS_Test`, polarity confirmed; EDL ranked top cheap probe. JNE-crack bytes: P1 `04d1→00bf` at file `0x80c864` (`re/notes.md` §18). |
| 2026-09-27 | Text Script: factory auto-copy struct (`autocopysdcardinfotoenand.dat` + /mif + /mod) confirmed in firmware; wiki resolves it as empty-trigger, DIAG-gated, sig-at-run-time. EMAPPLET copy flow: no sig gate. |
| 2026-09-27 | Audits: 50-technique sweep (§21); exploit audit — unbounded strcat candidate, no SSP/ASLR/NX (ROP overkill); no remote flash path (§22); sibling HTC radios archived (same SPC family). |
| 2026-09-27 | Docs overhaul (README/PLAN/HANDOFF rewritten to verdicts). History slimmed: 766M→2.6M (dropped committed NAND extracts). Attack map now 18 vectors (§16). |
