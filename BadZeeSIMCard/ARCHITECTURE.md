# Architecture

The instrument is a six-subsystem embedded system with one hard external
constraint: it must behave like a card at the electrical and protocol level while
being driven and observed from a host. Everything below follows from that split
between *real-time card side* and *slow, scripted host side*.

---

## 1. Decomposition

```
+-----------------------------------------------------------------------------------+
|                                 HOST (Linux)                                      |
|                                                                                   |
|  +----------------+   +-----------------+   +----------------+  +--------------+  |
|  | Stimulus runner|   | USB observer    |   | Screen capture |  | Run recorder |  |
|  |  (python)      |   | (lsusb/dmesg)   |   |  (v4l2)        |  | (jsonl)      |  |
|  +--------+-------+   +--------+--------+   +--------+-------+  +------+-------+  |
+-----------|--------------------|---------------------|-----------------|----------+
            |  framed control    |                     |                 |
            v                    v                     v                 v
+-----------------------------------------------------------------------------------+
|                            INSTRUMENT (Pi Pico, 2 cores)                          |
|                                                                                   |
|  core 0  +---------------------+   +--------------------+   +------------------+   |
|          | ISO 7816 PHY (PIO)  |<->| APDU server        |<->| Card file tree   |   |
|          | etu framing, parity |   | CLA/INS dispatch   |   | MF/DF/EF, USIM   |   |
|          +----------+----------+   +---------+----------+   +------------------+   |
|                     |                        |                                    |
|                     |                        v                                    |
|                     |            +---------------------------+                    |
|                     |            | STK engine                |                    |
|                     |            | proactive queue, FETCH,   |                    |
|                     |            | TERMINAL RESPONSE, state  |                    |
|                     |            +-------------+-------------+                    |
|                     |                          |                                  |
|  core 1  +----------v--------------------------v--------------------+             |
|          | Stimulus interpreter (allowlist gate)  |  Logger (ring,    |             |
|          | reads script, arms STK, records        |  CRC, USB CDC)    |             |
|          +----------------------------------------+-------------------+             |
+-----------------------------------------------------------------------------------+
```

### Subsystem responsibilities

| Subsystem | Responsibility | Must not |
|---|---|---|
| **ISO 7816 PHY** | Bit/character framing, parity, work-wait timing, reset detection | interpret APDUs |
| **APDU server** | Command dispatch, status words, file selection, `GET RESPONSE` chaining | know about STK semantics |
| **Card file tree** | Minimal USIM content: ATR-independent EFs, transparent/record files, fixed values plus scripted overrides | hold real operator credentials |
| **STK engine** | Raise proactive commands, handle `TERMINAL PROFILE`, complete `FETCH`/`TERMINAL RESPONSE`, raise the next command from the script | emit a command outside the allowlist |
| **Stimulus interpreter** | Parse a script, sequence steps, apply allowlist, mark run start/stop | modify firmware behaviour at runtime outside the script |
| **Logger** | Timestamped, CRC-framed exchange; survives resets | lose the last exchange on power cut |

---

## 2. Boot and run sequence

```
operator            instrument              console (AMSS)            host rig
   |                    |                        |                     |
   |-- power on ------->|                        |                     |
   |                    |<------ reset ----------|                     |
   |                    |-- ATR ---------------->|                     |
   |                    |<-- PPS / first APDU ---|                     |
   |                    |-- card init responses->|                     |
   |                    |<-- TERMINAL PROFILE ---|  (terminal declares)|
   |                    |   [log: profile bytes] |                     |
   |                    |== arm stimulus =============================>|
   |                    |-- 91xx / FETCH ------->|                     |
   |                    |<-- FETCH -------------|                      |
   |                    |-- proactive TLV ------>|                     |
   |                    |<-- TERMINAL RESPONSE --|                     |
   |                    |   [log: cmd + result]  |                     |
   |                    |                        |-- USB descriptors ->|
   |<-- classify run ---|<====== run jsonl ======|====================>|
```

Three properties matter and are designed in, not hoped for:

