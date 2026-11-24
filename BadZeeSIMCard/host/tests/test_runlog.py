import pytest

from bzsim.runlog import CLASSES, Protocol, RunRecord, classify


def good(**over):
    base = dict(
        run_id="2026-11-24T14-02-11Z-a3f2",
        stimulus="menu-basic",
        stimulus_hash="1a2b3c4d",
        firmware="deadbeef",
        console_model="Zeebo",
        console_fw="1.1.2",
        cold_start=True,
        card_original_present=False,
        drops=0,
        protocol=Protocol(cls="B", clock_hz=3570000, t=0),
        usb_pre="pre.txt",
        usb_post="post.txt",
        classification="menu",
    )
    base.update(over)
    return RunRecord(**base)


def test_good_run_is_valid():
    rec = good()
    assert rec.validity_errors() == []
    assert rec.valid


@pytest.mark.parametrize(
    "field,value,needle",
    [
        ("stimulus_hash", "", "rule 1"),
        ("firmware", "", "rule 1"),
        ("drops", 3, "rule 2"),
        ("usb_pre", "", "rule 3"),
        ("cold_start", False, "rule 4"),
        ("card_original_present", True, "rule 5"),
    ],
)
def test_each_rule_can_fail(field, value, needle):
    rec = good(**{field: value})
    errors = rec.validity_errors()
    assert errors and needle in errors[0]
    assert not rec.valid


def test_json_roundtrip():
    rec = good()
    again = RunRecord.from_json(rec.to_json())
    assert again == rec
    assert again.protocol.cls == "B"


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        # card session never produced a proactive exchange
        (dict(saw_profile=False, response_ok=False, menu_on_screen=False, gap_s=5,
              answered_after_gap=True), "no-menu"),
        # the command ran and the menu was seen
        (dict(saw_profile=True, response_ok=True, menu_on_screen=True, gap_s=1,
              answered_after_gap=True), "menu"),
        # console restarted on its own
        (dict(saw_profile=True, response_ok=False, menu_on_screen=False, gap_s=0,
              answered_after_gap=True, rebooted=True), "reboot"),
        # stopped answering, screen normal -> hang
        (dict(saw_profile=True, response_ok=False, menu_on_screen=False, gap_s=45,
              answered_after_gap=False, screen_fault=False), "hang"),
        # stopped answering, screen faulted -> crash
        (dict(saw_profile=True, response_ok=False, menu_on_screen=False, gap_s=45,
              answered_after_gap=False, screen_fault=True), "crash"),
        # still talking after a long pause: nothing happened
        (dict(saw_profile=True, response_ok=False, menu_on_screen=False, gap_s=45,
              answered_after_gap=True), "silent-continue"),
        # short pause, still talking
        (dict(saw_profile=True, response_ok=False, menu_on_screen=False, gap_s=3,
              answered_after_gap=True), "silent-continue"),
    ],
)
def test_classification(kwargs, expected):
    result = classify(**kwargs)
    assert result == expected
    assert result in CLASSES
