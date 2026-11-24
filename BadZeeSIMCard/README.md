# BadZeeSIMCard — concept and systems engineering

A card-side research instrument for the Zeebo (MSM7201A, BREW 4.0.2): a
Raspberry Pi Pico that impersonates the USIM, exercises the terminal's
SIM Application Toolkit (GSTK) implementation in AMSS 1.1.2, and — if a parser
fault exists — reaches a state where the console maps its DIAG port without a
`61u.key`.

Everything here is research on hardware the author owns. Nothing in this project
transmits: no SMS, no calls, no bearer channels. See `HAZARDS.md`.

---

## 1. Why this project exists

The console gates its USB debug port behind a key file. Three delivery routes
have been studied so far, and each one ends on the ARM11 side while the effect we
want lives on the modem:

| Route | Reaches | Then needs |
|---|---|---|
| QX asset corruption | ARM11 (BREW/shell) | an RPC to the modem to map the port |
| USB host / HID | ARM11 (APPS) | the same RPC |
| SD auto-copy | ARM11 app directory | the same RPC |

The port assignment (`rdm_assign_port`) is served by the **modem**. The SIM
toolkit implementation (`gstk_*`) is also served by the **modem**. That is the
whole thesis of this project:

> A fault in the terminal's STK path yields execution in the same address space
> that owns the port map.

If that holds, the end state needs no key, no SD card, no network and no APPS
exploit: the instrument triggers the fault, and the console assigns the port.

---

## 2. Concept of operations (ConOps)

**Operator.** One person with physical access to a Zeebo, a lab bench, and a
Linux host. No external services.

**Instrument.** A Pi Pico wired in place of the console's USIM, plus a passive
tap so the exchange can be recorded. The Pico presents a minimal card file
system and a scripted sequence of card-originated commands (proactive commands).

**Mission profile.**

1. Operator powers the console with the instrument inserted.
2. The instrument answers card initialisation, declares capability, and offers a
   benign menu (`SET UP MENU`). This is the *liveness* check: a card menu on
   screen proves the terminal runs the STK path.
3. Operator advances through a graded stimulus library, from benign to malformed
   TLV, one variable per run.
4. Every run is recorded: APDU stream, timing, screen capture, USB enumeration of
   the console, and whether the console rebooted or hung.
5. Success condition: the console's USB device re-enumerates with the diagnostic
   function and answers an AT request from the host.

**Environment.** Bench only. The console's radio may be enabled by the firmware,
so the stimulus allowlist (section 5) forbids any card command that could cause
transmission.

**Time budget per run.** Power-on to menu is seconds; a full stimulus run is under
two minutes, dominated by human observation and power cycling.

---

## 3. System context

```
        +-------------------+         ISO 7816 (CLK/RST/IO)        +------------------+
        |  Lab host (Linux) |<------ USB CDC (control+log) ------->|  Instrument      |
        |  - stimulus runner|                                       |  (Pi Pico)       |
        |  - USB observer   |                                       |  card emulator   |
        |  - screen capture |                                       +---------+--------+
        +---------+---------+                                                 |
                  | USB (observe console role only)                           | SIM contacts
                  v                                                           v
        +-------------------------------------------------------------------------------+
        |                              Zeebo console                                    |
        |  APPS/ARM11 (BREW, shell)          AMSS/ARM9 (GSTK, RDevMap, SIM driver)      |
        +-------------------------------------------------------------------------------+
```

Note what is missing: **there is no console-side instrumentation**. The whole
observation strategy is built around that constraint — see `VV-PLAN.md` section 3.

---

## 4. System boundary

Inside the project:

- The instrument firmware: card emulation, APDU service, STK engine, stimulus
  interpreter.
- The stimulus library and its schema.
- The host-side runner and the observation rig.
- The analysis that maps GSTK parsers and picks stimuli.

Outside the project:

- Console firmware modification of any kind. The instrument never writes to the
  console.
- Network-side work. No SIM OTA, no SMS-PP delivery, no bearer channels.
- Key generation. This project is deliberately orthogonal to `61u.key`.

---

## 5. Non-negotiable constraints

1. **No egress.** The stimulus allowlist admits only card commands that cannot
   cause the console to transmit: `TERMINAL PROFILE`, `SET UP MENU`,
   `SELECT ITEM`, `DISPLAY TEXT`, `GET INPUT`, `PROVIDE LOCAL INFORMATION`
   (read-only fields), `TIMER MANAGEMENT`, `POLL INTERVAL`.
   Forbidden: `SEND SMS`, `SEND SS`, `SET UP CALL`, `OPEN CHANNEL`,
   `LAUNCH BROWSER`, `SEND USSD`, `SET UP EVENT LIST` with network events.
2. **Own hardware only.** No third-party console, no operator SIM, no borrowed
   equipment.
3. **Reversible.** No soldering on the console unless the SIM is unreachable;
   prefer an in-line adapter and restore the original card afterwards.
4. **Recorded.** A run that is not logged did not happen. Every claim in the lab
   notebook must be traceable to a run log.

---

## 6. Document map

| Document | Answers |
|---|---|
| `TECHNOLOGY.md` | platform, stack and component choices, each with its rejected alternative |
| `IMPLEMENTATION.md` | module contracts, build/test results, requirement trace, and the gaps |
| `REQUIREMENTS.md` | what the system must do, and how each item is verified |
| `ARCHITECTURE.md` | how it is decomposed, and why these decisions |
| `INTERFACES.md` | electrical, protocol and software contracts |
| `HAZARDS.md` | what can go wrong, and the interlocks |
| `VV-PLAN.md` | staged verification, gates, observation channels |
| `PROCEDURE.md` | the bench procedure that enforces the constraints |
| `RISK.md` | risks, likelihood, mitigation, kill criteria |
| `ROADMAP.md` | phases, effort, decision points |
| `annex/EVIDENCE.md` | the firmware evidence this design rests on |
| `stimuli/` | stimulus schema and the first benign script |
| `spec/REFERENCE.md` | every constant the code uses, and where it came from |
| `firmware/` | `core/` portable C (tested natively), `pico/` hardware glue |
| `host/` | `bzsim` python package (framing, stimuli, run records) |
| `tools/` | `test.sh` (no hardware) and `build_firmware.sh` |

### Configuration management

Four things are versioned, and a run is pinned to all four:

| Item | Versioned in | Pinned by |
|---|---|---|
| Instrument firmware | git, tag per bench session | `HELLO_ACK` firmware hash in every run record |
| ATR and card file tree | `config/` (to be added at P1) | hash in the run record |
| Stimulus | `stimuli/` | stimulus hash |
| Rigs and adapter | `PROCEDURE.md` plus a photo per session | session note |

A run record that cannot be pinned to all four is invalid, even if it looks good.

---

## 7. Glossary

| Term | Meaning here |
|---|---|
| **STK / SAT / USAT** | SIM Application Toolkit: card-originated commands the terminal executes |
| **Proactive command** | a command the card sends to the terminal (display, menu, send SMS, open channel) |
| **GSTK** | the modem's GSM toolkit service in AMSS, one source file per command |
| **APDU** | the command/response unit exchanged over ISO 7816 |
| **ATR** | the card's answer to reset; declares convention, protocols, timing |
| **PPS** | protocol and parameters selection, negotiated after ATR |
| **RDevMap** | the modem's device-map service; assigns ports (e.g. device 6 = `USB SER1`) |
| **Stimulus** | one scripted card behaviour, executed as a single recorded run |
| **Run** | one power-on to power-off cycle with one stimulus and one log |
