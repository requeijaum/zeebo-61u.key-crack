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
- **Top open static item (§32d/§36f/§38c)**: the `arg2` semantics is the one
  blocker that **cannot** be closed with current tooling. Not in the
  caller-side arguments — they are RDevMap RPC payload. The service state
  lives on the modem side, and the 1.1.2 RAM dump is byte-identical to the
  AMSS image (§36c), so it needs a **separate RE pass on the modem image**:
  find the `rdevmap` service function via its program/version registration
  strings (`unable to register (RDEVMAPPROG, RDEVMAPVERS, sm)`), not via
  logging (§38b). Hardware on the `61u.key` path is the other route.
- **⛔ AMSS log records are PROVABLY dead (§38b); the log→`arg2` route is
  closed.** A complete `ldr [pc,#imm]` index of the modem image (291,233 sites,
  224,445 literal slots) yields **zero** references into the rdevmap record
  block `0xd568f8–0xd56c00`. §36c was right about AMSS and wrong only in
  generalising to APPS (where §36h found the records live). Both images are
  now settled separately — **do not retry the `Invalid cmd: %d` breadcrumbs in
  either image.** Also note `Invalid cmd: %d` (`0x143bdbb`) is shared by 8
  records across `rdevmap.c` + 7 `wms*.c`, so it could not have localised the
  switch anyway.
- **⛔ `tools/refs.py` had a real bug, now fixed (§39a).** The ARM PLT match
  `(w & 0xFFFF0000) == 0xE51FF000` never matched anything — the offset is in
  the low 12 bits, so the correct test is `(w & 0x0FFFF000) == 0x051FF000`.
  The PLT arm of the scan had been silently returning zero. **All §36g/§37a
  negatives were re-run with the fix and all still hold** (`0x107639da` → 0,
  `0x108d2c02` → 0), so those conclusions are now stronger, not weaker.
  `0x108d06ee` gained a real third reference (ARM PLT `0x112df9b0`).
- **⚠ `+LCTUSBLOCK`'s target partition is UNRESOLVED (§39b).** Do not assume
  it writes `fs:/mcp/61u.key`. The image addresses `lctsys` under three
  different roots, and `/61u.key`'s leading `/` means "root of the current
  volume" with no file backing. `OEMefs_GetNativePath` — the API that would
  settle it — appears only as a `core_ui.c` log string, not an importable
  symbol.
- **AT command names are a shared pool (§39c)** at `0x113d0900–0x113d0b80`;
  entries carry their handler inline (`+LCTUSBLOCK` → `0x10aff100`,
  `+STORENEWPIN` → `0x10afef80`). Each `dsat*.c` module registers into it.
  This proves the parser is registered unconditionally at init, but **not**
  which transport carries it — §28f stays open.
- **⚠ `arg2 = 6` is weaker than §35b claimed (§37b).** A census of all 22
  RDevMap client call sites (`refs.py firmware/1.1.2_APPS.bin 0x1079e4a0`)
  shows argument 2 is **caller-dependent**: the near-clone `0x108d07a0`
  reports `r1 = 4` on the same "keys matched" event where `check_61u_key`
  reports `6`. So `6` is not a shared "success/unlock" value. Argument 1
  discriminates the caller, not the outcome (`r0`=0 in `check_61u_key`,
  `r0`=1 in the clone) — §32d's "`r0` is 0 on all paths" was over-stated and is
  corrected there. Hand-verified tuples only; the other sites are a worklist.
- **The RPC interface id is NOT in NAND (§37c).** `0x1036942a` loads
  `0x2a7c3000`, a relocated shared-memory pointer outside every APPS LOAD
  segment. More APPS scanning will not settle `arg2`; the route is AMSS
  `rdevmap.c`.
- **Trigger not closed (§37a).** `check_61u_key ← 0x108d25c2 ← 0x108d2c02`.
  The top has one inbound reference of any kind: a Thumb-form data pointer at
  `0x108d4f18`, which itself has no inbound reference. Live vtable dispatch
  vs stale descriptor is unresolved — do not assume it runs.
- **⛔ The `usb.key` check is UNREACHABLE on 1.1.2 APPS (§36g).**
  `fn~0x107639da` is a real function start but has **zero** callers: no
  `bl`/`blx` in the whole text range, no ARM PLT slot, no LE32 pointer to
  `0x107639da`/`0x107639db` anywhere in the file. The same scanner finds
  `check_61u_key`'s caller correctly, so this is a real negative.
  **Do not plan a keyless `usb.key` unlock on 1.1.2.** The wiki recipe is
  1.1.1-only, and the reason it fails on 1.1.2 is most likely that the
  consuming code is no longer wired up — not that extra paths are required.
  Two earlier claims are also retracted: the check is **not** a vtable method
  (no `0x107639da` in the 32 slots at `0x11459b08`), and `/mmc1/usb.key` is
  **not** composed at runtime (two complete literals are used).