1. **The exchange is self-describing.** Every APDU carries direction and time, so
   a run can be replayed and diffed against another stimulus.
2. **The classification does not depend on the console cooperating.** If the
   console crashes mid-exchange the Pico still has the log, and the host still has
   the pre/post USB descriptors.
3. **The script is data, not firmware.** Changing the attack does not change the
   binary, which keeps runs comparable (SYS-F-012).

---

## 3. Card-side state machine

```
        +---------+
   ---->|  RESET  |--- ATR ---> [WAIT_PPS]
        +---------+                    |
                                       v
                              +-----------------+
                              |   CARD_INIT     |  (SELECT MF/DF, READ EF)
                              +--------+--------+
                                       |
                              TERMINAL PROFILE
                                       v
                              +-----------------+
                              |   IDLE          |<-------------+
                              +--------+--------+              |
                                       | script arms           |
                                       v                       |
                              +-----------------+              |
                              | PENDING_CMD     |-- FETCH ---->|
                              +--------+--------+              |
                                       | TERMINAL RESPONSE     |
                                       +-----------------------+
```

`PENDING_CMD` is where every stimulus lives. The engine refuses to enter it if the
command is not allowlisted.

---

## 4. Design decisions

### D-1 T=0 first, T=1 behind a flag

T=0 is the smaller state machine and the mechanism most STK implementations use
for proactive commands (`91xx` status + `FETCH`). T=1 needs block framing,
checksums and re-transmission. DECISION: implement T=0, keep the ATR able to
declare T=1 only once the T=1 path exists. Alternative rejected: declare both
immediately — the terminal may choose T=1 and lock us out mid-session.

### D-2 Power the instrument independently

Drawing current from the card VCC contact is the fastest way to brown out the
modem's card interface or damage it. DECISION: USB power for the Pico, level
shifters on I/O, common ground, VCC contact sensed but not loaded. (SYS-I-002,
SYS-I-004.)

### D-3 Level shifting, not resistor dividers

The card may run at 3 V or 1.8 V; a divider is not enough for bidirectional I/O
and wastes rise time. DECISION: a dual-supply transceiver per line, or a
3 V-tolerant buffer if the card is confirmed 3 V. Rise/fall must stay inside the
7816 envelope at 5 MHz (SYS-P-002).

### D-4 Keep the file tree minimal but *complete enough*

Initialisation fails loudly if a mandatory EF is missing, and a failure tells us
nothing about the STK path. DECISION: serve the smallest tree that completes init
on this terminal, determined empirically, and version it as configuration.

### D-5 Stimulus as data with an allowlist gate

A firmware that can send anything is a legal and safety hazard. DECISION: the
command set is compiled in as an allowlist; the script selects among allowed
commands and parameters. Forbidden commands are rejected before the exchange
(SYS-F-013).

### D-6 Dual-core split

The PHY must not be blocked by logging. DECISION: core 0 owns the wire and the
STK state machine; core 1 owns script parsing and logging, communicating through
a lock-free queue with drop counters (so a slow log is visible, not silent).

### D-7 Observation without console instrumentation

The console has no accessible log. DECISION: define the observation channels up
front (wire log, USB descriptors, screen, power) and require all four per run.
This is a V&V requirement, not an afterthought — see `VV-PLAN.md` section 3.

---

## 5. Failure domains

| Domain | Failure | Containment |
|---|---|---|
| Electrical | Overvoltage / short on a contact | Series resistors, transceiver with enable, current limit |
| Protocol | Desync (parity, timing) | Reset detection, character re-sync, log the raw edge trace |
| Semantic | Stimulus hangs the terminal | Watchdog on the script; power cycle is always available |
| Data | Corrupted card tree | Tree is generated from source, never hand-edited |
| Process | Unrecorded run | Runner refuses to start without a log path |

---

## 6. What this architecture deliberately does not do

- It does not try to be a general-purpose SIM emulator.
- It does not implement crypto (no authentication); the console's card
  initialisation on this platform is not proven to require it, and that is part of
  what the first gate measures.
- It does not attempt RF or network behaviour of any kind.
