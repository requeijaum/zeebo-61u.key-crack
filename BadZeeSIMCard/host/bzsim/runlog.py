"""Run records: the only thing that counts as evidence (VV-PLAN.md §4 and §7).

A run is valid only if all five rules hold. An invalid run is kept, marked, and
never used to close a gate.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

CLASSES = ("no-menu", "menu", "crash", "hang", "reboot", "silent-continue")


@dataclass
class Protocol:
    cls: str = ""      # voltage class A/B/C
    clock_hz: int = 0
    t: int = 0         # negotiated protocol, 0 or 1


@dataclass
class RunRecord:
    run_id: str
    stimulus: str
    stimulus_hash: str
    firmware: str
    console_model: str
    console_fw: str
    cold_start: bool = True
    card_original_present: bool = False
    drops: int = 0
    protocol: Protocol = field(default_factory=Protocol)
    profile_bytes: str = ""
    classification: str = ""
    notes: str = ""
    log: str = ""
    usb_pre: str = ""
    usb_post: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, blob: str) -> "RunRecord":
        data = json.loads(blob)
        data["protocol"] = Protocol(**data.get("protocol", {}))
        return cls(**data)

    def validity_errors(self) -> list[str]:
        """VV-PLAN.md §4, one entry per violated rule."""
        errors: list[str] = []
        if not self.stimulus or not self.stimulus_hash:
            errors.append("rule 1: stimulus id or hash missing")
        if not self.firmware:
            errors.append("rule 1: firmware hash missing")
        if self.drops != 0:
            errors.append(f"rule 2: {self.drops} dropped log records")
        if not self.usb_pre:
            errors.append("rule 3: no pre-run USB capture")
        if not self.cold_start:
            errors.append("rule 4: not a cold start")
        if self.card_original_present:
            errors.append("rule 5: original card was present during the run")
        return errors

    @property
    def valid(self) -> bool:
        return not self.validity_errors()


def classify(
    *,
    saw_profile: bool,
    response_ok: bool,
    menu_on_screen: bool,
    gap_s: float,
    answered_after_gap: bool,
    rebooted: bool,
) -> str:
    """Deterministic classification from observations (VV-PLAN.md §3).

    The wire log decides; the screen only separates crash from hang.
    """
    if rebooted:
        return "reboot"
    if not saw_profile:
        return "no-menu"
    if response_ok and menu_on_screen:
        return "menu"
    if gap_s >= 30.0 and not answered_after_gap:
        return "hang"
    if gap_s >= 30.0 and answered_after_gap and not menu_on_screen:
        return "crash"
    return "silent-continue"


def make_run_id(stamp: str, rand: str) -> str:
    """`<UTC stamp>-<4 hex>`; the timestamp sorts, the suffix disambiguates."""
    return f"{stamp}-{rand[:4]}"
