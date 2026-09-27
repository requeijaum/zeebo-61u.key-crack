#!/usr/bin/env python3
"""Statistical analysis of IMEI -> 61u.key pairs.

Usage:
    python3 tools/stats.py data/spreadsheet.csv
    python3 tools/stats.py data/spreadsheet.csv --serials  # include serial breakdown

Reads the OpenZeebo spreadsheet CSV (IMEI,Serial,Region,Version,Key).
With n=10 the statistics are descriptive only -- nothing here can prove the
keygen algorithm. The main value is falsifying hypotheses (e.g. batch-based).
"""

import csv
import math
import sys
from collections import Counter, defaultdict

VALID_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")


def load_pairs(csv_path):
    """Return list of (imei, serial, region, version, key)."""
    pairs = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # header
        for row in reader:
            if len(row) >= 5 and row[0].strip() and row[4].strip():
                imei = row[0].strip()
                if not (imei.isdigit() and len(imei) >= 14):
                    print(f"  skip malformed row: {row}", file=sys.stderr)
                    continue
                pairs.append((
                    imei,
                    row[1].strip(),
                    row[2].strip() if len(row) > 2 else "",
                    row[3].strip() if len(row) > 3 else "",
                    row[4].strip(),
                ))
    return pairs


def shannon_entropy(s):
    freq = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def char_class(c):
    if c.isupper():
        return "upper"
    if c.islower():
        return "lower"
    return "digit"


def analyze_keys(keys):
    all_chars = "".join(keys)
    print(f"Sample size: {len(keys)} keys x 14 chars = {len(all_chars)} chars")
    print(f"Unique alphabet symbols used: {len(set(all_chars))}/62")
    print(f"Mean per-key Shannon entropy: "
          f"{sum(shannon_entropy(k) for k in keys) / len(keys):.2f} bits/char "
          f"(max for 14 unique chars = {math.log2(14):.2f})")

    cls = Counter(char_class(c) for c in all_chars)
    print(f"Char classes overall: {dict(cls)}")

    print("\nPer-position analysis (pos: top chars, class mix):")
    for i in range(14):
        col = [k[i] for k in keys if len(k) == 14]
        cmix = Counter(char_class(c) for c in col)
        top = Counter(col).most_common(3)
        print(f"  pos {i:2d}: top={top} classes={dict(cmix)}")


def analyze_batch(pairs, show_serials=False):
    key_to_entries = defaultdict(list)
    for imei, serial, region, ver, key in pairs:
        key_to_entries[key].append((imei, serial, region, ver))

    print(f"\nTotal pairs: {len(pairs)}")
    print(f"Unique keys: {len(key_to_entries)}")
    dups = {k: v for k, v in key_to_entries.items() if len(v) > 1}
    print(f"Duplicate keys: {len(dups)}")
    for key, entries in dups.items():
        print(f"  Key {key}: {len(entries)} IMEIs:")
        for imei, serial, region, ver in entries:
            print(f"    IMEI={imei} serial={serial} region={region} ver={ver}")

    # Falsification check: group by serial-batch prefix, expect same key
    # if the key were batch-derived. Serial layout (observed, n=10):
    #   [0:5] plant code (BQAAF=BR, SQAAF=MX) | [5:16] batch (e.g. 0150B215810)
    #   [16:] 7-digit unit sequence (e.g. 2402209)
    print("\nBatch-prefix consistency check (2-char unit prefix -> keys):")
    prefix_to_keys = defaultdict(set)
    for imei, serial, region, ver, key in pairs:
        prefix_to_keys[serial[16:18] if len(serial) >= 18 else "?"].add(key)
    for prefix in sorted(prefix_to_keys):
        keys = prefix_to_keys[prefix]
        verdict = "CONSISTENT (1 key)" if len(keys) == 1 else \
            f"INCONSISTENT ({len(keys)} keys -> batch hypothesis fails at this granularity)"
        print(f"  unit prefix {prefix!r}: {sorted(keys)} -- {verdict}")

    if show_serials:
        print("\nSerial breakdown (hypothesized layout):")
        for imei, serial, region, ver, key in pairs:
            print(f"  {serial} plant={serial[:5]} batch={serial[5:16]} "
                  f"unit={serial[16:]} imei_snr={imei[8:14]} key={key}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    pairs = load_pairs(sys.argv[1])
    print(f"Loaded {len(pairs)} IMEI->Key pairs from {sys.argv[1]}")
    keys = [k for _, _, _, _, k in pairs]
    bad = [k for k in keys if len(k) != 14 or set(k) - VALID_CHARS]
    if bad:
        print(f"WARNING: {len(bad)} keys fail format check: {bad}", file=sys.stderr)
    analyze_keys(keys)
    analyze_batch(pairs, show_serials="--serials" in sys.argv)


if __name__ == "__main__":
    main()
