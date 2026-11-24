# Requirements

Numbering: `SYS-F-nnn` functional, `SYS-P-nnn` performance, `SYS-I-nnn`
interface, `C-nnn` constraint. Every requirement carries a verification method
(I = inspection, A = analysis, D = demonstration, T = test) and an acceptance
criterion that can be recorded in a run log.

A requirement without a verifiable acceptance criterion is a wish and does not
belong here.

---

## 1. Stakeholder needs

| ID | Need | Source |
|---|---|---|
| SN-1 | Determine whether the console executes card-originated commands at all | open question in the lab notebook (§44) |
| SN-2 | Determine whether the terminal's STK parser can be driven into memory corruption from the card side | same |
| SN-3 | If it can, obtain the port assignment without a key | project goal |
| SN-4 | Never cause radio transmission, data charges or damage | constraints |
| SN-5 | Every conclusion reproducible from a log | house rule |

---

## 2. Functional requirements

### Card emulation

| ID | Requirement | Verify | Acceptance |
|---|---|---|---|
| SYS-F-001 | The instrument shall answer reset with an ATR and remain responsive for at least 30 s. | T | Cold reset 10/10 times; no timeout in the modem's card-init log path. |
| SYS-F-002 | The instrument shall support the protocol the terminal selects after ATR (T=0, or T=1 with checksum) and shall report which one was negotiated. | T | Negotiated protocol appears in every run log. |
| SYS-F-003 | The instrument shall serve a minimal USIM file tree sufficient to complete card initialisation. | T | Console reaches the menu stimulus without card-init errors. |
| SYS-F-004 | The instrument shall accept and parse APDUs of at least 261 bytes (5 header + 255 data) and return responses up to 258 bytes with correct `SW1 SW2`. | T | Loopback test with maximum-length APDU passes. |
| SYS-F-005 | The instrument shall log every APDU in both directions with direction, timestamp, and full hex payload. | D | Log inspection of any run shows a complete, ordered exchange. |

### Toolkit behaviour

| ID | Requirement | Verify | Acceptance |
|---|---|---|---|
| SYS-F-010 | The instrument shall declare its capabilities to the terminal at initialisation (`TERMINAL PROFILE` response handling) and record what the terminal declares back. | T | The terminal's profile bytes appear in the run log. |
| SYS-F-011 | The instrument shall be able to raise a proactive command and complete the exchange (command, terminal response) for the allowlisted command set. | T | `SET UP MENU` produces a terminal response with result 0. |
| SYS-F-012 | The instrument shall expose a stimulus library selected per run without reflashing where practical. | D | Switching stimulus changes behaviour with one host command. |
| SYS-F-013 | The instrument shall refuse, at runtime, any stimulus that contains a forbidden command (constraint C-001). | T | A stimulus carrying `SEND SMS` is rejected before any exchange. |
| SYS-F-014 | The instrument shall refuse to enable its line drivers when the detected card voltage class does not match its configuration, and shall log the refusal. | T | With the transceiver configured for 3 V and a 1.8 V class detected, no driver is enabled and a refusal record appears; console unaffected. |

### Observation

| ID | Requirement | Verify | Acceptance |
|---|---|---|---|
| SYS-F-020 | The instrument shall timestamp the interval between power-on and the first APDU. | T | Value present in every run log; matches the console's documented init order. |
| SYS-F-021 | The host rig shall record the console's USB device descriptor set before and after each run. | D | Two captures per run, stored with the log. |
| SYS-F-022 | The host rig shall classify each run as one of: `no-menu`, `menu`, `crash`, `hang`, `reboot`, `silent-continue`. | A | Classification rule documented and applied identically to all runs. |

---

## 3. Performance requirements

| ID | Requirement | Verify | Acceptance |
|---|---|---|---|
| SYS-P-001 | Response latency shall not exceed one ETU plus processing overhead, per ISO 7816 timing. | T (logic analyser) | Measured latency over 1 000 exchanges: p99 ≤ 1 ETU + 20 µs; zero work-wait violations in the terminal's view (no retry, no abort) |
| SYS-P-002 | The instrument shall tolerate a terminal clock of 1–5 MHz without resynchronisation errors. | T | 10 consecutive resets and 1 000 APDUs at each of 1.0, 3.57 and 5.0 MHz with zero parity errors reported by the terminal |
| SYS-P-003 | Run log size shall stay under 1 MB for a 120 s run. | A | Computed worst case (bytes per record × records per second × 120) under 1 MB; verified on one real run |

---

## 4. Interface requirements

