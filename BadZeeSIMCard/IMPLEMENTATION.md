# Implementation

What exists today, what it is verified against, and what is deliberately not built
yet. The last section is the important one: a plan that hides its gaps is a plan
nobody can execute.

---

## 1. Layout

```
BadZeeSIMCard/
├── firmware/
│   ├── core/                  portable C, no SDK, no allocation  [TESTED]
│   │   ├── include/bz_core.h  CRC, TLV, APDU, allowlist, builders
│   │   ├── include/bz_stk.h   toolkit state machine
│   │   ├── src/bz_core.c
│   │   ├── src/bz_stk.c
│   │   ├── tests/test_core.c  96 assertions, ASan/UBSan, -Werror
│   │   └── CMakeLists.txt     native build
│   └── pico/                  thin hardware glue            [NOT COMPILED HERE]
│       ├── include/board.h    pins, ATR, firmware hash
│       ├── include/phy.h
│       ├── include/host_link.h
│       ├── src/main.c         session loop
│       ├── src/phy.c          bit-timed ISO 7816 PHY
│       ├── src/host_link.c    framing over USB CDC
│       └── CMakeLists.txt     requires PICO_SDK_PATH
├── host/
│   ├── bzsim/frame.py         frame codec (mirror of host_link.c)  [TESTED]
│   ├── bzsim/allow.py         allowlist table                      [TESTED]
│   ├── bzsim/stimulus.py      load, validate, hash, encode         [TESTED]
│   ├── bzsim/runlog.py        run record, validity, classification [TESTED]
│   ├── bzsim/cli.py           tlv / verify / stimuli / run / hello
│   ├── tests/                 34 pytest cases
│   └── pyproject.toml
├── stimuli/                   schema.md, menu-basic.json
├── spec/REFERENCE.md          every constant and where it came from
└── tools/
    ├── test.sh                everything verifiable without hardware
    └── build_firmware.sh      SDK checkout + UF2
```

---

## 2. The layering rule

`firmware/core` has no SDK, no hardware access, no dynamic allocation and no
logging side effects. It is the only part of the instrument that can be tested on
a laptop, so it is where every decision that *can* be expressed as data lives:
encoding, state transitions, the allowlist.

`firmware/pico` only moves bytes: GPIO timing, USB frames, the session loop. Its
job is to be small enough to review by eye, because it cannot be unit tested here.

`host/` never touches the card. It arms the instrument, validates stimuli, records
runs and decides validity.

The rule behind the rule: **the untested surface should be boring.** Every hour
spent making the bench debuggable is an hour not spent guessing at a console that
gives no logs.

---

## 3. Module contracts

| Module | Contract | Failure behaviour |
|---|---|---|
| `bz_crc16` | CRC-16/CCITT-FALSE over a buffer | pure function, no state |
| `bz_tlv_*` | append TLVs into a caller buffer, nested with back-patched lengths | sets `err`; never writes past `cap`; `bz_tlv_ok()` reports |
| `bz_apdu_parse` | split an APDU into header, Lc/Le, flags | returns 0 if shorter than a header; sets `malformed` when Lc exceeds the bytes present |
| `bz_allow_check` | parse the D0 template far enough to read the command type | whitelist: unknown ⇒ denied; not a template ⇒ malformed |
| `bz_cmd_build` | D0 + command details + device identities + caller-supplied TLVs | −1 on overflow |
| `bz_cmd_menu` / `bz_cmd_display_text` | encode the two commands used by G1 | −1 on overflow, never truncates |
| `bz_stk_*` | one command in flight; both fetch mechanisms; profile capture | refused commands increment `refusals` and are never queued |
| `phy_*` | characters, ATR, one APDU read, one response write | returns negative codes rather than hanging |
| `host_link_*` | framing, message dispatch, exchange logging | a bad CRC drops one byte and resyncs |
| `bzsim.frame` | same frame format as the firmware | raises `FrameError` |
| `bzsim.stimulus` | load/validate/encode/hash | raises `StimulusError` before anything is armed |
| `bzsim.runlog` | record, validity rules, classification | returns a list of violations, never a boolean alone |

---

## 4. A run, module by module

```
host                     instrument                       console
 |-- ARM(tlv) ---------->| bz_stk_arm -> allowlist gate
 |                       | state PENDING
 |                       |<----------------------------- RST release
 |                       |-- phy_send_atr() ------------->|
 |                       |<-- TERMINAL PROFILE (80 10) --| bz_stk_handle: capture
 |                       |<-- any APDU -----------------| sw 91 xx  (pending)
 |                       |<-- FETCH (80 12) ------------| bz_stk_handle: deliver
 |                       |   (or GET RESPONSE, A0 C0)   | state WAIT_RESP
 |<-- LOG(exchange) -----|                              |
 |                       |<-- TERMINAL RESPONSE (80 14) | result captured, IDLE
 |                       |                              |-- USB descriptors
 |<-- LOG, RESULT -------|                              |
 v
 classify() + validity_errors() + run record
```

