# Annex — firmware evidence behind the design

Everything in this annex is a measurement on the 1.1.2 images held in this
repository, except where marked as inference. Addresses are physical addresses as
the loader uses them, which is how the project's tooling reports them.

---

## 1. The toolkit service exists, per command

AMSS 1.1.2 (21 626 880 bytes) contains the GSM toolkit service with one source
file per command:

| String | Address | What it establishes |
|---|---|---|
| `gstk_proactive_cmd.c` | `0x16E51518` | proactive command handling exists as a unit |
| `Unable to find expected proactive cmd rsp 0x%x` | `0x16E51598` | the terminal expects and validates a response |
| `Received Proactive cmd` | `0x16EE2488` | commands are actually received and dispatched |
| `Slot 0x%x App: USIM, Sending Terminal Profile to UICC` | `0x16FC4789` | the terminal declares capabilities to the card |
| `ERR in sending Terminal Profile` | `0x16EE24EE` | error path around that declaration |
| `Could not allocate memory for open channel req` | `0x16FC70CB` | bearer-independent (BIP) path exists |
| `MMGSDI: OPEN CHANNEL REQ FAILURE: %x` | `0x1719E5E5` | BIP failures are tracked at the card-driver layer |
| `gstk_envelope_rsp.c` | `0x00C4A8BC` | envelope (event) responses |
| `gstk_polling.c` | `0x00C4BB0C` | polling capability |
| `gstk_provide_local_info.c` | `0x00C4C0B0` | local information command (IMEI, location) |

A toolkit implementation of this granularity means the card-supplied TLV is parsed
by dedicated code per command. That is the attack surface this project targets.

---

## 2. The port map is owned by the same processor

From the key-validation work in this repository (§40a of the lab notebook):

| Fact | Evidence |
|---|---|
| `check_61u_key` calls a client stub at `0x103693E8` | APPS image, instruction level |
| That stub identifies itself as the port-assignment procedure | its own literal pool: `rdm_assign_port: No client for task %d`, `rdevmap_clnt.c` |
| Success assigns device 6, `USB SER1`, to service 0 | measured arguments at the call sites |
| Device names come from the modem image | table at `0x17567744`, getter at `0x16E07BFA` |
| The argument pair is validated on the modem side | check at `0x16E07C4C` rejects service ≥ 17, device ≥ 24, then tests a per-service mask |

The client is in APPS; the service is in AMSS. The device map, the validation and
the device names all live in the modem image — which is the same image that hosts
the toolkit code above.

**Inference (not measurement):** code execution in AMSS can call the port
assignment directly. The call path has not been traced to its internal entry
point; that trace is part of gate G2.

---

## 3. The card interface is a full UICC driver

From the AMSS string survey:

- `sim_init`, `sim_read`, `sim_write`, `sim_read` appear as driver entry names.
- `apdu`, `sw1`, `sw2`, `fcp` present: the driver parses the card's file control
  parameters and status words.
- `uicc`, `uim` present: the stack addresses a UICC, not a legacy 2G SIM.
- `sms pp`, `envelope`, `open channel`, `bip`: the toolkit reaches the SMS and
  bearer layers.

Consequence for design: the card's file control parameters and EF contents are
parsed before any toolkit command is issued. Two distinct parser surfaces exist —
the file system side (FCP/EF) and the toolkit side (proactive TLV). The plan ranks
both in G2.

---

## 4. What was *not* found

| Question | Status |
|---|---|
| Does the terminal accept a card without authentication? | unknown; decided at G0 |
| Which fetch mechanism does the terminal use (SAT `GET RESPONSE` vs USAT `FETCH`)? | unknown; both supported by the instrument |
| Does the product enable or disable the toolkit in its build? | unknown; G1 answers it |
| Is there a reachable length fault? | unknown; G2 |

These four unknowns are the reason the plan is gate-ordered rather than
feature-ordered.

---

## 5. Evidence that observation will be hard

| Fact | Consequence |
|---|---|
| The diagnostic port is off by default and gated by a key file | there is no console log during the runs |
| The console's only external interfaces are USB (device role) and the card slot | observation is limited to wire, screen, USB descriptors and power |
| A successful run changes the USB device role | this is the one unambiguous, host-observable success signal, and it is the G4 acceptance criterion |

---

## 6. Method note

Two of the conclusions in this repository's recent history were faults in the
project's own scanners rather than properties of the target: an 8-byte error in
the thunk arithmetic and a wrong immediate mask in the Thumb ADR decoder. Both
were found by validating the tool against a known positive.

This project therefore requires, for every parser claim in G2: the address, the
instruction, and a control case that the same tool finds. A negative from an
unvalidated tool is not a negative.
