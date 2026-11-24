# Verification and validation plan

Verification asks whether the instrument is built right. Validation asks whether
it answers the question. This project can easily pass the first and fail the
second, so the gates are ordered to make a negative result cheap.

---

## 1. Verification methods

| Method | Used for |
|---|---|
| Inspection (I) | wiring, adapter keying, firmware allowlist table, configuration files |
| Analysis (A) | timing budget, current budget, log size, state-machine reachability |
| Demonstration (D) | stimulus switching without reflash, log completeness, classification rule |
| Test (T) | any requirement whose acceptance is a measured number or a reproducible behaviour |

Every requirement in `REQUIREMENTS.md` names one of these. A gate cannot close on
inspection alone when the requirement says test.

---

## 2. Gates

### G0 — Card emulation (no console attack yet)

**Question:** can the instrument be a card that this terminal accepts?

| Entry | Exit criterion |
|---|---|
| Adapter built and continuity-checked | 10 consecutive cold resets answered with the ATR |
| | Card initialisation completes: the console reaches its normal boot screen with the instrument inserted |
| | The negotiated protocol and the detected voltage class appear in all 10 logs |

**Kill criterion:** if card initialisation cannot complete after three distinct
file-tree configurations, stop and reassess (the terminal may require
authentication).

### G1 — Toolkit liveness

**Question:** does this console execute card-originated commands?

| Entry | Exit criterion |
|---|---|
| G0 closed | The terminal sends `TERMINAL PROFILE` (recorded verbatim) |
| | A `SET UP MENU` stimulus produces visible menu content on screen |
| | The `TERMINAL RESPONSE` comes back with a success result |

**This is the decisive gate.**

**Kill criterion:** if the terminal accepts card initialisation but never raises or
answers a card-originated command across the allowlisted set, G1 closes negative. The
route is dead on this product, the effort moves back to the other three, and the
negative is written up in one page.

### G2 — Parser map (analysis gates, no console needed)

**Question:** which code handles card-supplied bytes, and where are the length
checks?

| Exit criterion |
|---|
| The GSTK command dispatcher is identified in the AMSS image |
| Every proactive command parser that touches card-supplied TLV is listed with its buffer sizes |
| Candidate faults are ranked by reachability × controllability × observability |

Deliverable: `annex/EVIDENCE.md` updated with the map.

**Kill criterion:** if no card-reachable parser takes a length or count from the card
without a bound, G2 closes negative and the route ends here — before any fuzzing and
before any further bench time. That outcome is written up in one page and the effort
returns to the other routes.

### G3 — Fault confirmation

**Question:** does a malformed stimulus produce a reproducible fault?

| Entry | Exit criterion |
|---|---|
| G1 and G2 closed | A stimulus produces the same observable deviation in three consecutive runs |
| | The deviation is distinguishable from a protocol desync (documented comparison) |
| | The APDU log shows the last exchange before the deviation |

**Kill criterion:** if three attempts at a reproducible deviation produce only protocol
desyncs (explained by timing or parity), G3 closes negative. A desync is not a fault,
and treating it as one is the most common way to chase a ghost.

### G4 — Control (the real objective)

**Question:** can the console be brought to map its diagnostic port?

| Exit criterion |
|---|
| The console's USB device, observed from the host, gains an interface that was absent in the G0 baseline capture |
| That interface answers a host probe — the protocol depends on what the interface implements (QCDM framing or AT text); the probe is chosen from the interface class/endpoints, not assumed in advance |
| The difference between the pre- and post-run descriptor sets is attributable to the port assignment (device id 6, `USB SER1`) and not to a reboot or a re-enumeration artefact |
| The state is reached without modifying console storage and without a `61u.key` |

Only G4 validates the project. Everything before it is progress, not success.

**Kill criterion:** if a fault is proven at G3 but no path from it to the port-assignment
service is found within the effort agreed at the G3 review, the project closes with a
fault disclosure and no control claim. That is a complete result, not a failure.

