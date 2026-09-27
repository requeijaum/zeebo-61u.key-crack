# Handoff snapshot — 2026-09-27 (evening)

Living docs: `README.md` (status), `PLAN.md` (phases + verdict log),
`re/notes.md` (§1–§25, full RE record). This file is a pointer, not a copy.

## Settled (do not re-investigate without new evidence)

- Validation = `check_61u_key@0x108d081c`: resolve mcp → resolve card0 →
  read both → **strcmp(mcp, card0)** → SUCCESS(0,6) → event gate →
  AUXSETTINGS+0x54. ARM11-only. Keygen secret factory-side only.
- Fail-open on missing internal key (= Hospital key removal → perm DIAG).
- `61s.dat` = SIM PIN. zloader/Z-Wheel/modem-EFS/SMS-remote/presence-only/
  overflow = closed. Sibling MSM7201A radios = same SPC family.
- JNE-crack bytes: P1 `04d1→00bf` at file `0x80c864` (§18; needs NAND write).
- Text Script = factory auto-copy (empty `.dat` trigger, DIAG-gated,
  sig-at-run-time). EMAPPLET copy flow has no sig gate.
- FAT/LFN: HCC lib + CVE-2026-6688 pattern; strcpy shape PROVEN executable
  under Unicorn (`tools/prove_overflow.py`); trigger (long name → param_2)
  open. Evil-SD generator committed UNTESTED (`tools/make_evil_sd.py`).
- Ex-dev emails archived (`docs/`): external provisioning, NV IMEI.
- Data: 10 pairs + 3 unpaired keys + 2 unpaired IMEIs. Batch falsified.
  Alphabet bias (uppercase) confirmed, cause unknown.

## Open (blocked on people or hardware)

1. Garbage-key confirm test (`61u.key.bad`, predicts FAIL) — Layo/OLX console
2. EMAPPLET Memory Copy / Text Script auto-copy gating — same consoles
3. Evil-SD LFN crash test (needs operator-run elsewhere) — same consoles
4. DIAG fuzz pre-gate + SPC defaults (`tools/diag_fuzz.py` ready) — USB + locked
5. EDL 9008 probe (top payoff if unfused) — USB cable + edl client
6. Pairing Telegram keys×IMEIs; duplicate-key resolution — group answers
7. TecToy tool/DB leak — contacts/luck
8. Timing oracle, secure-boot fuse RE — impractical / separate project

## Resume commands

```bash
cd /home/rafaelfrequiao/projects/zeebo-61u.key-crack
git log --oneline -5 && git status --short
python tools/stats.py data/spreadsheet.csv --serials
python tools/bruteforce.py data/spreadsheet.csv
python tools/diag_fuzz.py --dry-run
# Ghidra (673MB project, gitignored): re/ghidra/Zeebo61u
```

## Memory pointers (other agents/hosts)

- Hermes `MEMORY.md`: Ghidra location + `0x1078c8d0` ref — STALE
  (correct: cluster `0x108d06ee–0x108d0d80`, this repo `re/notes.md` §2d-i).
- Prime agent sessions: emulator work only, nothing on 61u.key.
