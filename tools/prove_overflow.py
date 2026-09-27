#!/usr/bin/env python3
"""Prove the unbounded-copy primitive with the firmware's own bytes.

Emulates (Unicorn, Thumb):
  1. FUN_101d7f48 (strcat dst,src) — the 101d7f48 bytes from 1.1.2_APPS.bin
  2. FUN_1079bff4 (word-at-a-time strcpy) — same source

Setup per test: 128B stack buffer (like auStack_148) + canary past it.
Input: 200-char LFN-style name. Verdict: canary intact or smashed.

This proves the MECHANISM (unbounded copy into fixed stack buffer) using
the target's own machine code. It does NOT prove the trigger (whether a
long SD-derived name reaches these functions) — see re/notes.md section 20.

Usage: python3 tools/prove_overflow.py
Requires: unicorn 2.x (pip), firmware/1.1.2_APPS.bin
"""

import struct
import sys

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC

BIN = "firmware/1.1.2_APPS.bin"
BASE_V = 0x1013a000
BASE_OFF = 0x76000

# file offsets (vaddr - BASE_V + BASE_OFF)
STRCAT_OFF = 0x101d7f48 - BASE_V + BASE_OFF
STRCPY_OFF = 0x1079bff4 - BASE_V + BASE_OFF

CODE_BASE = 0x10000
STACK_BASE = 0x20000
STACK_SIZE = 0x2000


def load_code(mu, off, size=0x80):
    data = open(BIN, "rb").read()
    blob = data[off:off + size]
    mu.mem_map(CODE_BASE, 0x1000)
    mu.mem_write(CODE_BASE, blob)
    return blob


def run_func(off, dst_off, src: bytes, name: str):
    mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    blob = load_code(mu, off)
    mu.mem_map(STACK_BASE, STACK_SIZE)
    mu.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)
    dst = STACK_BASE + 0x100
    mu.mem_write(dst, b"fs:/card0/mod/\x00")  # realistic prefix
    mu.mem_write(dst + 0x200, src + b"\x00")
    canary_addr = dst + 128
    mu.mem_write(canary_addr, b"CANARY!!")
    mu.reg_write(UC_ARM_REG_R0, dst)
    mu.reg_write(UC_ARM_REG_R1, dst + 0x200)
    mu.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 4)
    mu.reg_write(UC_ARM_REG_LR, CODE_BASE + 0x500 | 1)
    try:
        mu.emu_start(CODE_BASE | 1, CODE_BASE + len(blob), timeout=2 * 10**6)
    except Exception as e:  # noqa: BLE001 - overrun means smash, report below
        print(f"  [{name}] emu exception (often = wild copy): {e}")
    canary = bytes(mu.mem_read(canary_addr, 8))
    # find how far past 128 the input reached
    region = bytes(mu.mem_read(dst, 320))
    try:
        reach = region.index(b"\x00", 128)
    except ValueError:
        reach = 320
    smashed = canary != b"CANARY!!"
    print(f"  [{name}] input={len(src)}B canary={'SMASHED' if smashed else 'intact'} "
          f"bytes-past-128-zone={max(0, reach - 128)}")
    return smashed


def main():
    long_name = b"A" * 200  # FAT LFN-style attacker name
    print("Proving unbounded-copy primitive (firmware bytes, Unicorn Thumb):")
    r1 = run_func(STRCAT_OFF, 0, long_name, "strcat-101d7f48")
    r2 = run_func(STRCPY_OFF, 0, long_name, "strcpy-1079bff4")
    # sanity: short input must NOT smash
    r3 = run_func(STRCAT_OFF, 0, b"game1234", "strcat-short")
    if r1 and r2 and not r3:
        print("PRIMITIVE CONFIRMED: long input smashes past 128B, short does not.")
        return 0
    print("INCONCLUSIVE (check harness)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
