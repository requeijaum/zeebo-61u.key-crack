"""Command allowlist — the host half of the two-stage gate (SYS-F-013).

Ordered numbers come from 3GPP TS 31.111 §8.6, verified in spec/REFERENCE.md §1.
The set is a whitelist: anything not listed is refused, so a spec revision cannot
silently widen what the instrument may do.
"""

from __future__ import annotations

# type -> (name, allowed)
COMMANDS: dict[int, tuple[str, bool]] = {
    0x01: ("REFRESH", True),
    0x02: ("MORE TIME", True),
    0x03: ("POLL INTERVAL", True),
    0x04: ("POLLING OFF", True),
    0x05: ("SET UP EVENT LIST", False),  # can request network events
    0x10: ("SET UP CALL", False),
    0x11: ("SEND SS", False),
    0x12: ("SEND USSD", False),
    0x13: ("SEND SHORT MESSAGE", False),
    0x14: ("SEND DTMF", False),
    0x15: ("LAUNCH BROWSER", False),
    0x16: ("GEOGRAPHICAL LOCATION REQUEST", False),
    0x20: ("PLAY TONE", True),
    0x21: ("DISPLAY TEXT", True),
    0x22: ("GET INKEY", True),
    0x23: ("GET INPUT", True),
    0x24: ("SELECT ITEM", True),
    0x25: ("SET UP MENU", True),
    0x26: ("PROVIDE LOCAL INFORMATION", True),
    0x27: ("TIMER MANAGEMENT", True),
    0x28: ("SET UP IDLE MODE TEXT", True),
    0x30: ("PERFORM CARD APDU", False),
    0x31: ("POWER ON CARD", False),
    0x32: ("POWER OFF CARD", False),
    0x33: ("GET READER STATUS", False),
    0x34: ("RUN AT COMMAND", False),
    0x35: ("LANGUAGE NOTIFICATION", True),
    0x40: ("OPEN CHANNEL", False),
    0x41: ("CLOSE CHANNEL", False),
    0x42: ("RECEIVE DATA", False),
    0x43: ("SEND DATA", False),
    0x44: ("GET CHANNEL STATUS", False),
    0x45: ("SERVICE SEARCH", False),
    0x46: ("GET SERVICE INFORMATION", False),
    0x47: ("DECLARE SERVICE", False),
    0x50: ("SET FRAMES", False),
    0x51: ("GET FRAMES STATUS", False),
}

BY_NAME: dict[str, int] = {name: code for code, (name, _) in COMMANDS.items()}


def name_of(code: int) -> str:
    return COMMANDS.get(code, ("UNKNOWN", False))[0]


def is_allowed(code: int) -> bool:
    """Whitelist semantics: unknown codes are not allowed."""
    return COMMANDS.get(code, ("", False))[1]


class NotAllowed(Exception):
    """The command is not on the whitelist and must not be armed."""
