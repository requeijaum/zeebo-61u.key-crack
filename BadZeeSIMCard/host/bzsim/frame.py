"""Framing for the host <-> instrument control channel.

Frame (INTERFACES.md §5):

    0x5A | version | type | length (u16 LE) | payload | crc16(payload) (u16 LE)

The magic byte is a delimiter, not a security control. The CRC covers the payload
only, so a corrupted length field is caught by the bounds check, not the CRC.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum

MAGIC = 0x5A
VERSION = 1
HEADER = struct.Struct("<BBBH")
CRC = struct.Struct("<H")
MAX_PAYLOAD = 4096


class FrameError(ValueError):
    """Raised when a buffer is not a valid frame."""


class MsgType(IntEnum):
    HELLO = 1
    HELLO_ACK = 2
    ARM = 3
    STATUS = 4
    LOG = 5
    RESULT = 6
    STOP = 7
    ERROR = 8


def crc16_ccitt_false(data: bytes) -> int:
    """CRC-16/CCITT-FALSE, same polynomial as the firmware core."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


@dataclass(frozen=True)
class Frame:
    type: MsgType
    payload: bytes = b""
    version: int = VERSION

    def encode(self) -> bytes:
        if len(self.payload) > MAX_PAYLOAD:
            raise FrameError(f"payload too large: {len(self.payload)}")
        head = HEADER.pack(MAGIC, self.version, int(self.type), len(self.payload))
        return head + self.payload + CRC.pack(crc16_ccitt_false(self.payload))

    @classmethod
    def decode(cls, buf: bytes) -> Frame:
        if len(buf) < HEADER.size + CRC.size:
            raise FrameError("short buffer")
        magic, version, mtype, length = HEADER.unpack_from(buf, 0)
        if magic != MAGIC:
            raise FrameError(f"bad magic 0x{magic:02X}")
        if version != VERSION:
            raise FrameError(f"unsupported version {version}")
        if length > MAX_PAYLOAD:
            raise FrameError(f"length out of range: {length}")
        end = HEADER.size + length
        if len(buf) < end + CRC.size:
            raise FrameError("truncated payload")
        payload = buf[HEADER.size:end]
        (got_crc,) = CRC.unpack_from(buf, end)
        if got_crc != crc16_ccitt_false(payload):
            raise FrameError("crc mismatch")
        try:
            msg = MsgType(mtype)
        except ValueError as exc:
            raise FrameError(f"unknown type {mtype}") from exc
        return cls(type=msg, payload=payload, version=version)

    @classmethod
    def decode_stream(cls, buf: bytes) -> tuple[list[Frame], bytes]:
        """Decode as many frames as possible; return them and the leftover bytes."""
        frames: list[Frame] = []
        while True:
            if len(buf) < HEADER.size + CRC.size:
                return frames, buf
            magic = buf[0]
            if magic != MAGIC:
                raise FrameError(f"bad magic 0x{magic:02X}")
            _, _, _, length = HEADER.unpack_from(buf, 0)
            total = HEADER.size + length + CRC.size
            if len(buf) < total:
                return frames, buf
            frames.append(Frame.decode(buf[:total]))
            buf = buf[total:]
