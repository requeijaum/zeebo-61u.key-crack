/*
 * board.h — wiring and configuration for the Pico side.
 *
 * The instrument is powered from its own USB; the card VCC contact is only
 * sensed (HAZARDS.md H-02). Do not connect VCC to the Pico's supply.
 */
#ifndef BZ_BOARD_H
#define BZ_BOARD_H

/* GPIOs. I/O is half-duplex: driven for transmit, released (pull-up) for receive. */
#define BZ_PIN_CLK 2
#define BZ_PIN_RST 3
#define BZ_PIN_IO  4
#define BZ_PIN_VCC_SENSE 5

/* Fallback ETU when CLK cannot be measured (372 / 3.57 MHz). */
#define BZ_ETU_DEFAULT_US 104u

/* ATR offered to the terminal. Configuration, not code (SYS-F-001):
 * direct convention, TA1 present, T=0 offered. Adjust at G0 against the
 * terminal's card-init behaviour; a change here is a configuration version. */
#define BZ_ATR_BYTES                                                             \
    { 0x3B, 0x9F, 0x96, 0x80, 0x1F, 0xC7, 0x80, 0x31, 0xE0, 0x73, 0xFE,         \
      0x21, 0x1B, 0x67, 0x4A, 0x4C, 0x75, 0x30, 0x34, 0x05, 0x4B }

/* Firmware identity reported in HELLO_ACK (SYS-I-003, run pinning). */
#ifndef BZ_FW_HASH
#define BZ_FW_HASH "dev"
#endif

#endif /* BZ_BOARD_H */
