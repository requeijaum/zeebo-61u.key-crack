# Reference values used by the implementation

Every constant in the code has a source. This file names the source and records what
was verified, so a later reader does not have to trust the code.

---

## 1. Proactive command types (3GPP TS 31.111 §8.6)

Verified against the Wireshark dissector `packet-etsi_card_app_toolkit.c`, which cites
3GPP TS 31.111 v9.7.0 (Release 9, 2012-03), table `proactive_cmd_type`.

| Type | Name | Class in this project |
|---|---|---|
| `0x01` | REFRESH | allowed |
| `0x02` | MORE TIME | allowed (local timer) |
| `0x03` | POLL INTERVAL | allowed |
| `0x04` | POLLING OFF | allowed |
| `0x05` | SET UP EVENT LIST | **conditionally allowed** — only local events, never network events |
| `0x10` | SET UP CALL | forbidden |
| `0x11` | SEND SS | forbidden |
| `0x12` | SEND USSD | forbidden |
| `0x13` | SEND SHORT MESSAGE | forbidden |
| `0x14` | SEND DTMF | forbidden |
| `0x15` | LAUNCH BROWSER | forbidden |
| `0x16` | 3GPP GEOGRAPHICAL LOCATION REQUEST | forbidden |
| `0x20` | PLAY TONE | allowed (local) |
| `0x21` | DISPLAY TEXT | allowed |
| `0x22` | GET INKEY | allowed |
| `0x23` | GET INPUT | allowed |
| `0x24` | SELECT ITEM | allowed |
| `0x25` | SET UP MENU | allowed |
| `0x26` | PROVIDE LOCAL INFORMATION | allowed (read-only items) |
| `0x27` | TIMER MANAGEMENT | allowed |
| `0x28` | SET UP IDLE MODE TEXT | allowed |
| `0x30` | PERFORM CARD APDU | forbidden (talks to another card) |
| `0x31` | POWER ON CARD | forbidden |
| `0x32` | POWER OFF CARD | forbidden |
| `0x33` | GET READER STATUS | forbidden |
| `0x34` | RUN AT COMMAND | forbidden (AT surface) |
| `0x35` | LANGUAGE NOTIFICATION | allowed (local) |
| `0x40` | OPEN CHANNEL | forbidden (bearer) |
| `0x41` | CLOSE CHANNEL | forbidden |
| `0x42` | RECEIVE DATA | forbidden |
| `0x43` | SEND DATA | forbidden |
| `0x44` | GET CHANNEL STATUS | forbidden |
| `0x45` | SERVICE SEARCH | forbidden |
| `0x46` | GET SERVICE INFORMATION | forbidden |
| `0x47` | DECLARE SERVICE | forbidden |
| `0x50` | SET FRAMES | forbidden |
| `0x51` | GET FRAMES STATUS | forbidden |
| `0x60`–`0x62` | MMS retrieve/submit/display | forbidden |
| `0x70`+ | CAT/eCAT activations | forbidden |

The allowlist is a **whitelist in code**: unknown types are refused, so a spec revision
cannot silently widen the attack surface.

Note on namespaces: the APDU instruction codes (below) live in a different space from
the proactive command types. `0x10` as an INS is TERMINAL PROFILE; `0x10` as a command
type is SET UP CALL. They must never share a table.

---

## 2. APDU instruction codes for the toolkit (3GPP TS 31.111 §7)

| APDU | Meaning | Direction |
|---|---|---|
| `80 10 00 00 <Lc> <profile>` | TERMINAL PROFILE | terminal → card |
| `80 12 00 00 <Le>` | FETCH | terminal → card |
| `80 14 00 00 <Lc> <response>` | TERMINAL RESPONSE | terminal → card |
| `80 C2 00 00 <Lc> <event>` | ENVELOPE | terminal → card |

Status words:

| SW | Meaning |
|---|---|
| `90 00` | success |
| `91 xx` | proactive command pending, `xx` bytes available |
| `9F xx` | proactive command pending (UICC busy variant) |
| `6D 00` | instruction not supported |
| `6A 82` | file or application not found |
| `6C xx` | wrong Le, retry with `xx` |
| `6F xx` | technical problem, no precise diagnosis |

---

## 3. Proactive command TLV encoding

Inside the `D0` template, data-object tags carry bit 8 set:

| Tag | Object |
|---|---|
| `0x81` | Command details (3 bytes: number, type, qualifier) |
| `0x82` | Device identities (2 bytes: source, destination) |
| `0x83` | Result (in TERMINAL RESPONSE) |
| `0x85` | Alpha identifier |
| `0x8D` | Text string |
| `0x8F` | Item (item identifier + text string) |
| `0x90` | Item identifier |
| `0x91` | Response length |
| `0x9F 0xXX` | Timer identifier / value (two-byte tag) |

Text coding — measured, not assumed. A real SET UP MENU from a commercial card
(capture reproduced in *SIM Toolkit in Practice*, Radboud University, §3.2):

```
D0 26 81 03 01 25 00 82 02 81 82 85 09 4D 65 6E 75 20 6E 61 6D 65
   8F 07 80 49 74 65 6D 20 31
   8F 07 81 49 74 65 6D 20 32
```

That fixes three things the code depends on:

| Object | Encoding | Evidence |
|---|---|---|
| Alpha identifier (`0x85`) | bytes of the 8-bit default alphabet, **no coding byte** | `85 09 "Menu name"` |
| Item (`0x8F`) | item identifier byte, then the text bytes, no coding byte | `8F 07 80 "Item 1"` |
| Text string (`0x8D`) | `0x04` (8-bit default alphabet) then the text | `8D 0F 04 "Toolkit Test 1"` (3GPP TP-020315) |

A `0x80` first byte means **UCS2**, not ASCII — the Quectel STK manual shows
`85 0B 80 90 60 50 B3 67 0D 52 D9 53 40`, and `8F 0A 01 80 <UCS2>` for an item.
Encoding ASCII with a `0x80` prefix would have been silently wrong, which is why
the builder is pinned to the capture by a unit test.

---

## 4. Device identities

| Byte | Meaning |
|---|---|
| `0x81` | UICC (card) |
| `0x82` | ME (terminal) |
| `0x83` | network |

A card-originated command normally uses `82 02 81 82` (UICC → ME).

---

## 5. Electrical and timing (ISO/IEC 7816-3)

| Quantity | Value | Note |
|---|---|---|
| Contacts | C1 VCC, C2 RST, C3 CLK, C5 GND, C7 I/O | C6 VPP unused |
| Classes | A 5 V, B 3 V, C 1.8 V | A USB-adapter card is class B or C |
| ETU | `372 / f` | 104 µs at 3.57 MHz, 74.4 µs at 5 MHz |
| t0 | VCC stable → CLK | 400 clock cycles minimum |
| Guard time | 12 ETU minimum between characters | enforced between bytes |

---

## 6. What is still unverified

| Item | Why | Where it gets decided |
|---|---|---|
| Which protocol the console negotiates (T=0 / T=1) | needs the console | G0 |
| The terminal's real work-wait timeout | vendor stacks differ | G1 |
| The card file tree this terminal insists on | empirical | G0 |
| Which fetch mechanism is used (FETCH vs `91xx` + GET RESPONSE) | needs the console | G1 |

The code supports both mechanisms precisely because this is unknown.
