/*
 * bz_core.c — CRC, TLV, APDU, allowlist and proactive-command builders.
 *
 * Encoding decisions are taken from real captures, not from memory:
 *   spec/REFERENCE.md §3 lists them with the exact byte sequences.
 */
#include "bz_core.h"

#include <string.h>

/* ---------------------------------------------------------------- CRC-16 ---- */

uint16_t bz_crc16(const uint8_t *data, size_t len)
{
    uint16_t crc = 0xFFFFu;
    for (size_t i = 0; i < len; i++) {
        crc ^= (uint16_t)data[i] << 8;
        for (int b = 0; b < 8; b++)
            crc = (crc & 0x8000u) ? (uint16_t)((crc << 1) ^ 0x1021u) : (uint16_t)(crc << 1);
    }
    return crc;
}

/* ------------------------------------------------------------------ TLV ----- */

void bz_tlv_init(bz_tlv *t, uint8_t *buf, size_t cap)
{
    t->buf = buf;
    t->cap = cap;
    t->len = 0;
    t->depth = 0;
    t->err = 0;
}

int bz_tlv_ok(const bz_tlv *t)
{
    return t->err == 0 && t->depth == 0;
}

int bz_tlv_put(bz_tlv *t, uint8_t tag, const void *val, size_t len)
{
    if (t->err) return 0;
    if (len > 255u || t->len + 2u + len > t->cap) { t->err = 1; return 0; }
    t->buf[t->len++] = tag;
    t->buf[t->len++] = (uint8_t)len;
    if (len) {
        memcpy(t->buf + t->len, val, len);
        t->len += len;
    }
    return 1;
}

int bz_tlv_u8(bz_tlv *t, uint8_t tag, uint8_t v)
{
    return bz_tlv_put(t, tag, &v, 1);
}

int bz_tlv_text(bz_tlv *t, uint8_t tag, const char *ascii)
{
    size_t n = ascii ? strlen(ascii) : 0;
    return bz_tlv_put(t, tag, ascii, n);
}

/* Text string with the 0x04 (8-bit default alphabet) coding byte. */
int bz_tlv_text_dcs(bz_tlv *t, uint8_t tag, const char *ascii)
{
    size_t n = ascii ? strlen(ascii) : 0;
    if (t->err) return 0;
    if (n + 1u > 255u || t->len + 2u + n + 1u > t->cap) { t->err = 1; return 0; }
    t->buf[t->len++] = tag;
    t->buf[t->len++] = (uint8_t)(n + 1u);
    t->buf[t->len++] = 0x04u;
    if (n) {
        memcpy(t->buf + t->len, ascii, n);
        t->len += n;
    }
    return 1;
}

int bz_tlv_begin(bz_tlv *t, uint8_t tag)
{
    if (t->err) return 0;
    if (t->depth >= BZ_TLV_MAX_DEPTH || t->len + 2u > t->cap) { t->err = 1; return 0; }
    t->stack[t->depth++] = t->len;
    t->buf[t->len++] = tag;
    t->buf[t->len++] = 0; /* patched by bz_tlv_end */
    return 1;
}

int bz_tlv_end(bz_tlv *t)
{
    if (t->err || t->depth == 0) { t->err = 1; return 0; }
    size_t hdr = t->stack[--t->depth];
    size_t n = t->len - hdr - 2u;
    if (n > 255u) { t->err = 1; return 0; }
    t->buf[hdr + 1u] = (uint8_t)n;
    return 1;
}

/* ----------------------------------------------------------------- APDU ----- */

int bz_apdu_parse(const uint8_t *buf, size_t n, bz_apdu *out)
{
    if (n < 4) return 0;
    memset(out, 0, sizeof *out);
    out->cla = buf[0];
    out->ins = buf[1];
    out->p1 = buf[2];
    out->p2 = buf[3];
    if (n == 4) return 1; /* T=0: no P3 yet */

    size_t p3 = buf[4];
    size_t rest = n - 5;
    if (p3 == 0) {
        /* Le = 256 per ISO 7816-3 (encoded as 00). */
        out->p3_zero = 1;
        out->has_le = 1;
        out->le = 0;
        return 1;
    }
    if (rest >= p3) {
        out->data = buf + 5;
        out->lc = p3;
    } else if (rest == 0) {
        out->has_le = 1;
        out->le = (uint8_t)p3;
    } else {
        out->malformed = 1;
        out->lc = rest;
        out->data = buf + 5;
    }
    return 1;
}

/* ------------------------------------------------------------- allowlist ---- */

static int type_allowed(uint8_t type)
{
    switch (type) {
    case BZ_CMD_REFRESH:
    case 0x02: /* MORE TIME */
    case BZ_CMD_POLL_INTERVAL:
    case 0x04: /* POLLING OFF */
    case BZ_CMD_PLAY_TONE:
    case BZ_CMD_DISPLAY_TEXT:
    case BZ_CMD_GET_INKEY:
    case BZ_CMD_GET_INPUT:
    case BZ_CMD_SELECT_ITEM:
    case BZ_CMD_SET_UP_MENU:
    case BZ_CMD_LOCAL_INFO:
    case BZ_CMD_TIMER_MGMT:
    case 0x28: /* SET UP IDLE MODE TEXT */
    case 0x35: /* LANGUAGE NOTIFICATION */
        return 1;
    default:
        /* 0x05 SET UP EVENT LIST is deliberately NOT allowed: it can request
         * network events, and this instrument must never cause transmission.
         * Everything else is forbidden by construction. */
        return 0;
    }
}

