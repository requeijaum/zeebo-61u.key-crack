# Zeebo 61u.key Crack — Project Plan

## Objective
Reverse-engineer the **61u.key generation algorithm** used by TecToy/Qualcomm to unlock the Zeebo diagnostic port, enabling:
- DIAG port activation without JTAG
- Remote unlock via binary SMS (modem → ARM9 → ARM11 RPC)
- Permanent unlock via zloader bootloader mod

---

## Background

| Fact | Source |
|------|--------|
| 61u.key = 14-char alphanumeric (A-Za-z0-9), case-sensitive | TripleOxygen wiki |
| Enables DIAG port via SD card at boot (valid until reboot) | TripleOxygen wiki |
| Only extractable via JTAG (force Appmgr → enable DIAG → read file) | TripleOxygen wiki |
| Generation logic unknown; suspected IMEI-based | Wiki: "pode ser totalmente aleatória ou obedecer algum padrão baseado em dados do console, como o IMEI" |
| TecToy had internal tool: input IMEI → output 61u.key | Moon Sarito (Discord) |
| Public spreadsheet: ~57 IMEI→Key pairs collected | `docs.google.com/spreadsheets/d/1Rd9UGbUBCqipReINDDyM0gFQITxU_hE3l5IxNtlvLV8` |
| Validation logic lives in `OEM_LCTSystemCtl.c` (Longcheer system applet) | APPS.bin strings + RE |
| **CRITICAL: Spreadsheet has duplicate keys for different IMEIs** | Guilherme Ricardo (03labs): "tem mais de 1 IMEI por 61u.key... descartaram que tenha a ver com IMEI e estavam apostando em algo relacionado com lote de produção" |
| **Data quality issue**: Moon Sarito suspects the duplicate may be an error in the spreadsheet | Moon Sarito: "real me parece ter sido um erro acidental mesmo" |
| **Key may be production batch/lot based, NOT IMEI-based** | 03labs analysis |
| **Layo** has unlocked many Zeebos — potential data source | Moon Sarito |

---

## Attack Vectors

### 1. Statistical / Cryptanalytic (Primary)
- Obtain spreadsheet data (IMEI → Key pairs)
- **FIRST: Verify data quality** — check for duplicate IMEIs, duplicate keys, malformed entries
- **Test batch/lot hypothesis** — group by key, check if IMEIs in same batch share key
- Test hypotheses:
  - HMAC-SHA1(IMEI, secret) truncated to 14 chars
  - AES-ECB(IMEI, key) truncated
  - Custom PRF: `SHA1(IMEI || salt)[:14]` mapped to alphanumeric
  - CRC/checksum + IMEI encoding
  - **Production batch ID / lot number based** (not IMEI)
- If algorithm is in TecToy tool (not console), need the secret key

### 2. Reverse Engineering Validation (Secondary)
- Fully RE the Thumb function in APPS.bin at `~0x10bff2f5` (validates 61u.key)
- Understand exact constraints: length, charset, checksum, any crypto verification
- May reveal if validation uses a public key (RSA/ECDSA verify) vs symmetric

### 3. TecToy Tool Recovery (Tertiary)
- Search for leaked internal tools in:
  - `vendor/tripleoxygen/` (openzeebo repo)
  - Aldebaran manager (`z-wheel_gerenciador_1.0.0.0.zip` — C#, decompilable)
  - Any Qualcomm BREW SDK tools for Zeebo
- If found, decompile (dnSpy/ILSpy for .NET, Ghidra for native)

### 4. Binary SMS Injection (Operational)
- If key algorithm cracked: craft binary SMS (WMS PDU) → modem (ARM9/AMSS)
- Modem RPCs to ARM11 (ONCRPC/SMD) → writes 61u.key to EFS2 → DIAG enabled
- Requires: working QMI/WMS on modem (Guilherme's work), valid IMEI

---

## Repository Structure

```
zeebo-61u.key-crack/
├── PLAN.md                    # This file
├── README.md                  # Quick start
├── data/
│   ├── spreadsheet.csv        # IMEI,Key pairs (from Google Sheets export)
│   ├── imeis.txt              # Just IMEIs for testing
│   └── keys.txt               # Just keys for analysis
├── re/
│   ├── ghidra/                # Ghidra project files
│   ├── notes.md               # RE findings
│   ├── validation_func.asm    # Disassembly of 61u.key check
│   └── strings_61u.txt        # Relevant strings from APPS/AMSS
├── tools/
│   ├── validate.py            # Reimplements validation logic
│   ├── bruteforce.py          # Hypothesis testing
│   ├── stats.py               # Statistical analysis of pairs
│   └── qmi_sms.py             # QMI/WMS binary SMS sender (later)
├── firmware/
│   ├── 1.1.2_APPS.bin         # Copy from zeebo-lle/nand/
│   ├── 1.1.2_AMSS.bin         # Modem firmware
│   └── extracted/             # Binwalk/extracted partitions
└── docs/
    ├── tripleoxygen_wiki_61u.md
    ├── modem_qmi_wms.md
    └── references.md
```

---

## Phase 1: Data Collection & Setup (Week 1)

### 1.1 Get Spreadsheet Data
- [ ] Export Google Sheet to CSV → `data/spreadsheet.csv`
- [ ] Parse: columns = IMEI, Key, Console Version, Region, Notes
- [ ] Verify: 14 chars, alphanumeric, case-sensitive
- [ ] **CRITICAL: Check for duplicate IMEIs, duplicate keys, malformed entries**
- [ ] **Count unique IMEIs vs unique keys (collisions = batch hypothesis support)**
- [ ] **Group by key → list IMEIs sharing same key → check for production batch patterns**

### 1.2 Firmware Extraction
- [ ] Copy `1.1.2_APPS.bin`, `1.1.2_AMSS.bin` from `~/projects/zeebo-lle/nand/`
- [ ] Extract strings: `strings -a 1.1.2_APPS.bin > firmware/strings_apps.txt`
- [ ] Extract strings from AMSS: `strings -a 1.1.2_AMSS.bin > firmware/strings_amss.txt`
- [ ] Search for 61u.key, 61s.dat, IMEI, validation refs, **batch/lot identifiers**

### 1.3 Ghidra Project Setup
- [ ] Create Ghidra project for APPS.bin (ARM 32-bit LE, base 0x10000000)
- [ ] Load APPS.bin with program headers (see `readelf -l`)
- [ ] Find validation function: search for "61u.key" string → xrefs
- [ ] Disassemble Thumb function at `~0x1078c8d0` (first ref) and `~0x10bff2f5` (second ref)
- [ ] Document in `re/validation_func.asm`

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