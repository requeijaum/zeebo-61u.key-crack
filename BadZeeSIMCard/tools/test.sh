#!/usr/bin/env bash
# Everything that can be verified without hardware. Used as the pre-flight check.
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"

echo "== native core tests (ASan/UBSan, -Werror) =="
cmake -S "$HERE/firmware/core" -B "$HERE/firmware/core/build" -DCMAKE_BUILD_TYPE=Debug >/dev/null
cmake --build "$HERE/firmware/core/build" >/dev/null
"$HERE/firmware/core/build/bz_tests"

echo
echo "== host tests =="
(cd "$HERE/host" && python3 -m pytest)

echo
echo "== stimulus gate =="
(cd "$HERE/host" && python3 -m bzsim stimuli ../stimuli)
