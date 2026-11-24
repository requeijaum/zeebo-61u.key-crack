import json
from pathlib import Path

import pytest

from bzsim import allow
from bzsim.stimulus import Stimulus, StimulusError

ROOT = Path(__file__).resolve().parents[2]
MENU = ROOT / "stimuli" / "menu-basic.json"


def _write(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / f"{data['id']}.json"
    p.write_text(json.dumps(data))
    return p


def test_menu_basic_loads():
    st = Stimulus.load(MENU)
    assert st.command == "SET UP MENU"
    assert st.digest()
    tlv = st.tlv()
    assert tlv[0] == 0xD0
    assert tlv[2] == 0x81 and tlv[3] == 0x03
    assert tlv[5] == 0x25  # SET UP MENU


def test_digest_is_stable():
    assert Stimulus.load(MENU).digest() == Stimulus.load(MENU).digest()


def test_forbidden_command_rejected(tmp_path):
    path = _write(
        tmp_path,
        {
            "id": "bad-sms",
            "version": 1,
            "description": "must never be armed",
            "command": "SEND SHORT MESSAGE",
        },
    )
    with pytest.raises(StimulusError, match="allowlist"):
        Stimulus.load(path)


def test_forbidden_raw_tlv_rejected(tmp_path):
    path = _write(
        tmp_path,
        {
            "id": "bad-raw",
            "version": 1,
            "description": "SEND SHORT MESSAGE smuggled as raw bytes",
            "command": "SET UP MENU",
            "raw_tlv_hex": "D00A810301130082028182",
        },
    )
    with pytest.raises(StimulusError, match="allowlist"):
        Stimulus.load(path)


def test_mutation_cannot_smuggle_forbidden_command(tmp_path):
    """A byte-level mutation that turns the type into SEND SMS must be refused."""
    path = _write(
        tmp_path,
        {
            "id": "mutation-smuggle",
            "version": 1,
            "description": "menu mutated into SEND SMS",
            "command": "SET UP MENU",
            "params": {"alpha": "x"},
            "mutations": [{"offset": 5, "hex": "13"}],
        },
    )
    with pytest.raises(StimulusError, match="allowlist"):
        Stimulus.load(path)


def test_raw_and_params_are_exclusive(tmp_path):
    path = _write(
        tmp_path,
        {
            "id": "both",
            "version": 1,
            "description": "ambiguous",
            "command": "SET UP MENU",
            "params": {"alpha": "x"},
            "raw_tlv_hex": "D009810301250082028182",
        },
    )
    with pytest.raises(StimulusError, match="mutually exclusive"):
        Stimulus.load(path)


def test_mutation_offset_bounds(tmp_path):
    path = _write(
        tmp_path,
        {
            "id": "oob",
            "version": 1,
            "description": "mutation beyond the buffer",
            "command": "SET UP MENU",
            "params": {"alpha": "x"},
            "mutations": [{"offset": 999, "hex": "00"}],
        },
    )
    with pytest.raises(StimulusError, match="outside"):
        Stimulus.load(path)


def test_naive_allowlist_semantics():
    assert allow.is_allowed(0x25)
    assert not allow.is_allowed(0x13)
    assert not allow.is_allowed(0x40)
    assert not allow.is_allowed(0x77)  # unknown is not allowed
    assert allow.name_of(0x26) == "PROVIDE LOCAL INFORMATION"
