# HARDWARE_TODO.md

Everything that is **blocked on a physical console, a port, or a person**.
Companion to `HANDOFF.md` (which holds the settled model and the *static* open
items) and `re/notes.md` (the full RE record, §-referenced throughout).

Created 2026-09-29, right after `re/notes.md` §39 concluded the static
`+LCTUSBLOCK` path. Sections are ordered by information-per-risk, not by
cheapness.

---

## How to read this file

Every test below has a **pre-registered prediction** and a reading for both
outcomes. That is deliberate, because of two open unknowns that make a bare
"nothing happened" uninterpretable:

- **§37a — the trigger is not closed.** `check_61u_key` is reached through
  `0x108d25c2 ← 0x108d2c02`, and the top of that chain has one inbound
  reference of any kind (a Thumb data pointer at `0x108d4f18`) which itself has
  none. The function is *reachable by reference*; **whether it executes at
  boot is unproven.**
- **§38c — `arg2` semantics are unknown.** No test can be called a confirmed
  unlock until it is known whether the RDevMap service treats argument 2 = 6
  as "port enabled", as "no comparison performed, keep the persisted Port Map",
  or as something else. And §37b showed argument 2 is caller-dependent (the
  near-clone reports `4` where `check_61u_key` reports `6`), so **`6` is not a
  success code.**

So a null result on any test below is consistent with at least three different
causes. Record the *setup* (console IMEI, SD contents, whether DIAG appeared,
whether a port enumerated) alongside the outcome, or the result is not reusable.

---

## Access tiers

| tier | what it means | tests |
|---|---|---|
| **A** | SD/USB only, console otherwise untouched | 3, 4 |
| **B** | needs a removable-internal-key edit (or a console already fail-open) | 1, 2 |
| **C** | needs NAND write / flash access | 5 |
| **D** | needs an *unlocked* console (usually the same as the above) | 5, 6, 7 |
| **E** | needs a second party (operator, group, contact) | 8, 9, 10 |

---

## Tier A — cheap, non-destructive

### 3. Empty `usb.key` on the SD root — DEMOTED, expected no-op

**Prediction:** no effect. The function that would read it, `fn~0x107639da`,
has **zero** callers in 1.1.2 APPS (§36g: no `bl`/`blx`, no PLT slot, no
pointer to `0x107639da`/`0x107639db` anywhere in the image).

**Do it anyway?** Only for 1.1.1 compatibility, or as a control that confirms
the §36g static negative in the field. **Not** as a keyless-unlock attempt.

- If DIAG appears → §36g is wrong and the whole priority order needs revisiting.
- If nothing → as predicted; note it and move on. This is the *only* test here
  whose null result is clean, because the static case for it is the strongest
  in the project.

### 4. Observe the boot-time port window (no writes at all)

**Why:** `tools/diag_fuzz.py` targets the observation that DFS Port Manager
occasionally enumerates the DIAG port **at boot without a key** (USB race, no
authorization). If that is real and repeatable, several other tests get cheaper.

**Do:** cold-boot with a USB host and an empty SD, repeatedly; log
`lsusb` / `ls /dev/ttyUSB*` and the `diagcomm_assign_port_cb called in IDLE`
message if any log is reachable (§39c notes registration is unconditional at
init, so logs may exist pre-DIAG).

- Port enumerates sometimes → fuzz it (test 7) inside the window.
- Never enumerates → drop the fuzz line of attack and the "USB race" premise.

### Garbage-key control (`61u.key.bad`) — the *only* key test with a firm prediction

**File:** `61u.key.bad` in this repo, 14 bytes: `AAAAAAAAAAAAAA`.

**Setup:** locked console, `61u.key.bad` on the SD **as `61u.key`**, internal
key untouched.

**Prediction:** `RPC(0,0)` — the strcmp-mismatch branch, and no unlock
(§30e/§31c). Note the *narrowness*: the strcmp is only reached when the
internal key resolves with an all-zero status; a present non-empty internal key
can take the early `report(0,6)` branch instead without ever comparing (§31c).
So "FAIL" here confirms the model only if the internal key's state is known.

---

## Tier B — the two that actually matter

### 1. Deleted-internal-key confirm — **TOP hardware priority**

**Setup:** locked console, `mcp/61u.key` removed (or renamed, or made
unresolvable), SD without a `61u.key`.

**Prediction (static):** `check_61u_key` → resolve `fs:/mcp/61u.key` fails →
helper returns `0x0d` → translated to `259` → nonzero → early
`report(0, 6)` — the same tuple a valid match produces (§30e, §31c).

