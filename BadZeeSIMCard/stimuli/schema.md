# Stimulus schema

A stimulus is the smallest unit of experiment: one card behaviour, one run, one
log. It is data, not code, so that two runs differing in one byte are provably
the same experiment otherwise.

---

## 1. File format

One JSON object per file, `stimuli/<id>.json`. The runner computes a hash of the
canonical form; that hash is what identifies the stimulus in the run log.

```json
{
  "id": "menu-basic",
  "version": 1,
  "description": "Benign liveness stimulus: offer a one-item menu.",
  "command": "SET_UP_MENU",
  "params": {
    "title": "Service",
    "items": [{"index": 1, "text": "Info"}],
    "priority": 0
  },
  "expect": {
    "screen": "menu",
    "result": 0
  }
}
```

---

## 2. Fields

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Stable name; equals the filename stem |
| `version` | yes | Bumped on any semantic change; the hash changes too |
| `description` | yes | One sentence, written for someone reading the log a year later |
| `command` | yes | Toolkit command to raise, from the allowlist |
| `params` | no | Structured parameters; the interpreter builds the TLV |
| `raw_tlv_hex` | no | Complete replacement TLV; mutually exclusive with `params` |
| `mutations` | no | Byte-level edits applied after generation; used from G3 |
| `expect` | no | Predicted observation; a mismatch is data, not an error |
| `notes` | no | Anything the operator should know before the run |

---

## 3. Allowlist

The `command` field must be one of:

```
PROVIDE_LOCAL_INFORMATION
SET_UP_MENU
SELECT_ITEM
DISPLAY_TEXT
GET_INPUT
TIMER_MANAGEMENT
POLL_INTERVAL
```

Anything else is rejected by the runner **and** by the instrument (two-stage gate,
`HAZARDS.md` section 4). `SEND SMS`, `SET UP CALL`, `OPEN CHANNEL`,
`LAUNCH BROWSER` and `SEND USSD` are not compiled into the instrument at all.

`raw_tlv_hex` and `mutations` are allowlist-checked on the **command tag**, not on
the payload: a malformed `SET UP MENU` is in scope; a well-formed `SEND SMS` is
not.

---

## 4. Mutation semantics (used from G3)

```json
"mutations": [
  {"offset": 5, "hex": "ff"},
  {"offset": 6, "length": 0}
]
```

| Key | Meaning |
|---|---|
| `offset` | byte offset into the generated TLV (command tag byte 0) |
| `hex` | bytes to write at that offset |
| `length` | truncate the TLV to this length after the write |

Mutations exist so that a fault-finding series is a list of files, diffable and
reproducible, rather than a script that generates bytes at run time.

---

## 5. Rules

1. One variable per stimulus. If a run needs two changes, it is two runs.
2. `expect` is a prediction, not an assertion. A failed prediction is recorded as
   a finding.
3. A stimulus that was modified during a session is a new file with a new version.
4. Stimuli that produced a `crash` or `hang` are kept verbatim, even if later
   understood to be a desync; the record of a wrong hypothesis is part of the
   evidence.

---

## 6. Stimulus-to-gate map

| Stimulus | Gate | Purpose |
|---|---|---|
| `menu-basic` | G1 | prove the terminal executes a card-originated command with no side effect |
| `local-info` (to add) | G1 | prove a full round trip and return the IMEI as evidence |
| mutation series (to add, G3) | G3 | one byte changed per file, from the G2-ranked candidate |
