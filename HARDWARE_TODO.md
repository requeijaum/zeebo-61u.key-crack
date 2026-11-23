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
- **§40a — `arg2` is DECODED; read every outcome through it.** `check_61u_key`
  calls `rdm_assign_port(service=0, device=6)`, and device 6 is the RDevMap
  **"USB SER1"** (AMSS `RDM_DEV_MAP` at `0x17567744`); the near-clone calls
  `(service=1, device=4 = "USB MDM")`. So a positive result means *DIAG mapped
  to USB SER1*, and a negative one means either the trigger never ran (§37a) or
  the assignment was overwritten / not applied — **not** "the code 6 was wrong".
  Unknown still: the service *names*, and whether `assign_port` persists.

So a null result on any test below is consistent with at least three different
causes. Record the *setup* (console IMEI, SD contents, whether DIAG appeared,
whether a port enumerated) alongside the outcome, or the result is not reusable.

---

## Access tiers

| tier | what it means | tests |
|---|---|---|
| **A** | SD/USB only, console otherwise untouched | 3, 4 |
| **B** | needs a removable-internal-key edit (or a console already fail-open) | 1, 2, 2b |
| **C/D** | needs NAND write / flash access, or an unlocked console | 5, 6, 7, 8, 13 |
| **E** | needs a second party (operator, group, contact) | 9, 10, 11, 12 |

---

## Tier A — cheap, non-destructive

### 3. Empty `usb.key` on the SD root — DEMOTED, expected no-op

**Prediction:** no effect. The hotplug consumer, `fn~0x107639da`, has **zero**
references of any kind in 1.1.2 APPS under the superset scanner (§36g + §40c:
no `bl`/`blx`, no `b`/`b.w` tail-call, no ARM branch, no LE32 pointer).

**↻ §40b changes where this test should point.** A *third* `usb.key` consumer is
alive — not in hotplug, in the AT table: `+LCTUSBDISABLE` (`0x103611EE`) does
`adr r0,"/usb.key"` and then ends in `[shell+0x54](3, arg, 0x7000)`. So the SD
test stays a no-op control, and the real test became "does any port answer AT
before DIAG" (test 2b, below).

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

### 2b. `AT+LCTUSBDISABLE` — the `/usb.key` path that is actually alive (§40b)

**Handler:** `0x103611EE` — `adr r0,"/usb.key"` (+0x40), then on success calls
`0x1033088C`, which ends in `[shell+0x54](3, arg, 0x7000)`. Its only reference in
the whole image is the Thumb pointer `0x103611EF` at `0x113D0950`: the AT entry
**`+LCTUSBDISABLE`**.

**Prediction:** if any port answers AT before DIAG, this command touches
`/usb.key` and drives the same port-map hook AUXSETTINGS uses.

**Do the static step first:** disassemble `0x112A116A` and decide whether it
opens/creates the file or only formats the string. That single answer changes
what a positive result means.

**Readings:**

- **AT answers and `/usb.key` appears on some volume** → keyless route reopens
  through AT, and it does not depend on which volume `/61u.key` resolves to.
- **AT answers, no file appears** → `0x112A116A` is logging; the handler's effect
  is the port-map call alone.
- **No port answers AT** → §28f closes, and the whole AT surface dies as a
  primitive.

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

### 13. `flixfile.dat` → EMAPPLET (persistência do DIAG)

**Origem:** descoberta importada do Z2Shell, verificada byte a byte contra o dump
(737 bytes, CRLF). O arquivo `fs:/lctsys/flixfile.dat` escolhe o applet de boot:
`0:0`/`FIRSTAPP:0` = Z-Wheel; `FIRSTAPP:1` = **EMAPPLET** (menu de engenharia da
Longcheer, com Field Test → Memory Copy e AUXSETTINGS → SIO Port Map).

**Setup:** com DIAG já ativo, backup do arquivo original (737 B) e upload da
variante gerada por `external/z2shell/flixfile/make_flixfile.py`
(`--firstapp 1 -o flixfile_em.dat`). Reboot.

**Prediction:** o console boota no EMAPPLET; o AUXSETTINGS de lá rearma o DIAG e
o Memory Copy instala applets do SD. É a rota de *persistência* depois do
primeiro acesso — não uma entrada sem chave.

**Readings:**

- **EMAPPLET abre** → o pós-unlock muda: DIAG rearmável sem depender da chave a
  cada boot, e instalação de applet por SD (com o EM ativo).
- **Boot normal** → o FIRSTAPP não é lido desse caminho nesta versão; conferir
  com `--firstapp 0` que a extração reproduz o arquivo original antes de acusar
  o firmware.

**Avisos:** é menu de fábrica — não executar testes de RF/transmissão. Reverter =
re-upload do original. Exige DIAG primeiro: não resolve o problema da chave.

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
                    ├── cheap, informs tests 1, 2, 2b, 7
test 3 (usb.key)  ──┘

test 2  (+LCTUSBLOCK)    ← answers target-volume + which port carries AT
test 2b (+LCTUSBDISABLE) ← same port question, better outcome (`/usb.key`)
test 1  (deleted key)    ← does `assign(0, USB SER1)` actually apply?
   all need: locked console, DIAG observation method

test 6 (copy gating)  ← alternative write route if test 2 is circular
test 5 (JNE-crack)    ← needs NAND access
test 7 (DIAG fuzz)    ← only worth it if test 4 shows a boot window
test 8 (Evil-SD)      ← operator-run, destructive risk
test 13 (flixfile)    ← only AFTER DIAG works; makes it persistent
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

- **`arg2` service semantics — CLOSED (§40a).** It is the RDevMap **device id**:
  `(service=0, device=6 = "USB SER1")`; the near-clone is
  `(service=1, device=4 = "USB MDM")`. What remains is *not* hardware: the
  service **names** (no name table found) and whether `assign_port` persists.
- **`0x112A116A` (§40b)** — decide whether the `+LCTUSBDISABLE` handler opens or
  creates `/usb.key`, or only formats it for the log. Static, small, and it
  changes the reading of hardware test 2b.
- **The `check_61u_key` trigger** (§37a) — static; needs whoever loads the base
  of the `0x108d4e00` region and indexes it.
- **Keygen** — `tools/gen_61u.py` is an intentional stub that refuses to guess.
  The secret is factory-side; 10 pairs, batch falsified, no HMAC/SHA1 match
  (`tools/bruteforce.py`).
