"""Command line for the host side (no hardware required).

    python -m bzsim tlv ../../stimuli/menu-basic.json     # bytes + hash
    python -m bzsim verify ../../stimuli/menu-basic.json  # allowlist gate only
    python -m bzsim stimuli ../../stimuli                 # list and check a directory
    python -m bzsim hello                                 # the HELLO frame, hex
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .frame import Frame, FrameError, MsgType
from .runlog import CLASSES, RunRecord
from .stimulus import Stimulus, StimulusError


def cmd_tlv(args: argparse.Namespace) -> int:
    st = Stimulus.load(args.path)
    tlv = st.tlv()
    print(f"id        {st.id} v{st.version}")
    print(f"hash      {st.digest()}")
    print(f"length    {len(tlv)}")
    print(f"tlv       {tlv.hex(' ').upper()}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    try:
        st = Stimulus.load(args.path)
    except (StimulusError, KeyError) as exc:
        print(f"REJECTED  {exc}")
        return 1
    print(f"OK        {st.id} v{st.version} command={st.command} hash={st.digest()}")
    return 0


def cmd_stimuli(args: argparse.Namespace) -> int:
    root = Path(args.dir)
    files = sorted(root.glob("*.json"))
    bad = 0
    for path in files:
        try:
            st = Stimulus.load(path)
            print(f"OK        {path.name:24s} {st.command:26s} {st.digest()}")
        except (StimulusError, KeyError, ValueError) as exc:
            bad += 1
            print(f"REJECTED  {path.name:24s} {exc}")
    print(f"{len(files)} stimuli, {bad} rejected")
    return 1 if bad else 0


def cmd_hello(args: argparse.Namespace) -> int:
    frame = Frame(MsgType.HELLO, bytes([1]))
    print(frame.encode().hex(" ").upper())
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    rec = RunRecord.from_json(Path(args.path).read_text())
    errors = rec.validity_errors()
    if rec.classification and rec.classification not in CLASSES:
        errors.append(f"classification {rec.classification!r} is not one of {CLASSES}")
    if errors:
        print(f"INVALID   {rec.run_id}")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"VALID     {rec.run_id} classification={rec.classification}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bzsim", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("tlv", help="encode a stimulus and print its bytes")
    p.add_argument("path")
    p.set_defaults(func=cmd_tlv)

    p = sub.add_parser("verify", help="check a stimulus against the allowlist")
    p.add_argument("path")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("stimuli", help="check every stimulus in a directory")
    p.add_argument("dir")
    p.set_defaults(func=cmd_stimuli)

    p = sub.add_parser("hello", help="print the HELLO frame")
    p.set_defaults(func=cmd_hello)

    p = sub.add_parser("run", help="validate a run record")
    p.add_argument("path")
    p.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FrameError, StimulusError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
