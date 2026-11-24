import pytest

from bzsim.frame import CRC, HEADER, MAGIC, Frame, FrameError, MsgType, crc16_ccitt_false


def test_crc_check_value():
    # CRC-16/CCITT-FALSE("123456789") == 0x29B1
    assert crc16_ccitt_false(b"123456789") == 0x29B1


def test_roundtrip():
    original = Frame(MsgType.ARM, b'{"stimulus":"menu-basic"}')
    decoded = Frame.decode(original.encode())
    assert decoded.type is MsgType.ARM
    assert decoded.payload == b'{"stimulus":"menu-basic"}'


def test_frame_layout():
    blob = Frame(MsgType.HELLO, b"\x01").encode()
    magic, version, mtype, length = HEADER.unpack_from(blob, 0)
    assert magic == MAGIC
    assert version == 1
    assert mtype == int(MsgType.HELLO)
    assert length == 1
    assert len(blob) == HEADER.size + 1 + CRC.size


def test_bad_magic():
    blob = bytearray(Frame(MsgType.STOP).encode())
    blob[0] = 0x00
    with pytest.raises(FrameError, match="magic"):
        Frame.decode(bytes(blob))


def test_bad_version():
    blob = bytearray(Frame(MsgType.STOP).encode())
    blob[1] = 9
    with pytest.raises(FrameError, match="version"):
        Frame.decode(bytes(blob))


def test_crc_mismatch():
    blob = bytearray(Frame(MsgType.LOG, b"hello").encode())
    blob[HEADER.size] ^= 0xFF
    with pytest.raises(FrameError, match="crc"):
        Frame.decode(bytes(blob))


def test_truncated():
    blob = Frame(MsgType.LOG, b"hello").encode()
    with pytest.raises(FrameError):
        Frame.decode(blob[:-1])


def test_stream_partial():
    a = Frame(MsgType.STATUS, b"a").encode()
    b = Frame(MsgType.LOG, b"bb").encode()
    frames, rest = Frame.decode_stream(a + b)
    assert [f.type for f in frames] == [MsgType.STATUS, MsgType.LOG]
    assert rest == b""

    frames, rest = Frame.decode_stream(a + b[:-2])
    assert len(frames) == 1
    assert rest == b[:-2]


def test_payload_limit():
    with pytest.raises(FrameError):
        Frame(MsgType.LOG, b"x" * 5000).encode()
