# Interface control

Three interfaces, three failure modes. Each is specified here because each one
has already been the cause of a dead end on comparable projects.

---

## 1. Contact interface (physical)

| Contact | Signal | Direction (card view) | Notes |
|---|---|---|---|
| C1 | VCC | in | Supplied by the console. Sensed, not loaded. |
| C2 | RST | in | Active low; reset detection is the PHY's trigger |
| C3 | CLK | in | 1–5 MHz assumed; used for ETU timing |
| C5 | GND | — | Common ground with the instrument's own supply |
| C6 | VPP | — | Not connected; legacy programming voltage |
| C7 | I/O | in/out | Half-duplex, open-drain style, pull-up on the card side |

Electrical rules:

- The instrument is powered from USB. The VCC contact is used only as a sense
  line through a resistor, never as a supply (SYS-I-002, SYS-I-004).
- I/O is bidirectional. A single-direction buffer is not acceptable.
- Series resistors on RST, CLK and I/O, close to the contact, protect the
  console's interface if the firmware misbehaves.
- The voltage class (1.8 V / 3 V) is detected from the sensed VCC and selects the
  transceiver's supply; the firmware reports the detected class in every log.

| Parameter | Value | Source of truth |
|---|---|---|
| VCC class A / B / C | 5.0 V / 3.0 V / 1.8 V | ISO 7816-3 |
| Maximum current drawn from VCC | 1 mA | SYS-I-004 |
| I/O pull-up on instrument side | 10–20 kΩ to the class voltage | ISO 7816-3 |
| Contact bounce after insertion | debounce ≥ 5 ms | design |

---

## 2. Timing

| Quantity | Meaning | Budget used here |
|---|---|---|
| ETU | elementary time unit = 372 / f | 104 µs at 3.57 MHz |
| t0 | VCC stable to CLK activity | 400 clock cycles minimum (ISO 7816-3); the instrument waits, it does not enforce |
| ATR character | one character at ETU | must be contiguous; gaps reset the parser |
| tWW | work waiting time | response within 960 ETU typical; the terminal's own limit is unknown |
| t1 | RST release to ATR | must not exceed the terminal's timeout budget |

The instrument's jitter target is ≤ 10 % of one ETU at maximum clock (SYS-P-001).
At 5 MHz an ETU is 74.4 µs, so the jitter budget is ~7 µs — comfortably inside a
PIO implementation with a 133 MHz system clock, and the reason the PHY is PIO
based rather than a polling loop.

---

## 3. Protocol: initialisation

```
console                                instrument
   |  VCC (class applied)                  |
   |  CLK on, RST low ------------------->|  sense VCC class, arm PHY
   |  RST high -------------------------->|  start ATR after the required gap
   |<------------------- ATR -------------|
   |------------ PPS request ------------>|  (optional)
   |<----------- PPS response ------------|
   |------------ first APDU ------------->|
```

ATR content is configuration, not code (derived from SYS-F-001). It declares:

- convention (direct, `TS = 0x3B`),
- the protocol offer (T=0 first; T=1 only when the T=1 path exists),
- the minimum supported clock and the guard time to use,
- historical bytes identifying the card profile — kept constant across runs so
  that a comparison between runs isolates the stimulus, not the identity.

---

## 4. Protocol: APDU and the toolkit exchange

### 4.1 Command/response

| Field | Size |
|---|---|
| CLA INS P1 P2 | 4 bytes |
| Lc (optional) | 1 byte, 0–255 |
| Data (optional) | Lc bytes |
| Le (optional) | 1 byte |

Response: `[data] SW1 SW2`.

Handling rules:

- `SW1 = 0x61` → terminal will issue `GET RESPONSE`; the pending data length is
  `SW2`. This is also the SAT channel in T=0.
- `SW1 = 0x6C` → wrong Le; retry with the length in `SW2`.
- `SW = 0x9000` → success.

### 4.2 Toolkit exchange (the part that matters)

```
console                                instrument
   |--- some command -------------------->|
   |<-- 91 xx ---------------------------|   card signals a pending proactive command
   |--- FETCH (80 12 00 00 00) ---------->|   (USAT) or GET RESPONSE (SAT)
   |<-- D0 <len> <proactive TLV> ---------|
   |--- TERMINAL RESPONSE (80 14 ...) --->|   result of executing it
   |<-- 90 00 ---------------------------|
```

Supporting both fetch mechanisms is required by SYS-F-011 because the terminal's
choice (SAT vs USAT) is not yet measured. The engine records which one the
terminal used; that single field tells us whether this is a 31.111 terminal.

### 4.3 Terminal Profile

Sent by the terminal at initialisation (`80 10 00 00 <len> <profile>`). The
profile bytes state which toolkit features the terminal claims. They are recorded
verbatim (SYS-F-010) and are the primary evidence for which stimuli are even
plausible.

---

## 5. Host control channel

Framed, versioned, over USB CDC.

```
+--------+--------+--------+------------------+--------+
| 0x5A   | ver    | type   | length (u16 LE)  | payload|
+--------+--------+--------+------------------+--------+
                        CRC-16 over payload, appended
```

| Type | Direction | Payload |
|---|---|---|
| `HELLO` | host → instrument | protocol version, expected version |
| `HELLO_ACK` | instrument → host | firmware git hash, ATR hash, voltage class |
| `ARM` | host → instrument | stimulus ID, parameters, run ID |
| `STATUS` | instrument → host | state, queue depths, drop counters |
| `LOG` | instrument → host | one exchange record (direction, time, payload) |
| `RESULT` | instrument → host | classification hint (`menu`/`crash`/`hang`/…) |
| `STOP` | host → instrument | end run, flush log |
| `ERROR` | instrument → host | code, message |

The magic byte `0x5A` ('Z') is a frame delimiter, not a security control.

Rules:

- The instrument refuses `ARM` if the stimulus fails the allowlist gate.
- The instrument never waits for the host to continue the card exchange. If the
  host disappears, the card keeps answering; only the script stops advancing.
- `HELLO_ACK` carries the firmware hash so a run log can never be attributed to
  the wrong binary.

---

## 6. Interface change control

An interface change requires: a version bump, a note in this file, and a re-run of
the gate that depends on it. The card-side protocol (sections 3–4) is fixed by the
standard and cannot change; the host channel can, which is why it is versioned.