- **⛔ "Log strings are a dead end" is WITHDRAWN (§36h).** The log records
  are reached by a **`ldr` from a literal pool inside the function** — an
  instruction reference, not the data pointer I searched for. `0x10c4cdd0`
  and `0x10c4cde4` are live (`lit @0x10763b00` / `@0x10763b0e`), and the
  `blx 0x105c2ef4` log emitter resolves to a real formatter at `0x1014e902`.
  Fifth instance of the same lesson (§27, §29a, §30a, §2b, §36h): **zero
  data pointers never means no code reference on this image.** §36c's
  AMSS-RAM-identical finding still stands; its "dead end in principle" does not.
- **`+LCTUSBLOCK` / `+LCTSN` are inert on this console (§36e).** The 67-byte
  LCT value buffer at `0x1434d881` is all-zero in the live dump, so the AT
  path never ran — independent support for §29d's "circular" reading.
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

0. **`+LCTUSBLOCK` write primitive** (2026-09-29, §28/§39). `AT+LCTUSBLOCK="<content>"`
   writes the content verbatim into `/61u.key` — no keygen, no derivation.
   ⚠ **The target partition is UNRESOLVED (§39b).** §28d's "relative ⇒ mcp"
   inference was downgraded: this image addresses `lctsys` under `fs:/lctsys`,
   `fs:/card0/lctsys` *and* `fs:/mcp/lctsys`, so there is no convention to
   generalise, and `/61u.key`'s leading `/` means "root of the current volume",
   which has no file backing. Confirm on hardware by looking for `/61u.key` on
   **both** volumes. Blocked on: the AT port (§28f/§39c — registration is
   unconditional at init, so the parser exists, but the transport is unknown and
   the strings hint it may be entangled with DIAG-port assignment).
1. **Deleted-internal-key confirm — TOP hardware priority (§36g).**
   Locked console with `mcp/61u.key` removed. Static chain predicts
   `report(0,6)` = the same state a valid match produces (§30e fail-open).
   `check_61u_key` has a real caller (`bl @0x108d2694`), whereas the
   `usb.key` path has none — though note the **top of the trigger chain is
   still unresolved** (§37a), so the function's reachability ≠ proven
   execution. Needs: one locked console, one file removal, no key, no JTAG.
   The unproven link is unchanged — what the RDevMap service does with
   argument 2 (AMSS side, §35c/§38c).
2. **Empty `usb.key` on the SD root — DEMOTED, predicted no-op (§36g).**
   The check that would read it has zero callers on 1.1.2 APPS, so this is
   expected to do nothing on a 1.1.2 console. Still worth creating if you want
   1.1.1 compatibility, but do not run it as a keyless-unlock attempt. The
   §35b table (absent → no RDevMap call; present → `(0,6)` then `(1,4)`) is
   instruction-accurate but describes an unreachable path.
3. **AMSS `rdevmap` service function** — the `arg2` blocker. The log-record
   route is **closed** (§38b, proven), so this means finding the handler via
   the program/version registration strings and decoding the `cmd` switch
   directly. A separate RE pass on the modem image, not a quick win.
4. Garbage-key confirm test (`61u.key.bad`, predicts FAIL) — Layo/OLX console
5. EMAPPLET Memory Copy / Text Script auto-copy gating — same consoles
6. Evil-SD LFN crash test (needs operator-run elsewhere) — same consoles
7. DIAG fuzz pre-gate + SPC defaults (`tools/diag_fuzz.py` ready) — USB + locked
8. EDL 9008 probe (top payoff if unfused) — USB cable + edl client
9. Pairing Telegram keys×IMEIs; duplicate-key resolution — group answers
10. TecToy tool/DB leak — contacts/luck
11. Timing oracle, secure-boot fuse RE — impractical / separate project

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
# caller finder: proves a function is (un)reachable. Validated: returns the
# real caller of check_61u_key, and zero for the unreferenced usb.key check.
python tools/refs.py firmware/1.1.2_APPS.bin 0x107639da
python tools/refs.py firmware/1.1.2_APPS.bin 0x108d081c
# disassemble at PADDR (the third readelf LOAD column, what Ghidra loads)
python tools/dis.py 0x10763af0 40
# Ghidra (673MB project, gitignored): re/ghidra/Zeebo61u
```

## Memory pointers (other agents/hosts)

- Hermes `MEMORY.md`: Ghidra location + `0x1078c8d0` ref — STALE
  (correct: cluster `0x108d06ee–0x108d0d80`, this repo `re/notes.md` §2d-i).
- Prime agent sessions: emulator work only, nothing on 61u.key.
