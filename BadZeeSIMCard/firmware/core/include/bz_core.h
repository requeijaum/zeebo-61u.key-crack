/*
 * bz_core.h — portable core of the BadZeeSIMCard instrument.
 *
 * No SDK, no hardware, no allocation. Everything here compiles for the host and
 * is unit-tested natively (firmware/core/tests), which is the only way to trust
 * code that will later run on a wire with a 74 µs timing budget.
 *
 * Spec references: BadZeeSIMCard/spec/REFERENCE.md
 */
#ifndef BZ_CORE_H
#define BZ_CORE_H

#include <stddef.h>
#include <stdint.h>

/* ---------------------------------------------------------------- CRC-16 ---- */

/* CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF. Used by the host link frame. */
uint16_t bz_crc16(const uint8_t *data, size_t len);

/* ------------------------------------------------------------------ TLV ----- */

#define BZ_TLV_MAX_DEPTH 6

typedef struct {
    uint8_t *buf;
    size_t cap;
    size_t len;
    size_t stack[BZ_TLV_MAX_DEPTH];
    int depth;
    int err;
} bz_tlv;

void bz_tlv_init(bz_tlv *t, uint8_t *buf, size_t cap);
int bz_tlv_ok(const bz_tlv *t);

/* Append tag/len/value. len <= 255 (short form only). */
int bz_tlv_put(bz_tlv *t, uint8_t tag, const void *val, size_t len);
int bz_tlv_u8(bz_tlv *t, uint8_t tag, uint8_t v);

/* Text with an 8-bit default alphabet (no coding byte) — used for alpha
 * identifiers and item texts, matching real captures (spec/REFERENCE.md §3). */
int bz_tlv_text(bz_tlv *t, uint8_t tag, const char *ascii);

/* Text string with the 0x04 coding byte (8-bit default alphabet). */
int bz_tlv_text_dcs(bz_tlv *t, uint8_t tag, const char *ascii);

/* Open/close a constructed TLV with length back-patched on close. */
int bz_tlv_begin(bz_tlv *t, uint8_t tag);
int bz_tlv_end(bz_tlv *t);

/* ----------------------------------------------------------------- APDU ----- */

#define BZ_SW_OK          0x9000u
#define BZ_SW_INS_UNKNOWN 0x6D00u
#define BZ_SW_WRONG_LEN   0x6700u
#define BZ_SW_NO_EF       0x6A82u

typedef struct {
    uint8_t cla, ins, p1, p2;
    const uint8_t *data; /* NULL when lc == 0 */
    size_t lc;
    int has_le;
    uint8_t le;
    int p3_zero;   /* P3 == 00: Le encoded as 256 (ISO 7816-3) */
    int malformed; /* Lc declared larger than the bytes present */
} bz_apdu;

/* Returns 1 on a parseable header (even if malformed data), 0 if too short. */
int bz_apdu_parse(const uint8_t *buf, size_t n, bz_apdu *out);

/* ------------------------------------------------------------- allowlist ---- */

typedef enum {
    BZ_ALLOW_OK = 0,
    BZ_ALLOW_DENIED = 1,   /* command type is not on the whitelist */
    BZ_ALLOW_MALFORMED = 2 /* not a D0 template with command details */
} bz_allow_rc;

/* Whitelist gate (SYS-F-013). Parses the D0 template enough to read the type. */
bz_allow_rc bz_allow_check(const uint8_t *tlv, size_t len, uint8_t *type_out);

/* Command type names, for logs. Returns "UNKNOWN" for unmapped types. */
const char *bz_allow_name(uint8_t type);

/* ------------------------------------------------------- command builders --- */

/* Proactive command types (TS 31.111 §8.6), the subset the instrument may emit. */
#define BZ_CMD_REFRESH        0x01
#define BZ_CMD_POLL_INTERVAL  0x03
#define BZ_CMD_PLAY_TONE      0x20
#define BZ_CMD_DISPLAY_TEXT   0x21
#define BZ_CMD_GET_INKEY      0x22
#define BZ_CMD_GET_INPUT      0x23
#define BZ_CMD_SELECT_ITEM    0x24
#define BZ_CMD_SET_UP_MENU    0x25
#define BZ_CMD_LOCAL_INFO     0x26
#define BZ_CMD_TIMER_MGMT     0x27

#define BZ_TEXT_MAX 96
#define BZ_ITEMS_MAX 8

typedef struct {
    uint8_t id;
    char text[BZ_TEXT_MAX];
} bz_item;

/* Generic builder: D0 { 81 command details, 82 device identities, extra... }.
 * Returns the total length, or -1 on overflow. `extra` may be NULL. */
int bz_cmd_build(uint8_t *out, size_t cap, uint8_t number, uint8_t type,
                 uint8_t qualifier, const uint8_t *extra, size_t extra_len);

/* D0 + alpha identifier + N items. Returns length or -1. */
int bz_cmd_menu(uint8_t *out, size_t cap, uint8_t number, const char *alpha,
                const bz_item *items, size_t nitems);

/* D0 + alpha + text string. Returns length or -1. */
int bz_cmd_display_text(uint8_t *out, size_t cap, uint8_t number,
                        const char *alpha, const char *text);

#endif /* BZ_CORE_H */