**Why this is the top test:** it rides a path that is live by reference
(`bl @0x108d2694`), unlike the `usb.key` route, and it needs no key, no JTAG,
no valid key value.

**Readings:**

- **DIAG appears** → fail-open confirmed end to end, and `arg2 = 6` means
  "enable" on this service. This is the single result that would let the project
  claim a keyless unlock, and it also answers §38c's question in the positive
  direction.
- **Nothing happens** → **ambiguous, and three causes are live**: (a) `6` is
  inert and the check is doing what §31d suggests (no comparison performed,
  keep the persisted Port Map); (b) the check never executed because §37a's
  trigger is a stale descriptor; (c) it ran and a later RDevMap call overwrote
  the effect (test 11). Do not read this as "fail-open is wrong".

**Safest subject:** a console that already has its key removed is fail-open/DIAG-on
anyway, so it cannot be broken by the test. Use a throwaway first.

### 2. `+LCTUSBLOCK` — resolves *both* remaining `+LCTUSBLOCK` blockers at once

> **This is the item to test when a console becomes available.**
>
> `AT+LCTUSBLOCK="<content>"` writes `<content>` **verbatim** into `/61u.key`.
> No key generation, no IMEI, no derivation — a raw write (§28c). If the
> target is the *internal* key, then writing a chosen value there plus the same
> value on the SD defeats `strcmp(mcp, card0)` **with no keygen at all**,
> converting the whole keygen problem into a write problem.
>
> **Both remaining blockers are answered by this one command**, and **the
> static path is exhausted** — see below.

**Command:** `AT+LCTUSBLOCK="AAAA"`

**Blocker (a) — which partition does `/61u.key` resolve to?** **Unresolved
statically (§39b).** The image addresses `lctsys` under `fs:/lctsys`,
`fs:/card0/lctsys` *and* `fs:/mcp/lctsys`, so there is no "relative ⇒ mcp"
convention to generalise from, and `/61u.key`'s leading `/` means *root of the
current volume* — a runtime property with no file backing. `OEMefs_GetNativePath`,
the OEMFS API that would settle it, appears only as a `core_ui.c` log string,
never as an importable symbol.

**How to answer it:** after running the command, look for `/61u.key` on
**both** volumes — internal and card. Which one appeared is the answer.

**Blocker (b) — which port carries the ATCOP parser?** The parser is registered
**unconditionally at init** (§39c: shared name pool at `0x113d0900–0x113d0b80`,
`+LCTUSBLOCK` → handler `0x10aff100`), so the command *exists*. Registration
says nothing about the transport, though. The strings are discouraging:
`diagcomm_assign_port_cb called in IDLE`, `Invalid DTR change: UART1`, and
`fail to return DIAG port` all point at DIAG-port assignment being entangled
with UART enumeration.

**How to answer it:** find any port that accepts `AT` and replies `OK` while
DIAG is still locked. Candidate transports: USB, the UART pads, a factory
header, any shell/boot console.

**Readings:**

- **AT reachable pre-DIAG, and the file lands on the internal volume** → the
  keyless-unlock-by-write route is real. Then place the same value on the SD
  and the `strcmp` matches. This is the highest-payoff possible outcome.
- **AT reachable pre-DIAG, but the file lands on card0** → still useful, but
  it only controls the SD side; the internal key then needs another route.
- **AT only reachable on the DIAG port** → **circular and useless**: DIAG is
  exactly what the key gates. Kill this avenue and say so.
- **No port answers `AT` pre-DIAG** → avenue closed; `+LCTUSBLOCK` is confirmed
  not to be a pre-auth primitive. Note that §36e already found the LCT value
  buffer at `0x1434d881` all-zero in the live dump, i.e. the AT path had not run
  on that console — consistent with "unreachable", though not proof.

**Non-destructive variant first.** Run the command on a console whose key is
already removed (fail-open anyway) so nothing of value can be lost, before
touching a console you care about.

---

## Tier C/D — need flash or an unlocked console

### 5. JNE-crack

**Bytes:** patch P1 `04d1` → `00bf` at NAND file offset **`0x80c864`** (§18).
Requires a NAND write. This is the "crack" the console name refers to; it is
the strongest static candidate for a one-patch unlock.

### 6. EMAPPLET Memory Copy / Text Script auto-copy gating

- **EMAPPLET Memory Copy** — no sig gate in the copy flow. Test whether the
  console will copy a modified `61u.key` (or any payload) to the internal
  partition without DIAG.
- **Text Script auto-copy** — DIAG-gated per the wiki, sig-at-run-time. Test
  whether the gate holds.

