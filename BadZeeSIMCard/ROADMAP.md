# Roadmap

Five phases, each ending in a gate from `VV-PLAN.md`. Effort is in bench sessions
of roughly three hours, by the same operator who wrote the plan — no optimistic
parallelism.

| Phase | Scope | Effort | Gate | Kill condition |
|---|---|---|---|---|
| **P0 — Bench and adapter** | Inspect the SIM access; build the in-line adapter; continuity and voltage-class checks; power the instrument independently | 1–2 sessions | — | Contacts unreachable without destructive intervention → stop and re-scope as a hardware project |
| **P1 — Card emulation** | PIO PHY, ATR, T=0 APDU server, minimal file tree, logging | 3–5 sessions | G0 | Init cannot complete after three tree configurations |
| **P2 — Toolkit liveness** | Terminal profile capture, `SET UP MENU` stimulus, terminal response, classification rig | 2–3 sessions | G1 | No proactive command is ever answered |
| **P3 — Parser map** | AMSS static analysis: dispatcher, per-command parsers, length checks, buffer sizes; rank candidates | 4–8 sessions | G2 | No card-reachable parser with a plausible length fault |
| **P4 — Fault confirmation** | Graded malformed stimuli, three-reproduction rule, wire-log evidence | 3–6 sessions | G3 | No reproducible deviation |
| **P5 — Control** | Turn the fault into a call path to `rdm_assign_port`; observe DIAG | unbounded | G4 | Fault proven but not weaponisable within agreed effort |

Total to G3 (the point where the question "is there a bug" is answered): roughly
13–24 bench sessions plus analysis time. G4 is open-ended by nature.

---

## Sequencing rules

1. No phase starts before the previous gate closes. The temptation to fuzz before
   G1 is real and is the most common way to waste a month.
2. P3 runs in parallel with P2 *only* in the static-analysis sense: reading the
   AMSS image does not need the bench.
3. Any negative result is written up at the gate, in one page, with the measurement
   that produced it.

---

## Deliverables per phase

| Phase | Artifacts |
|---|---|
| P0 | adapter photos, continuity results, voltage class measured |
| P1 | firmware sketch, ATR, 10 valid G0 runs |
| P2 | profile bytes, first menu screenshot, G1 classification |
| P3 | `annex/EVIDENCE.md` parser map with addresses and buffer sizes |
| P4 | run set for the confirmed fault, three reproductions each |
| P5 | DIAG observation: descriptor capture and AT response |

---

## What "done" looks like

- The console enumerates its diagnostic function on USB, observed from the host,
  with no key file and no modification to console storage.
- The same run is reproducible from the recorded stimulus, on a cold start.
- The write-up states exactly which parser fault was used and why it is not a
  protocol desync.

Anything short of that is a partial result and is documented as such — the record
is the deliverable, not the headline.
