# Risk register

Likelihood and impact are judged against the goal in `VV-PLAN.md` G4. Each risk
names a mitigation and, where relevant, the gate at which it becomes decidable —
a risk that cannot be decided at any gate is a blocker and is marked as such.

| ID | Risk | L | I | Why it is real | Mitigation | Decided at |
|---|---|---|---|---|---|---|
| R-01 | The SIM is not user-accessible (soldered / embedded) | M | H | The console is a sealed 3G handheld; many such designs solder the M2M SIM | Inspect the console; if soldered, an in-line interception adapter on the SIM pads is the fallback, at higher mechanical risk | before G0 |
| R-02 | Terminal negotiates T=1 only, or requires T=1 for USAT | M | M | 3G USIMs commonly support both, but the terminal chooses | Build the T=1 path; keep the ATR honest about capability | G0 |
| R-03 | Card initialisation requires authentication the instrument cannot perform | M | H | Some terminals verify a network-derived key early | Emulate the non-crypto path first; if init stops on authentication, the route is dead for this product | G0 |
| R-04 | Terminal never runs the toolkit path | M | H | The product may have disabled STK in its firmware build | G1 is designed to fail cheaply and produce a written negative | G1 |
| R-05 | Timeout behaviour differs from the standard | M | M | Vendor stacks often use shorter work-wait times | Instrumented jitter and explicit timing in the log; measure the terminal's actual timeouts | G1 |
| R-06 | No parser fault is reachable from card input | H | H | Mature baseband stacks have been fuzzed for years | G2 ranks candidates before any fuzzing; abort if no candidate survives analysis | G2 |
| R-07 | Fault exists but is not observable without console instrumentation | H | H | The whole point is that the console has no accessible log | Four-channel observation design; classification by wire log, not by opinion | G3 |
| R-08 | Fault yields modem crash but no path to `rdm_assign_port` | M | M | Code execution on a baseband RTOS is not automatically control of a service | Identify `rdm_assign_port` call path and its argument setup during G2 | G4 |
| R-09 | Instrument damages the console's card interface | L | H | Voltage class mismatch or current draw | Independent supply, sense-only VCC, series resistors, interlocks H-01/H-02 | all gates (pre-flight check in `PROCEDURE.md` §2) |
| R-10 | Lose the console's original SIM | L | M | Adapter insertion | Practice on scrap card; keep original stored in a labelled holder | all gates (session-end checklist) |
| R-11 | Unintended transmission from a stimulus | L | H | A malformed or mis-typed command could be interpreted as `SEND SMS` | Two-stage allowlist (firmware + runner), script review, forbidden classes never compiled in | all gates (SYS-F-013 test) |
| R-12 | No modem emulator, so every experiment needs the physical console | H | M | The project's emulator runs APPS only | Keep runs short and scripted; batch experiments; accept hardware-in-the-loop | each gate's exit criteria assume bench access |
| R-13 | Log loss or mis-attribution invalidates conclusions | M | M | CDC throughput, resets, human error | Firmware hash in handshake, drop counters, run validity rules | every run (invalid run does not close a gate) |
| R-14 | Effort expands beyond the value of the route | M | M | Baseband RE is slow | Gate-driven plan with explicit kill criteria at G0/G1/G2 | each gate |

---

## Decision points

| Gate | If the gate fails | Cost already spent |
|---|---|---|
| G0 | Reassess the whole route; likely stop | adapter + firmware skeleton |
| G1 | Write the negative; return to SD/QX/USB routes | + stimulus library |
| G2 | Stop before touching hardware again | + static analysis |
| G3 | Publish the fault, no control claimed | + fuzzing |
| G4 | Objective met | full project |

The ordering exists so that the most expensive work (G3/G4) is only entered with
evidence from the cheapest gates.

---

## Top three risks, in plain words

1. **R-04/R-06:** the console may simply not run card commands, or the parser may
   be clean. Both are decided before significant effort, by design.
2. **R-07:** without console logging, a fault can be mistaken for a hang. Mitigated
   by classifying from the wire log and requiring three reproductions.
3. **R-01:** if the card is soldered, the mechanical risk rises sharply and the
   project becomes a hardware project before it is a software one.