const char *bz_allow_name(uint8_t type)
{
    switch (type) {
    case 0x01: return "REFRESH";
    case 0x02: return "MORE TIME";
    case 0x03: return "POLL INTERVAL";
    case 0x04: return "POLLING OFF";
    case 0x05: return "SET UP EVENT LIST";
    case 0x10: return "SET UP CALL";
    case 0x11: return "SEND SS";
    case 0x12: return "SEND USSD";
    case 0x13: return "SEND SHORT MESSAGE";
    case 0x14: return "SEND DTMF";
    case 0x15: return "LAUNCH BROWSER";
    case 0x16: return "GEOGRAPHICAL LOCATION REQUEST";
    case 0x20: return "PLAY TONE";
    case 0x21: return "DISPLAY TEXT";
    case 0x22: return "GET INKEY";
    case 0x23: return "GET INPUT";
    case 0x24: return "SELECT ITEM";
    case 0x25: return "SET UP MENU";
    case 0x26: return "PROVIDE LOCAL INFORMATION";
    case 0x27: return "TIMER MANAGEMENT";
    case 0x28: return "SET UP IDLE MODE TEXT";
    case 0x30: return "PERFORM CARD APDU";
    case 0x31: return "POWER ON CARD";
    case 0x32: return "POWER OFF CARD";
    case 0x33: return "GET READER STATUS";
    case 0x34: return "RUN AT COMMAND";
    case 0x35: return "LANGUAGE NOTIFICATION";
    case 0x40: return "OPEN CHANNEL";
    case 0x41: return "CLOSE CHANNEL";
    case 0x42: return "RECEIVE DATA";
    case 0x43: return "SEND DATA";
    case 0x44: return "GET CHANNEL STATUS";
    case 0x45: return "SERVICE SEARCH";
    case 0x46: return "GET SERVICE INFORMATION";
    case 0x47: return "DECLARE SERVICE";
    case 0x50: return "SET FRAMES";
    case 0x51: return "GET FRAMES STATUS";
    default: return "UNKNOWN";
    }
}

bz_allow_rc bz_allow_check(const uint8_t *tlv, size_t len, uint8_t *type_out)
{
    if (len < 2 || tlv[0] != 0xD0) return BZ_ALLOW_MALFORMED;

    const uint8_t *p;
    size_t body;
    if (tlv[1] < 0x80u) { /* short form */
        body = tlv[1];
        p = tlv + 2;
        if (body > len - 2) return BZ_ALLOW_MALFORMED;
    } else { /* long form: 81 <len8> */
        size_t nb = tlv[1] & 0x7Fu;
        if (nb != 1u || len < 4) return BZ_ALLOW_MALFORMED;
        body = tlv[2];
        p = tlv + 3;
        if (body > len - 3) return BZ_ALLOW_MALFORMED;
    }

    if (body < 5u) return BZ_ALLOW_MALFORMED;
    if (p[0] != 0x81u || p[1] < 3u) return BZ_ALLOW_MALFORMED;

    uint8_t type = p[3];
    if (type_out) *type_out = type;
    return type_allowed(type) ? BZ_ALLOW_OK : BZ_ALLOW_DENIED;
}

/* ------------------------------------------------------- command builders --- */

int bz_cmd_build(uint8_t *out, size_t cap, uint8_t number, uint8_t type,
                 uint8_t qualifier, const uint8_t *extra, size_t extra_len)
{
    bz_tlv t;
    bz_tlv_init(&t, out, cap);
    bz_tlv_begin(&t, 0xD0);
    {
        uint8_t cd[3] = {number, type, qualifier};
        bz_tlv_put(&t, 0x81, cd, 3);
    }
    {
        uint8_t di[2] = {0x81, 0x82}; /* UICC -> ME */
        bz_tlv_put(&t, 0x82, di, 2);
    }
    if (extra && extra_len) {
        if (t.err || t.len + extra_len > t.cap) { t.err = 1; return -1; }
        memcpy(t.buf + t.len, extra, extra_len);
        t.len += extra_len;
    }
    bz_tlv_end(&t);
    return bz_tlv_ok(&t) ? (int)t.len : -1;
}

int bz_cmd_menu(uint8_t *out, size_t cap, uint8_t number, const char *alpha,
                const bz_item *items, size_t nitems)
{
    uint8_t extra[256];
    bz_tlv e;
    bz_tlv_init(&e, extra, sizeof extra);

    if (alpha && alpha[0]) bz_tlv_text(&e, 0x85, alpha); /* no coding byte: 8-bit default */

    for (size_t i = 0; i < nitems && i < BZ_ITEMS_MAX; i++) {
        /* Item value = item identifier byte, then the text (8-bit default). */
        uint8_t val[1 + BZ_TEXT_MAX];
        size_t tl = strlen(items[i].text);
        if (tl > BZ_TEXT_MAX) tl = BZ_TEXT_MAX;
        val[0] = items[i].id;
        memcpy(val + 1, items[i].text, tl);
        bz_tlv_put(&e, 0x8F, val, 1 + tl);
    }
    if (!bz_tlv_ok(&e)) return -1;
    return bz_cmd_build(out, cap, number, BZ_CMD_SET_UP_MENU, 0x00, extra, e.len);
}

int bz_cmd_display_text(uint8_t *out, size_t cap, uint8_t number,
                        const char *alpha, const char *text)
{
    uint8_t extra[256];
    bz_tlv e;
    bz_tlv_init(&e, extra, sizeof extra);

    if (alpha && alpha[0]) bz_tlv_text(&e, 0x85, alpha);
    if (text && text[0]) bz_tlv_text_dcs(&e, 0x8D, text);
    if (!bz_tlv_ok(&e)) return -1;
    return bz_cmd_build(out, cap, number, BZ_CMD_DISPLAY_TEXT, 0x80, extra, e.len);
}
