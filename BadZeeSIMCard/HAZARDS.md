# Hazards, constraints and interlocks

A card that can ask a terminal to do things is a card that can cost money, break
rules or destroy hardware. This file exists so that none of those happen by
accident, and so that the interlocks are requirements rather than good intentions.

---

## 1. Regulatory and ethical frame

| Rule | Consequence for the design |
|---|---|
| The radio is out of scope | No command that could cause transmission is available to any stimulus |
| Own hardware only | No operator SIM, no third-party console, no borrowed equipment |
| The console must remain recoverable | The instrument never writes to console storage; the original card is restored at session end |
| Research record | Claims are only made from recorded runs; no claim from a single unrepeatable event |

The console is abandoned hardware from a discontinued platform. This project
studies it because the owner holds the hardware and because the security model is
of research interest — not to enable misuse on hardware belonging to others.

---

## 2. Command classification

| Class | Examples | Status |
|---|---|---|
| Local display | `SET UP MENU`, `SELECT ITEM`, `DISPLAY TEXT`, `GET INPUT` | allowed |
| Local read | `PROVIDE LOCAL INFORMATION` (IMEI, location, language) | allowed, logged |
| Local timing | `TIMER MANAGEMENT`, `POLL INTERVAL` | allowed |
| Terminal state | `TERMINAL PROFILE` handling, `PROVIDE LOCAL INFORMATION` result format | allowed |
| **Transmission** | `SEND SMS`, `SEND SS`, `SET UP CALL`, `LAUNCH BROWSER`, `SEND USSD` | **blocked in firmware** |
| **Bearer** | `OPEN CHANNEL`, `CLOSE CHANNEL`, `SEND DATA` | **blocked in firmware** |
| **Network event** | `SET UP EVENT LIST` with network/bearer events | **blocked in firmware** |

Blocking is not advisory: the STK engine refuses to enter `PENDING_CMD` with a
command outside the allowlist (SYS-F-013), and the host runner rejects the script
before it is sent.

A benign `PROVIDE LOCAL INFORMATION` is allowed because it is the cheapest way to
prove a full round trip through the terminal's toolkit code with zero external
effect — and it returns the IMEI, which is useful evidence that the terminal is
executing our commands rather than merely displaying a stored string.

---

## 3. Hazard table

| ID | Hazard | Cause | Effect | Severity | Interlock / mitigation |
|---|---|---|---|---|---|
| H-01 | Overvoltage on the card contacts | Wrong transceiver supply vs. detected class | Damage to the console's card interface | High | Voltage class sensed before enabling line drivers; series resistors; no 5 V mode in firmware |
| H-02 | Current draw from VCC | Instrument powered from the contact | Brown-out of the modem's card supply | High | Instrument powered from USB only; VCC through a sense resistor (SYS-I-004) |
| H-03 | Short on insertion | Misaligned adapter | Console reset loop or damage | Medium | Keyed in-line adapter, power off while inserting, continuity check before power-on |
| H-04 | Unintended transmission | A stimulus containing a forbidden command | Charges, RF exposure, rule breach | High | Allowlist gate in firmware **and** runner; review of every script |
| H-05 | Console hangs mid-initialisation | Malformed response timing | Loss of session, possible need to power cycle | Low | Watchdog; power cycle is always available; log survives reset |
| H-06 | Console storage modified | (Design prevents) | Console data loss | High | Instrument has no write path to console storage (C-002) |
| H-07 | Original card damaged | Adapter insertion | Loss of the console's only SIM | Medium | Practice insertion on a scrap card; never force |
| H-08 | Wrong run attributed to wrong stimulus | Log/run mismatch | False conclusion | Medium | `HELLO_ACK` carries firmware hash; every log carries stimulus ID and run ID |
| H-09 | Silent log loss | Slow host, full buffer | Missing evidence | Medium | Drop counters in `STATUS`; a run with drops is invalid (SYS-F-005) |
| H-10 | ESD during handling | Bench practice | Dead Pico or dead console | Low | Ground strap, powered-off insertion |

---

## 4. Interlocks (implemented, not documented-only)

| Interlock | Where | Behaviour |
|---|---|---|
| Allowlist gate | STK engine | Refuses to queue a non-allowlisted command; logs a refusal record |
| Runner pre-check | Host | Refuses to `ARM` a stimulus whose command is not in the allowlist |
| Voltage-class check | PHY | Line drivers enabled only after the class is detected and matches the transceiver configuration |
| Session end check | Procedure | Original card restored; console boots to the store shell; instrument unplugged |
| Log completeness | Runner | Run marked invalid if `STATUS` reports drops > 0 |

---

## 5. Recovery

| Situation | Recovery |
|---|---|
| Console does not boot with the instrument | Remove instrument, restore original card, power cycle; record as a `no-menu` run |
| Console boots but ignores the toolkit | Record `no-menu` with the ATR and profile bytes; this is a valid negative result |
| Console hangs after a malformed stimulus | Power cycle, keep the log, mark the stimulus as `crash` and reproduce twice before believing it |
| Suspected electrical fault | Stop. Inspect adapter and contacts before any further power-on |

---

## 6. What would make this project stop

- Evidence that the terminal never runs the toolkit path (no card menu, no
  terminal profile, no fetch) across correct card emulation.
- Evidence that the console requires SIM authentication the instrument cannot
  provide *and* that initialisation cannot be reached without it.
- Any sign of a hazard event (H-01/H-02/H-06) — the project stops until the cause
  is understood.
