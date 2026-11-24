# Bench procedure

The procedure is the enforcement point for C-001, C-002, C-003 and C-005. A run that
skips a step is not a run.

---

## 1. Pre-flight (before the console is powered)

| # | Check | Pass condition |
|---|---|---|
| 1 | The console is the owner's, and is the unit recorded in the session log | model, serial note, firmware 1.1.2 |
| 2 | Adapter continuity: VCC, RST, CLK, GND, I/O to the instrument, no shorts between adjacent contacts | continuity tester, no beep between neighbours |
| 3 | Instrument powered from its own USB, not from the card contact | current into VCC sense ≤ 1 mA |
| 4 | Voltage class detected and matching the transceiver supply | class reported over the host channel |
| 5 | Stimulus allowlist check passed | runner prints `ARM ok`, never `ARM refused` |
| 6 | Host rig armed: USB baseline capture, screen capture, log path | one file per channel exists and is empty |
| 7 | Original SIM stored in a labelled holder, console powered off | both observed |

If any check fails, stop. No run is worth an unverified adapter.

---

## 2. Insertion

1. Console powered off and disconnected.
2. Insert the adapter into the card slot without force; if resistance is felt, remove
   and inspect before retrying.
3. Verify the instrument is powered and enumerating on the host before the console is
   powered on.
4. Only then connect power to the console.

---

## 3. Run

1. Start the runner with the stimulus ID; it takes the USB baseline capture.
2. Power the console on.
3. Observe the screen; note the first visible state and the moment the stimulus is
   expected.
4. Let the run finish or hit the 120 s limit.
5. Power the console off.
6. Runner takes the post-run USB capture and writes the run record.

Do not touch the console during a run. Do not unplug the instrument while powered.

---

## 4. Post-run

| # | Check | Pass condition |
|---|---|---|
| 1 | Wire log present and non-empty | at least reset + ATR + one command |
| 2 | Drop counters zero | `STATUS` reports 0 drops |
| 3 | Classification assigned | one of the six classes in `VV-PLAN.md` §3 |
| 4 | Evidence attached | screen note, USB pre/post, any operator observation |
| 5 | Run valid | all five validity rules in `VV-PLAN.md` §4 hold |

An invalid run is recorded as invalid. It is not deleted and it does not close a gate.

---

## 5. Session end

| # | Step | Confirmation |
|---|---|---|
| 1 | Power the console off and remove the adapter | — |
| 2 | Restore the original SIM | card seated, console powers on to the store shell |
| 3 | Power the console off again and store it as found | — |
| 4 | Copy run data off the instrument and verify checksums | host has every run of the session |
| 5 | Write the session note: runs, classifications, surprises, next steps | one paragraph minimum |

C-005 is satisfied only when step 2 is confirmed by a successful boot.

---

## 6. Recovery

| Situation | Action |
|---|---|
| Console does not boot with the adapter | Remove adapter, restore SIM, boot. Record as `no-menu` with the ATR if one was logged. |
| Console boots but never raises the card session | Record `no-menu`; compare ATR and profile bytes with a previous run. |
| Console hangs after a stimulus | Power cycle. Keep the log. Reproduce twice before recording a fault. |
| Suspected electrical fault (heat, smell, no boot with the original SIM) | Stop the project. Inspect the card interface before any further power-on. |

---

## 7. Never do

- Never send a command outside the allowlist, even "just to see".
- Never run a stimulus with the radio enabled *and* an unclear command parsing path;
  the allowlist is the guard, not the operator's judgement.
- Never modify console storage or firmware.
- Never connect the adapter to a console other than the owner's.
- Never leave the bench with the instrument inserted.