| ID | Requirement | Verify | Acceptance |
|---|---|---|---|
| SYS-I-001 | Electrical interface shall comply with `INTERFACES.md` section 2, including voltage class autodetection. | I, T | Inspection against the contact table; measured class reported correctly for a 3 V card and a 1.8 V card (or the class the console provides) |
| SYS-I-002 | The instrument shall be powered independently of the card VCC contact. | I | Schematic shows no power path from VCC; measured current into the VCC contact ≤ 1 mA |
| SYS-I-003 | The host control channel shall be a framed message protocol as defined in `INTERFACES.md` section 5, versioned. | I | Frame layout inspected; version byte present; an out-of-version `HELLO` is rejected with `ERROR` |
| SYS-I-004 | The instrument shall not draw more than 1 mA from the VCC contact. | T | Series-resistor drop measured across 100 cold starts; reported value ≤ 1 mA |

---

## 5. Constraints

| ID | Constraint | Verify | Acceptance |
|---|---|---|---|
| C-001 | No stimulus may cause transmission (see allowlist in `README.md` section 5). | I, T | Source inspection shows the forbidden commands are not compiled in; a stimulus naming one is rejected (SYS-F-013 test) |
| C-002 | No modification of console firmware or storage by this project. | I | Design review: the instrument has no code path that writes to console storage; procedure has no such step |
| C-003 | Own hardware only. | I | Session log names the console and states ownership; no third-party hardware in any run |
| C-004 | Every conclusion traceable to a run log with stimulus ID and console state. | I | Audit of the last gate: every claim in the write-up cites a valid run ID |
| C-005 | The original SIM shall be restored, and the console left bootable, at the end of every session. | D | `PROCEDURE.md` section 5 checklist signed in the session log; console boots to the store shell with the original card |

---

## 6. Derived requirements (allocated)

| Parent | Allocation | Derived requirement |
|---|---|---|
| SYS-F-001 | Card emulator | ATR byte sequence stored as configuration, not hardcoded |
| SYS-F-002 | Card emulator | T=1 path implemented behind a compile flag; T=0 first |
| SYS-F-004 | APDU server | Chaining support for `GET RESPONSE` in T=0 |
| SYS-F-010 | STK engine | Terminal profile parser must accept unknown bits without rejecting |
| SYS-F-021 | Host rig | USB capture must not depend on the console enumerating successfully |
| SN-3 | Analysis | Static map of the GSTK command dispatcher is a prerequisite (see `annex/EVIDENCE.md`) |

---

## 7. Requirements not in scope (and why)

| Excluded | Reason |
|---|---|
| Over-the-air delivery (OTA/SMS-PP) | Requires network and transmission; violates C-001 |
| Reading or cloning a real operator SIM | Third-party credentials; out of scope |
| Any console-side write | The instrument has no path; C-002 |
| Key generation | Orthogonal; handled elsewhere in the repository |

---

## 8. Traceability

| Need | Requirements | Gate that produces evidence |
|---|---|---|
| SN-1 (does the console run card commands?) | SYS-F-001, SYS-F-002, SYS-F-003, SYS-F-004, SYS-F-011, SYS-F-020 | G0 → G1 |
| SN-2 (can the parser be driven to a fault?) | SYS-F-010, SYS-F-012, SYS-F-013, SYS-P-001, SYS-P-002 | G2 → G3 |
| SN-3 (port assignment without a key) | SYS-F-021, SYS-F-022, SYS-I-003 | G3 → G4 |
| SN-4 (no transmission, no damage) | C-001, C-002, C-003, SYS-F-013, SYS-F-014, SYS-I-001, SYS-I-002, SYS-I-004 | every gate (interlocks) |
| SN-5 (reproducible record) | SYS-F-005, SYS-F-012, SYS-P-003, SYS-I-003, C-004, C-005 | every gate |

No requirement is orphaned: each appears in at least one row above.

---

## 9. Assumptions

An assumption is a belief the design needs but has not measured. Each names the gate
at which it stops being an assumption.

| ID | Assumption | If false | Decided at |
|---|---|---|---|
| A-1 | The console's card interface is reachable without destructive work | Project becomes a hardware project first (R-01) | before G0 |
| A-2 | The terminal performs card initialisation without network authentication | Init blocks; route dead for this product (R-03) | G0 |
| A-3 | The product build has the toolkit path enabled | No card-originated command executes (R-04) | G1 |
| A-4 | Card-supplied TLV reaches at least one parser with a length derived from the card | No fault reachable by this route (R-06) | G2 |
| A-5 | A fault can be observed through the four channels | Fault indistinguishable from a hang (R-07) | G3 |
| A-6 | Modem-side code execution can reach the port-assignment service | Fault proven but not weaponisable (R-08) | G4 |
| A-7 | The card slot's mechanical presence contact does not need emulation beyond insertion | Init does not start (H-05 category) | G0 |
