#!/usr/bin/env bash
# Build the Pico firmware. Clones the SDK on first use (pinned tag).
set -euo pipefail

SDK_TAG="${SDK_TAG:-2.1.1}"
: "${PICO_SDK_PATH:=$HOME/pico-sdk}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"

if [ ! -d "$PICO_SDK_PATH" ]; then
    echo "cloning pico-sdk $SDK_TAG into $PICO_SDK_PATH"
    git clone --depth 1 --branch "$SDK_TAG" https://github.com/raspberrypi/pico-sdk "$PICO_SDK_PATH"
    git -C "$PICO_SDK_PATH" submodule update --init
fi

export PICO_SDK_PATH
cmake -S "$HERE/firmware/pico" -B "$HERE/firmware/pico/build" -DPICO_BOARD="${PICO_BOARD:-pico}"
cmake --build "$HERE/firmware/pico/build" -j"$(nproc 2>/dev/null || echo 2)"

echo
echo "firmware: $HERE/firmware/pico/build/badzeesim.uf2"
echo "flash:    hold BOOTSEL, plug USB, copy the UF2 to the RPI-RP2 volume"
