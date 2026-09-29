# Handoff snapshot — 2026-09-27 (evening)

Living docs: `README.md` (status), `PLAN.md` (phases + verdict log),
`re/notes.md` (§1–§25, full RE record). This file is a pointer, not a copy.

## Settled (do not re-investigate without new evidence)

- Validation = `check_61u_key@0x108d081c`: resolve mcp → resolve card0 →
  read both → **strcmp(mcp, card0)** → **RDevMap RPC**. ARM11-only.
  Keygen secret factory-side only. strcmp confirmed at instruction level
  (§30c). Both files must be present.
- **"SUCCESS(0,6) → event gate" is RETIRED (§32c).** That tuple came from an
  external decompilation and was never verified. The callee is
  `rdevmap_clnt.c` (RDevMap = Qualcomm's port-mapping RPC — the same service
  the wiki's AUXSETTINGS "Port Map > Diag" path drives, §32b) and it never
  branches on `r1` locally, and `r0` is 0 on all three call paths. But `r1`
  is *not* dead: it is RDevMap RPC argument 2 (§32c corrected by §33a). So
  0 vs 6 is payload for the service, not a local gate. **Do not restate it
  as a local success code.**
- **Fail-open CONFIRMED at instruction level (§30e)**: unresolvable
  `mcp/61u.key` → resolve helper returns `0x103` → same early branch as a
  matching pair. Only "opened but NULL" and "strcmp mismatch" take the other
  path. Explains the Hospital key-removal. Note the strcmp is a *narrow*
  path (§31c): a present internal key with a nonzero resolve-status byte
  never reaches the comparison.
- **Top open static item (§32d)**: where the decision is actually made.
  It is inside the RDevMap RPC (possibly a different process — the
  `rdevmap_null:` strings are client-side null-RPC stubs).
- `61s.dat` = SIM PIN. zloader/Z-Wheel/modem-EFS/SMS-remote/presence-only/
  overflow = closed. Sibling MSM7201A radios = same SPC family.
- **Superseded**: "nothing in firmware writes `61u.key`" — `+LCTUSBLOCK`
  writes it (§28). Keygen is still factory-side; the *write* is in the image.
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

0. **`+LCTUSBLOCK` partition + reachability** (2026-09-29, §28 — TOP
   priority, supersedes item 1): `AT+LCTUSBLOCK="<content>"` writes
   `/61u.key` verbatim. Relative path ⇒ likely `fs:/mcp/61u.key`. If the AT
   channel works without DIAG, writing a chosen value to NAND + the same on
   SD defeats the `strcmp` — no keygen needed. Blocked on: which port
   carries the ATCOP parser, and confirming mcp vs card0.
1. **Empty `usb.key` on the SD root** (cheap, §30f): the 1.1.2 image still
   contains the `usb.key` mechanism, and the hotplug path builds
   `/mmc1/usb.key` directly. Per the wiki an empty `usb.key` unlocked the
   port on 1.1.1. If 1.1.2's check is presence-only, that is an unlock with
   no key at all. Nobody has tested it.
2. **Deleted-internal-key confirm** (validates fail-open end to end,
   §30e): locked console with `mcp/61u.key` removed. Static chain predicts
   report code 6 = unlock. Nobody has run it, and it is the one test that
   separates the settled model from the §30e-bis open thread.
3. Garbage-key confirm test (`61u.key.bad`, predicts FAIL) — Layo/OLX console
4. EMAPPLET Memory Copy / Text Script auto-copy gating — same consoles
5. Evil-SD LFN crash test (needs operator-run elsewhere) — same consoles
6. DIAG fuzz pre-gate + SPC defaults (`tools/diag_fuzz.py` ready) — USB + locked
7. EDL 9008 probe (top payoff if unfused) — USB cable + edl client
8. Pairing Telegram keys×IMEIs; duplicate-key resolution — group answers
9. TecToy tool/DB leak — contacts/luck
10. Timing oracle, secure-boot fuse RE — impractical / separate project

Out of scope on purpose: `+LCTSN` **write** mode (alters a radio identifier —
Lei 12.735/2012). Read-only use, or not at all. See §28g.

## Resume commands

```bash
cd /home/rafaelfrequiao/projects/zeebo-61u.key-crack
git log --oneline -5 && git status --short
python tools/stats.py data/spreadsheet.csv --serials
python tools/bruteforce.py data/spreadsheet.csv
python tools/diag_fuzz.py --dry-run
# string/function reference finder (ADR, LDR-literal, movw/movt, PLT, callers)
python tools/find_str_refs.py firmware/1.1.2_APPS.bin --str "usb.key" \
    --callers 0x108d081c
# Ghidra (673MB project, gitignored): re/ghidra/Zeebo61u
```

## Memory pointers (other agents/hosts)

- Hermes `MEMORY.md`: Ghidra location + `0x1078c8d0` ref — STALE
  (correct: cluster `0x108d06ee–0x108d0d80`, this repo `re/notes.md` §2d-i).
- Prime agent sessions: emulator work only, nothing on 61u.key.