---

## 3. Observation channels (the hard part)

There is no console-side log. Four independent channels are recorded per run, and
a run missing any of them is invalid:

| Channel | What it proves | Instrumentation |
|---|---|---|
| **Wire log** | what the card asked and what the terminal answered | instrument, timestamped, CRC-framed |
| **Screen capture** | whether the terminal executed the command | camera or capture card, one frame per second, plus a manual note |
| **USB descriptors** | the console's device role before and after | host: `lsusb -v` and kernel log, captured pre and post |
| **Power/behaviour** | reboot, hang, or silent continuation | operator note plus instrument gap detection (no APDU for N seconds) |

Classification rule (SYS-F-022), applied identically to every run:

| Class | Criteria |
|---|---|
| `no-menu` | card initialises, no proactive command answered, console boots normally |
| `menu` | proactive command answered with success result and screen content observed |
| `crash` | exchange stops, no further APDU is answered, **and the screen shows a fault or goes blank** |
| `hang` | exchange stops, no further APDU is answered, **and the screen stays normal** (no fault, no blank) |
| `reboot` | APDU exchange restarts from reset without operator action |
| `silent-continue` | exchange stops, console continues to function (menu still navigable) |

`crash` and `hang` are the interesting ones, and they must be distinguished from
`no-menu` by the wire log, not by the screen.

---

## 4. Run validity rules

A run counts only if all of the following hold:

1. Stimulus ID and firmware hash are recorded (`HELLO_ACK`).
2. Drop counters are zero (no lost log records).
3. The pre-run USB descriptor capture exists.
4. The console was cold-started for this run (no warm restarts, which change the
   card init path).
5. The original card was absent for the whole run.

A conclusion drawn from an invalid run is retracted, not argued.

---

## 5. Reproducibility

Each run produces one record:

```json
{
  "run_id": "2026-11-24T14-02-11Z-a3f2",
  "stimulus": "menu-basic",
  "stimulus_hash": "…",
  "firmware": "…",
  "console": {"model": "…", "fw": "1.1.2", "card": "instrument"},
  "protocol": {"class": "B", "clock_hz": 3570000, "t": 0},
  "profile_bytes": "…",
  "classification": "menu",
  "notes": "menu shown, 3 items, no crash",
  "log": "runs/2026-11-24T14-02-11Z-a3f2.jsonl",
  "usb": {"pre": "…", "post": "…"}
}
```

Two runs are comparable only if `stimulus_hash`, `firmware` and `console.fw` match.

---

## 6. Validation of the concept itself

The concept is validated only at G4. If G1 or G3 fails, the correct outcome is a
written negative result:

- what was attempted,
- what was measured,
- which requirement or assumption failed,
- what would have to change for the route to be viable.

A negative result closes a route and is worth as much as a positive one; the
project's value is in the record, not in the conclusion being exciting.

---

## 7. Data management

| Item | Where | Rule |
|---|---|---|
| Run record (JSON) | `BadZeeSIMCard/runs/<run_id>.json` | one per run, never edited after the fact; a correction is a new run note |
| Wire log (JSONL) | `BadZeeSIMCard/runs/<run_id>.jsonl` | append-only; the instrument writes it, the host mirrors it |
| USB captures | `BadZeeSIMCard/runs/<run_id>.usb-pre.txt` / `.usb-post.txt` | captured before and after every run |
| Screen frames | `BadZeeSIMCard/runs/<run_id>.png` | one frame at the moment of interest; the time is in the record |
| Stimuli | `BadZeeSIMCard/stimuli/` | versioned in git; a modified stimulus is a new version |
| Firmware | git, referenced by hash in `HELLO_ACK` | a run log hash that no longer exists in git is invalid |

Retention: run data is kept for the life of the repository. Binary captures are small
(text); if a capture ever exceeds 1 MB it is compressed and its checksum recorded in the
run record.
