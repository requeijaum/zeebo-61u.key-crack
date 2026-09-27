#!/usr/bin/env python3
"""61u.key generator (STUB -- algorithm not yet cracked).

Success criteria (PLAN.md): gen_61u.py <imei> outputs the valid 14-char key
for ALL known pairs. We are not there yet.

Current status:
  - 10 known pairs, 1 duplicate key (3ulp223EpFKhDT for 2 IMEIs).
  - Batch/lot hypothesis FALSIFIED at 2-char unit-prefix granularity:
    units 24xx share prefix but have different keys; same for 18xx.
  - No HMAC-SHA1 / SHA1-salt match with tried secrets (see bruteforce.py).
  - Duplicate may be a spreadsheet error (Moon Sarito), so it must not be
    used to confirm any hypothesis -- only fresh pairs can confirm.

This stub exists so the CLI contract is fixed. It refuses to guess.
"""

import sys

VALID_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")


def generate_key(imei: str) -> str:
    raise NotImplementedError(
        "keygen algorithm unknown: no hypothesis validates against "
        "independent pairs yet. See tools/bruteforce.py and re/notes.md."
    )


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <imei>", file=sys.stderr)
        sys.exit(2)
    imei = sys.argv[1].strip()
    if not (imei.isdigit() and 14 <= len(imei) <= 16):
        print(f"Invalid IMEI: {imei!r} (expect 14-16 digits)", file=sys.stderr)
        sys.exit(2)
    try:
        print(generate_key(imei))
    except NotImplementedError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
