# Ex-dev emails via Moon Sarito (Discord, 2026-09-27)

Source: Moon Sarito recovered old emails from ex-Zeebo developers.
Transcription from briefing; senders unidentified. Treat as 10-year-old
memories, not facts — graded below.

## Email 1 (PT)
Dev consoles had their IMEIs CHANGED ("alterávamos o IMEI dos nossos
consoles de desenvolvimento") → IMEI is provisioned (NV), not fused.
Vague memory otherwise; devs discussing among themselves, nothing useful yet.

## Email 2 (PT)
Ex-devs thread: nobody remembers the key. BREW managed from San Diego.
Assistance (TecToy) might have had a way to request keys. Suggests generic
BREW-unlock content applies to Zeebo.

## Email 3 (EN)
Remembers an "SD card lock" and a "lookup file", purpose forgotten.

## Email 4 (PT) — most detailed, most speculative
Qualcomm developer program: send console IMEI to an ONLINE system, receive
files back (incl. `*.key`) to install on device. Key tied to the OS
"internal serial", itself generated from IMEI — "like Windows software
serials". Suggests BREW 4 (not BREW MP) docs at developer.brewmp.com
(paid program, likely dead).

## Grading (repo, 2026-09-27)
- COMPATIBLE with our RE: external per-device provisioning (mcp key +
  strcmp) is exactly what the firmware shows. Strengthens factory-side
  model; adds nothing to the algorithm itself.
- NEW: IMEI is NV-provisioned and was changeable on dev units (kills any
  remaining e-fuse/HW-ID theory for the INPUT side too).
- "Lookup file": consistent with the mcp key itself (the looked-up value)
  or a factory DB; too vague to act on.
- BREW 4 docs hunt: low value (developer-program Test-Enable docs, not
  keygen secrets; site likely dead; Wayback optional).
- Duplicate-key stance (Moon): agrees it smells like spreadsheet error.
