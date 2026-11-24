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

### Observation

| ID | Requirement | Verify | Acceptance |
|---|---|---|---|
| SYS-F-020 | The instrument shall timestamp the interval between power-on and the first APDU. | T | Value present in every run log; matches the console's documented init order. |
| SYS-F-021 | The host rig shall record the console's USB device descriptor set before and after each run. | D | Two captures per run, stored with the log. |
| SYS-F-022 | The host rig shall classify each run as one of: `no-menu`, `menu`, `crash`, `hang`, `reboot`, `silent-continue`. | A | Classification rule documented and applied identically to all runs. |

---

## 3. Performance requirements

| ID | Requirement | Rationale | Verify |
|---|---|---|---|
| SYS-P-001 | Response latency shall not exceed 1 ETU + processing, per ISO 7816 timing. | The terminal aborts on a work-wait violation. | T with a logic analyser |
| SYS-P-002 | The instrument shall tolerate a terminal clock of 1–5 MHz without resynchronisation errors. | Unknown clock on this platform. | T across the range |
| SYS-P-003 | Run log size shall stay under 1 MB for a 120 s run. | Keeps logs in git-adjacent storage. | A |

---

## 4. Interface requirements

| ID | Requirement | Verify |
|---|---|---|
| SYS-I-001 | Electrical interface shall comply with `INTERFACES.md` section 2, including voltage class autodetection. | I, T |
| SYS-I-002 | The instrument shall be powered independently of the card VCC contact. | I |
| SYS-I-003 | The host control channel shall be a framed message protocol as defined in `INTERFACES.md` section 5, versioned. | I |
| SYS-I-004 | The instrument shall not draw more than 1 mA from the VCC contact. | A, T |

---

## 5. Constraints

| ID | Constraint | Enforcement |
|---|---|---|
| C-001 | No stimulus may cause transmission (see allowlist in `README.md` section 5). | Firmware allowlist (SYS-F-013) |
| C-002 | No modification of console firmware or storage by this project. | Design review; instrument has no path to the console's storage |
| C-003 | Own hardware only. | Procedure |
| C-004 | Every conclusion traceable to a run log with stimulus ID and console state. | V&V gate review |
| C-005 | The original SIM shall be restored, and the console left bootable, at the end of every session. | End-of-session checklist |

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
