# Technology selection

Every choice below names the alternative it beat and the requirement that decides
it. A technology chosen "because it is familiar" is not a choice, it is a risk
with no owner.

---

## 1. Instrument platform

| Candidate | Why not |
|---|---|
| USB smart-card reader + host software | Cannot originate proactive commands through the reader's firmware; the reader answers the terminal, not our card logic |
| Arduino/AVR emulator | 16 MHz, 2 KB RAM: one APDU buffer and no room for a card file tree; timing depends on interrupt latency |
| FPGA (iCE40) | Right tool for a production device, wrong for a research instrument: no iteration speed |
| **Raspberry Pi Pico (RP2040)** | 133 MHz dual-core, 264 KB RAM, deterministic GPIO, USB CDC on the same part, cheap enough to keep several |

**Decided:** RP2040, because the whole instrument — card emulation, toolkit state
machine, framing and logging — fits one core, and the second core absorbs logging
jitter.

RP2350 (Pico 2) is a drop-in upgrade if logging ever contends with the PHY; nothing
in the design depends on the older part.

---

## 2. Firmware stack

| Candidate | Why not |
|---|---|
| MicroPython | GC pauses of milliseconds against an ETU of 104 µs |
| CircuitPython | Same, plus no access to the timing primitives needed |
| Arduino-Pico core | Layer of abstraction over exactly the two things we must control |
| **C11 + Pico SDK 2.x, no RTOS** | Deterministic, no hidden interrupt work, direct GPIO and timer access |

**No RTOS on purpose.** A card protocol is a single state machine; an RTOS adds
preemption where what we need is predictability. The two-core split (PHY+state on
core 0, host framing and logging on core 1 when needed) is chosen only if measured
contention appears — not preemptively.

**Busy-wait PHY (decision D-8).** At 3.57 MHz an ETU is 104 µs ≈ 13 800 cycles at
133 MHz. A calibrated busy-wait holds the jitter far inside the 10 % budget
(SYS-P-001) and is inspectable. PIO is the fallback if G0 measures jitter outside
budget, and the evidence for that change would be a logic-analyser capture, not a
preference.

---

## 3. Host stack

| Candidate | Why not |
|---|---|
| Bash + jq | Run records with validity rules are logic, not text munging |
| Node/TypeScript | A runtime and a dependency tree for ~400 lines of logic |
| Rust | Better long term, slower to change while the experiment is still moving |
| **Python 3.11+, stdlib only** | No environment to install on the bench; pytest for tests; dataclasses for record schemas |

Dependencies: none at runtime. `pytest` is the only development dependency, and the
package imports nothing outside the standard library — so the host side runs on the
same laptop that captures USB descriptors, without a virtualenv.

---

## 4. Verification tooling

| Need | Tool | Why this one |
|---|---|---|
| Unit tests of the portable core | CMake + gcc + AddressSanitizer/UBSan, `-Werror` | The core is the part that will hurt on hardware; it must be tested where debugging is cheap |
| Host logic tests | pytest | Fixtures and parametrisation for the validity rules |
| Wire timing and parity | 8-channel logic analyser + sigrok/PulseView | Cheap, scriptable, decodes ISO 7816 |
| Screen evidence | v4l2/ffmpeg capture or a phone camera | The console has no other screen output |
| USB enumeration | `lsusb -v`, kernel log | The only unambiguous success signal at G4 |

---

## 5. Component list

| Item | Purpose | Note |
|---|---|---|
| Raspberry Pi Pico | instrument | two units: one to work, one to replace the one that dies |
| Bidirectional level translator (e.g. TXS0102 or 2× SN74LVC1T45) | I/O and RST at card class voltage | Must be bidirectional; a divider fails at 5 MHz |
| SIM breakout (FPC or contact) | in-line insertion between console socket and instrument | Reversible: no soldering on the console |
| Series resistors 33–100 Ω | protect the console's card interface | close to the contacts |
| Pull-up 10–20 kΩ on I/O | idle-high line | to the class voltage |
| 8-channel logic analyser | timing evidence | 24 MHz sample rate is enough |
| Bench DMM | continuity, VCC current | before every session |

Not a shopping list to trust: `PROCEDURE.md` §1 verifies the assembled adapter
before any console is powered.

---

## 6. Toolchain versions

| Component | Version | Pin |
|---|---|---|
| cmake | ≥ 3.20 (3.31 used) | `CMakeLists.txt` minimum |
| gcc (host build) | ≥ 11 (14.2 used) | ASan/UBSan support |
| Python | ≥ 3.11 (3.13 used) | `pyproject.toml` |
| pytest | ≥ 7 (9.0.3 used) | `pyproject.toml` |
| Pico SDK | 2.1.1 | `tools/build_firmware.sh` `SDK_TAG` |
| arm-none-eabi-gcc | shipped with the SDK install | — |

A version change is a configuration change: it is noted in the session log, because
a run is pinned to firmware and toolchain (README §6).

---

## 7. Reference standards used by the code

| Standard | Used for | Where verified |
|---|---|---|
| 3GPP TS 31.111 | proactive command types, APDU instructions, TLV tags | `spec/REFERENCE.md` §1–§3, checked against Wireshark's dissector (v9.7.0 table) and two independent byte captures |
| ISO/IEC 7816-3 | contacts, classes, ETU, t0, guard time | `spec/REFERENCE.md` §5 |
| ISO/IEC 7816-4 | APDU structure, status words | `spec/REFERENCE.md` §2 |

The encoding rules are pinned by a unit test that compares our builder against a
captured commercial SET UP MENU, and by a Python test that compares the two
implementations against the same capture. Two independent encoders plus one real
capture is the strongest check available before a bench run.
