# Moon Sarito's GBAtemp summary post (2026-09-27)

Moon collected statements from TecToy/Zeebo Inc./Qualcomm/support people:

1. Early batches: any `usb.key` (even empty) opens DIAG (already documented).
2. Keygen people won't detail (Qualcomm/TecToy concerns) but consistently
   say: linked to IMEI, focus there.
3. One dev changed IMEIs on devkit consoles (reason unexplained).
4. Two people (dev + Brazil support) describe an ONLINE generator tool:
   enter IMEI → get file(s) for SD → DIAG unlock. Key unique per console
   (from IMEI). Implies the posted duplicate pair is bad data.
5. GBAtemp dev's lost "text script" for any-Zeebo game installs/flashing
   (SDs formatted, script gone); source credible (unreleased Zeebo 2/Z3
   photos). Plus: all Zeebo firmware already dumped
   (`tripleoxygen.net/files/devices/zeebo/dump/`).

Repo grading: (1) known; (2) compatible, unactionable; (3) CONFIRMED
mechanism class — IMEI is NV-provisioned, writable by tools (see `re/notes.md`
section 26); (4) compatible with external-provisioning model; duplicate
likely error; (5) Text Script skeleton confirmed in firmware (`re/notes.md`
section 19), reader/gating open.
