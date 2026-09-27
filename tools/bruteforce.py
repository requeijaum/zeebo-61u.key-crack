#!/usr/bin/env python3
"""Hypothesis testing harness for 61u.key generation.

Each hypothesis is a function mapping an input string -> 14-char key.
A hypothesis scores matches/total against known IMEI->Key pairs.

Usage:
    python3 tools/bruteforce.py data/spreadsheet.csv
    python3 tools/bruteforce.py data/spreadsheet.csv --input serial
    python3 tools/bruteforce.py data/spreadsheet.csv --secrets mysecrets.txt

Important: with only ~10 known pairs, a match is a lead, not proof.
Any hypothesis that matches all pairs on the training set must be
re-validated against fresh pairs before trusting it.

Hypothesis registry (priority order from PLAN.md):
    batch_exact   - lookup by exact IMEI (documents the duplicate-key anomaly)
    hmac_sha1     - HMAC-SHA1(input, secret), base64 -> alnum, [:14]
    sha1_salt     - SHA1(input + salt), base64 -> alnum, [:14]
    crc_prefix    - CRC32(input) rendered into key positions (structure probe)
"""

import argparse
import base64
import csv
import hashlib
import hmac
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stats import load_pairs  # noqa: E402

VALID_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")

DEFAULT_SECRETS = [
    b"",
    b"\x00" * 20,
    b"\xff" * 20,
    b"QUALCOMM",
    b"TecToy",
    b"TECTOY",
    b"tectoy",
    b"Zeebo",
    b"ZEEBO",
    b"zeebo",
    b"BREW",
    b"brew",
    b"Longcheer",
    b"LCT",
    b"61u",
    b"12345678901234567890",
]


def _b64_alnum14(raw: bytes) -> str:
    b64 = base64.b64encode(raw).decode()
    alnum = "".join(c for c in b64 if c in VALID_CHARS)
    return alnum[:14].ljust(14, "A")


def h_hmac_sha1(inp: str, secret: bytes) -> str:
    return _b64_alnum14(hmac.new(secret, inp.encode(), hashlib.sha1).digest())


def h_sha1_salt(inp: str, salt: bytes) -> str:
    return _b64_alnum14(hashlib.sha1(inp.encode() + salt).digest())


def h_crc_prefix(inp: str) -> str:
    """Structure probe: is CRC32(input) embedded anywhere in the key?"""
    crc = f"{zlib.crc32(inp.encode()) & 0xFFFFFFFF:08x}"
    return crc + "A" * 6


def score(fn, pairs, field=0, **kwargs):
    """Return (matches, total, mismatches). field: 0=IMEI, 1=serial."""
    mism = []
    for entry in pairs:
        if fn(entry[field], **kwargs) != entry[4]:
            mism.append(entry[field])
    total = len(pairs)
    return total - len(mism), total, mism


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("csv", help="spreadsheet CSV")
    ap.add_argument("--input", choices=["imei", "serial"], default="imei",
                    help="which console identifier feeds the hypothesis")
    ap.add_argument("--secrets", help="file with extra secrets (one per line)")
    args = ap.parse_args()

    pairs = load_pairs(args.csv)
    print(f"Loaded {len(pairs)} pairs (input field: {args.input})")
    field = 0 if args.input == "imei" else 1

    # 1. Memorization baseline (proves nothing -- just sizes the anomaly).
    # An exact input->key map trivially scores 10/10 because all inputs are
    # distinct; the anomaly is the reverse direction (1 key <- 2 IMEIs).
    n_inputs = len({e[field] for e in pairs})
    print(f"memorize ({args.input}): {len(pairs)}/{len(pairs)} trivial "
          f"({n_inputs} distinct inputs; proves nothing)")

    # 2. HMAC-SHA1 with candidate secrets.
    secrets = list(DEFAULT_SECRETS)
    if args.secrets:
        for line in Path(args.secrets).read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                secrets.append(line.encode())
    best = []
    for secret in secrets:
        m, t, _ = score(h_hmac_sha1, pairs, field, secret=secret)
        if m > 0:
            best.append((m, secret))
            print(f"hmac_sha1 secret={secret[:24]!r}: {m}/{t}")
    if not best:
        print("hmac_sha1: 0 matches for all tried secrets")

    # 3. SHA1(input+salt) over short salts (tunable search space).
    found = False
    for salt in (b"\x00", b"\xff", b"\xaa", b"\x55", b"0", b"61", b"61u"):
        m, t, _ = score(h_sha1_salt, pairs, field, salt=salt)
        if m > 0:
            print(f"sha1_salt salt={salt!r}: {m}/{t}")
            found = True
    if not found:
        print("sha1_salt: 0 matches for tried 1-2 byte salts")

    # 4. CRC32 structure probe (substring match, not equality).
    crc_hits = 0
    for entry in pairs:
        crc = f"{zlib.crc32(entry[field].encode()) & 0xFFFFFFFF:08x}"
        if crc[:4].lower() in entry[4].lower() or crc[4:].lower() in entry[4].lower():
            crc_hits += 1
            print(f"crc_probe: {entry[field]} crc={crc} key={entry[4]} (partial hit)")
    if not crc_hits:
        print("crc_probe: no CRC32 substrings found in keys")


if __name__ == "__main__":
    main()
