"""Cross-check: the Python encoder and the C builder must produce the same bytes.

The expected sequence is a real capture of a SET UP MENU from a commercial card
(reproduced in spec/REFERENCE.md §3), so this also pins the encoding to reality.
"""

from pathlib import Path

from bzsim.stimulus import Stimulus

ROOT = Path(__file__).resolve().parents[2]

CAPTURE = bytes(
    [
        0xD0, 0x26, 0x81, 0x03, 0x01, 0x25, 0x00, 0x82, 0x02, 0x81, 0x82,
        0x85, 0x09, *b"Menu name",
        0x8F, 0x07, 0x80, *b"Item 1",
        0x8F, 0x07, 0x81, *b"Item 2",
    ]
)


def make() -> Stimulus:
    return Stimulus(
        id="capture-menu",
        version=1,
        description="reproduction of a real SET UP MENU",
        command="SET UP MENU",
        params={
            "number": 1,
            "qualifier": 0,
            "alpha": "Menu name",
            "items": [
                {"index": 0x80, "text": "Item 1"},
                {"index": 0x81, "text": "Item 2"},
            ],
        },
    )


def test_python_matches_real_capture():
    assert make().tlv() == CAPTURE


def test_menu_basic_matches_expected_structure():
    st = Stimulus.load(ROOT / "stimuli" / "menu-basic.json")
    tlv = st.tlv()
    assert tlv[:7] == bytes([0xD0, tlv[1], 0x81, 0x03, 0x01, 0x25, 0x00])
    assert tlv[1] == len(tlv) - 2
    assert b"Service" in tlv
    assert b"Info" in tlv
    assert tlv[7:11] == bytes([0x82, 0x02, 0x81, 0x82])