---

## 5. Build and test

Everything below was executed in this repository:

```
$ tools/test.sh
== native core tests (ASan/UBSan, -Werror) ==
96 checks, 0 failures
== host tests ==
34 passed in 0.05s
== stimulus gate ==
OK        menu-basic.json          SET UP MENU                850c8ae918be57c9
1 stimuli, 0 rejected
```

Firmware (needs the SDK, not run here):

```
$ tools/build_firmware.sh      # clones pico-sdk 2.1.1, builds badzeesim.uf2
```

The encoded command for the first bench run:

```
$ python3 -m bzsim tlv stimuli/menu-basic.json
tlv       D0 19 81 03 01 25 00 82 02 81 82 85 07 53 65 72 76 69 63 65 8F 05 01 49 6E 66 6F
```

---

## 6. Requirement → module → test

| Requirement | Implementation | Verification |
|---|---|---|
| SYS-F-001 ATR | `board.h` `BZ_ATR_BYTES`, `phy_send_atr` | bench only (G0) |
| SYS-F-002 protocol negotiated | T=0 implemented; T=1 **not yet** | gap |
| SYS-F-003 card file tree | **not yet implemented** | gap, depends on G0 |
| SYS-F-004 APDU size and chaining | `bz_apdu_parse`, `p3_zero`, `malformed` | `test_apdu` |
| SYS-F-005 exchange logging | `host_log_exchange` + `bzsim.runlog` | firmware untested; host tested |
| SYS-F-010 profile capture | `bz_stk_handle` case `0x10` | `test_stk_flow` |
| SYS-F-011 proactive exchange | `bz_stk_arm`/`handle`, both fetch paths | `test_stk_flow`, `test_sat_path` |
| SYS-F-012 stimulus as data | `bzsim.stimulus` + `stimuli/schema.md` | `test_stimulus` |
| SYS-F-013 allowlist | `bz_allow_check`, `bzsim.allow`, both-stage gate | `test_allow`, `test_stimulus` (incl. mutation smuggling) |
| SYS-F-014 voltage-class refusal | **not yet implemented** | gap, needs the sense circuit |
| SYS-F-020 first-APDU latency | `host_log_exchange` timestamps | coarse (ms); gap for µs |
| SYS-F-021 USB descriptors | **not yet implemented** (host rig script) | gap |
| SYS-F-022 classification | `bzsim.runlog.classify` | `test_classification` (7 cases) |
| SYS-I-003 host channel | `host_link.c`, `bzsim.frame` | `test_frame` (layout, CRC, resync) |
| SYS-P-001 timing | busy-wait PHY design | logic analyser at G0 |

---

## 7. Coding rules

- C11, `-Wall -Wextra -Wpedantic -Werror`, ASan and UBSan on the native build.
- No `malloc` in the core: every buffer is caller-provided and bounded.
- No silent truncation: a value that does not fit is an error, never a clip.
- Python: standard library only; dataclasses for anything that gets serialised.
- One rule per function; if a function needs a paragraph of explanation, it is two
  functions.

---

## 8. What is deliberately not built yet

| Gap | Why it waits | Gate |
|---|---|---|
| Card file system (SELECT/READ/GET RESPONSE) | The tree must match what this terminal demands; guessing writes code that fails for the wrong reason | G0 |
| T=1 protocol | Not needed until the terminal asks; implementing both up front doubles the untested surface | G0 |
| Voltage-class logic (SYS-F-014) | Needs the sense divider characterised | G0 |
| USB descriptor capture script (SYS-F-021) | One evening of work, but worthless before G1 | G1 |
| Screen-capture rig | Same | G1 |
| Serial transport (host ↔ Pico over CDC) | The frame codec exists and is tested; the transport is 40 lines once the board is flashed | G0 |
| TLV fuzzer / mutation series | Writing mutations before the parser map is ranked wastes bench time | G3 |

Each gap is a requirement, not an oversight: the traceability table above names it.

---

## 9. Next three increments

1. **Serial transport + HELLO/ARM loop on the bench** (closes SYS-I-003 end to end,
   needs a flashed Pico, no console).
2. **Card file system v0** — the smallest tree that gets the console past card
   initialisation, driven by the APDU log from run 1 (G0).
3. **USB descriptor capture** — the baseline that makes G4 measurable at all (G1).