If either path copies SD → internal without DIAG, that is an alternative to
`+LCTUSBLOCK` for test 2, and it needs no AT channel at all.

### 7. DIAG fuzz pre-gate + SPC defaults

**Tool:** `tools/diag_fuzz.py` — **UNTESTED, no hardware behind it.** Speaks raw
QCDM/DIAG frames (unescaped `0x7E` framing, `0x7D`+`0x20` escaping, CRC-16/CCITT)
for unauthenticated commands and SPC/password defaults, aimed at the test-4 boot
window. Its own docstring flags the framing as "public knowledge, VERIFY against
a live port" — verify before trusting a null result.

### 8. Evil-SD LFN crash test

**Tool:** `tools/make_evil_sd.py` — **UNTESTED.** Builds a FAT32 image planting
200-char LFN entries where the console parses SD names (root, `/mif`,
`/mod/<app>/`, trigger `.dat`).

⚠ **The tool is explicit: it builds an `.img` FILE ONLY. Flashing it to a real SD
must be done by the operator elsewhere. Worst case on console: bootloop while
the SD is inserted.**

**Mechanism is proven, trigger is not:** `tools/prove_overflow.py` emulates the
firmware's own bytes under Unicorn (`FUN_101d7f48` strcat, `FUN_1079bff4`
word-at-a-time strcpy) into a 128-byte stack buffer with a canary, and smashes
it. That proves the *unbounded copy into a fixed stack buffer*. It does **not**
prove a long SD-derived name reaches those functions (§20).

The image also contains a `/61u.key` (14xA) with valid 8.3 aliases and correct
LFN checksums; `--no-key` omits it. Note `re/notes.md` §20/§25 keep this as
"presence-only" for the *key file* (reads are bounded) — the LFN exposure is a
different code path.

---

## Tier E — blocked on other people

- **9.** More `61u.key`/IMEI pairs (Layo console, Telegram group). 10 pairs
  exist; the batch hypothesis is **falsified**, and the one duplicate
  (`3ulp223EpFKhDT` for two IMEIs) may be a spreadsheet error, so **only fresh
  pairs can confirm** anything.
- **10.** TecToy internal tool / database leak (contacts, luck).
- **11.** Pairing the known keys against the unpaired IMEIs; resolving the
  duplicate.
- **12.** UART pad locations, and a 1.1.x image for downgrade testing (none
  obtained).

---

## Dependency order

```
test 4 (observe)  ──┐
                    ├── cheap, informs tests 1, 2, 7
test 3 (usb.key)  ──┘

test 2 (+LCTUSBLOCK)  ← answers 2 blockers, highest ceiling
test 1 (deleted key)  ← answers arg2, cheapest real unlock attempt
   both need: locked console, DIAG observation method

test 6 (copy gating)  ← alternative write route if test 2 is circular
test 5 (JNE-crack)    ← needs NAND access
test 7 (DIAG fuzz)    ← only worth it if test 4 shows a boot window
test 8 (Evil-SD)      ← operator-run, destructive risk
```

**Recommended first session, if only one console is available:** tests 3 → 4 →
1 → 2, in that order, recording the setup for each. Tests 3 and 4 are
non-destructive and cheap; 1 and 2 are where the project actually resolves.

---

## Out of scope, deliberately

`+LCTSN` **write** mode alters a device's IMEI or serial number — a radio
identifier. That is a different legal category from reading one (Lei
12.735/2012 and equivalents elsewhere; confirm the exact article before citing
anywhere). Read-only use, or not at all. The path exists in the image
(`0x10360ff4` SN_write, `0x10361134` IMEI_write, §33c) and that is the whole of
what is recorded. See §28g.

The timing side-channel is real in principle (a `strcmp` over attacker-supplied
data against a stored value) and impractical in practice; not budgeted.

---

## Not here

- **`arg2` service semantics** — a *static* RE task against the modem image, not
  hardware. Tracked in `HANDOFF.md` open item 3 and `re/notes.md` §38c. The
  log-record route to it is closed (§38b, proven), so it means finding the
  `rdevmap` service function via its program/version registration strings
  (`unable to register (RDEVMAPPROG, RDEVMAPVERS, sm)`) and decoding the `cmd`
  switch directly.
- **The `check_61u_key` trigger** (§37a) — static; needs whoever loads the base
  of the `0x108d4e00` region and indexes it.
- **Keygen** — `tools/gen_61u.py` is an intentional stub that refuses to guess.
  The secret is factory-side; 10 pairs, batch falsified, no HMAC/SHA1 match
  (`tools/bruteforce.py`).
