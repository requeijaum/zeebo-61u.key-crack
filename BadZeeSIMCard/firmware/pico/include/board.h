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

/* ATR offered to the terminal. Configuration, not code (SYS-F-001).
 *
 * TA1 = 0x11 declares Fi = 372, Di = 1 — exactly the timing assumption the PHY
 * makes (ETU = 372 / f). Declaring a different Fi/Di here is how an instrument
 * ends up talking at the wrong bit rate while looking correct on paper.
 * No TD1 byte: protocol T=0 is the default. Historical bytes are the identity. */
#define BZ_ATR_BYTES                                                             \
    { 0x3B, 0x9E, 0x11, 'B', 'A', 'D', 'Z', 'E', 'E', 'S', 'I', 'M', 'C', 'A',   \
      'R', 'D', ' ' }

/* Firmware identity reported in HELLO_ACK (SYS-I-003, run pinning). */
#ifndef BZ_FW_HASH
#define BZ_FW_HASH "dev"
#endif

#endif /* BZ_BOARD_H */
