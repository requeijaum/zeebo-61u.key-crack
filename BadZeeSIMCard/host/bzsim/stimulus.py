"""Stimuli: load, validate, hash and encode.

A stimulus is data (stimuli/schema.md). The encoder here mirrors the firmware
builder on purpose: if the two disagree, the cross-check test fails before a run
is wasted on the bench.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from . import allow


class StimulusError(ValueError):
    """A stimulus that must not be armed."""


@dataclass
class Stimulus:
    id: str
    version: int
    description: str
    command: str
    params: dict = field(default_factory=dict)
    raw_tlv_hex: str | None = None
    mutations: list[dict] = field(default_factory=list)
    expect: dict = field(default_factory=dict)
    notes: str = ""

    # ------------------------------------------------------------------ io --

    @classmethod
    def load(cls, path: str | Path) -> "Stimulus":
        data = json.loads(Path(path).read_text())
        st = cls(
            id=data["id"],
            version=int(data["version"]),
            description=data.get("description", ""),
            command=data.get("command", "").replace("_", " "),
            params=data.get("params", {}),
            raw_tlv_hex=data.get("raw_tlv_hex"),
            mutations=data.get("mutations", []),
            expect=data.get("expect", {}),
            notes=data.get("notes", ""),
        )
        st.validate()
        return st

    # ------------------------------------------------------------ validate --

    def validate(self) -> None:
        if not self.id:
            raise StimulusError("missing id")
        if self.version < 1:
            raise StimulusError(f"{self.id}: version must be >= 1")

        tlv = self.tlv()
        if len(tlv) < 6 or tlv[0] != 0xD0:
            raise StimulusError(f"{self.id}: not a D0 template")
        code = tlv[5]  # D0 len 81 03 number type qualifier
        if not allow.is_allowed(code):
            raise StimulusError(
                f"{self.id}: command 0x{code:02X} ({allow.name_of(code)}) is not on the allowlist"
            )
        if self.raw_tlv_hex and self.params:
            raise StimulusError(f"{self.id}: raw_tlv_hex and params are mutually exclusive")
        for mut in self.mutations:
            off = int(mut.get("offset", -1))
            if off < 0 or off >= len(tlv):
                raise StimulusError(f"{self.id}: mutation offset {off} outside the TLV")

    # ------------------------------------------------------------- encoding --

    def tlv(self) -> bytes:
        """The bytes the instrument will arm (mutations applied)."""
        if self.raw_tlv_hex:
            body = bytes.fromhex(self.raw_tlv_hex)
        else:
            body = self._encode()
        return self._apply_mutations(body)

    def _encode(self) -> bytes:
        code = allow.BY_NAME.get(self.command.replace("_", " "))
        if code is None:
            raise StimulusError(
                f"{self.id}: unknown command name {self.command!r} (use the spec name, e.g. SET UP MENU)"
            )

        number = int(self.params.get("number", 1)) & 0xFF
        qualifier = int(self.params.get("qualifier", 0)) & 0xFF
        inner = _tlv(0x81, bytes([number, code, qualifier])) + _tlv(0x82, b"\x81\x82")

        alpha = self.params.get("alpha") or self.params.get("title")
        if alpha:
            inner += _tlv(0x85, str(alpha).encode())

        for item in self.params.get("items", []):
            item_id = int(item.get("index", item.get("id", 0))) & 0xFF
            inner += _tlv(0x8F, bytes([item_id]) + str(item.get("text", "")).encode())

        text = self.params.get("text")
        if text:
            inner += _tlv(0x8D, b"\x04" + str(text).encode())

        if "response_length" in self.params:
            rl = self.params["response_length"]
            inner += _tlv(0x91, bytes([int(rl.get("min", 0)), int(rl.get("max", 0))]))

        return _tlv(0xD0, inner)

    def _apply_mutations(self, buf: bytes) -> bytes:
        out = bytearray(buf)
        for mut in self.mutations:
            off = int(mut["offset"])
            if "hex" in mut:
                repl = bytes.fromhex(mut["hex"])
                out[off:off + len(repl)] = repl
            if "length" in mut:
                out = out[: int(mut["length"])]
        return bytes(out)

    # --------------------------------------------------------------- identity --

    def canonical(self) -> bytes:
        blob = {
            "id": self.id,
            "version": self.version,
            "command": self.command,
            "params": self.params,
            "raw_tlv_hex": self.raw_tlv_hex,
            "mutations": self.mutations,
        }
        return json.dumps(blob, sort_keys=True, separators=(",", ":")).encode()

    def digest(self) -> str:
        return hashlib.sha256(self.canonical()).hexdigest()[:16]


def _tlv(tag: int, value: bytes) -> bytes:
    if len(value) > 255:
        raise StimulusError(f"value too long for tag 0x{tag:02X}: {len(value)}")
    return bytes([tag, len(value)]) + value
