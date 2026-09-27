# Zeebo 61u.key Crack - Handoff to OpenCode

## Project Status: Active
**Location**: `/home/rafaelfrequiao/projects/zeebo-61u.key-crack`
**Git**: Local repo initialized, 2 commits (clean working tree)

## What's Done

### 1. Data Collection (Item 1 ✓)
- Spreadsheet imported: `data/spreadsheet.csv` (10 pairs from 57+ in full sheet)
- Key finding: **Duplicate key `3ulp223EpFKhDT` for two BR consoles** sharing IMEI prefix `35580002` and serial batch `BQAAF0150B215810`
- Analysis tool: `python tools/validate.py batch data/spreadsheet.csv`
- **Hypothesis**: Key is manufacturing batch/lot based, NOT IMEI-based (confirmed by 03labs)

### 2. NAND Extraction (Item 2 ✓)
- **Existing extractor found**: `zeebx-emu/ferramentas/nand.py` (zeebx-emu has EFS2 parser)
- Partitions mapped: MIBIB, QCSBL, OEMSBL1/2, AMSS, APPSBL, FOTA, EFS2, APPS, FTL, EFS2APPS
- EFS2APPS extracted to `firmware/part_EFS2APPS.bin` (81MB, .gitignored)
- **317 distinct filenames** catalogued
- `lctsys/` directory found (ref 0x401), contains `61s.dat` (ref 0x1bff8)

### 3. TecToy Tool (Item 3 ✗)
- **ABORTED** - user doesn't have the internal TecToy keygen binary

### 4. 61s.dat File (Item 4 ✓)
- **Located** in EFS2APPS at directory entry ref 0x1bff8
- Page table lookup returns `0xffffffff` (deleted/old generation - EFS2 is log-structured)
- Need to find current generation of page table to read actual content
- Wiki says it contains a 4-digit PIN

## Key Technical Findings

| Finding | Evidence |
|---------|----------|
| Key = 14-char alphanumeric | TripleOxygen wiki + validation code |
| Validation in `OEM_LCTSystemCtl.c` | APPS.bin offset 0x80c8ac, function ~0x1078c8d0 (Thumb) |
| Checks `/mcp/61u.key` → `/card0/61u.key` | String refs in validation function |
| Reads `lctsys/61s.dat` | String ref in same function |
| Enables DIAG USB SER1 via AUXSETTINGS | Validation function logic |
| Valid until reboot only | Wiki + code analysis |
| ARM9 (modem) + ARM11 (BREW) | MSM7201A dual-core |
| SMS → QMI WMS (svc 0x12) → RPC → ARM11 | Architecture analysis |

## Next Steps

1. **Get full 57+ entry spreadsheet** from TripleOxygen Google Sheet
2. **Find current EFS2 page table generation** to read `61s.dat` content
3. **Ghidra RE** on APPS.bin (base 0x10000000) for validation function at 0x1078c8d0
   - User has prior Ghidra projects for DKWDRV/Zeebulator/Curupira/Zeebo-LLE - locate them
4. **Test batch hypothesis** with more data: cluster IMEIs by TAC/FAC/serial prefix per key

## Project Structure
```
zeebo-61u.key-crack/
├── PLAN.md              # 241 lines, 4 phases, updated with findings
├── README.md            # 89 lines
├── HANDOFF.md           # This file
├── .gitignore
├── data/
│   └── spreadsheet.csv  # 10 pairs (git tracked)
├── re/
│   ├── strings_61u_1.1.2_APPS.txt      # 1245 lines filtered
│   ├── strings_61u_1.1.2_AMSS.txt      # 775 lines filtered
│   ├── thumb_61u_func1.asm             # Disassembly
│   └── thumb_61u_validation.asm        # ~160KB
├── tools/
│   └── validate.py      # 237 lines: batch/test/analyze/hypothesis_* commands
└── firmware/            # Symlinks only (no copies)
    ├── 1.1.2.bin -> ~/projects/zeebo-lle/nand/1.1.2.bin
    ├── 1.1.2_APPS.bin -> ~/projects/zeebo-lle/nand/1.1.2_APPS.bin
    └── 1.1.2_AMSS.bin -> ~/projects/zeebo-lle/nand/1.1.2_AMSS.bin
```

## Commands to Resume
```bash
cd /home/rafaelfrequiao/projects/zeebo-61u.key-crack

# Analyze spreadsheet for batch patterns
python tools/validate.py batch data/spreadsheet.csv

# Test hypotheses (now tests batch first)
python tools/validate.py test data/spreadsheet.csv

# Extract EFS2APPS again if needed (regeneratable)
python3 ~/projects/zeebx-emu/ferramentas/nand.py extrair ~/projects/zeebo-lle/nand/1.1.2.bin EFS2APPS firmware/part_EFS2APPS.bin

# List EFS2APPS files
python3 ~/projects/zeebx-emu/ferramentas/nand.py nomes firmware/part_EFS2APPS.bin
```

## Memory Notes Saved
- Zeebo RE: Ghidra projects for DKWDRV/Zeebulator/Curupira/Zeebo-LLE exist - need to locate
- 61u.key validation at `OEM_LCTSystemCtl.c` (APPS.bin 0x1078c8d0)
- lctsys/61s.dat reference in validation logic
- NAND extraction via zeebx-emu/ferramentas/nand.py