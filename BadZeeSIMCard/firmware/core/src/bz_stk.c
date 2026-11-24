/*
 * bz_stk.c — toolkit state machine.
 *
 * Both fetch mechanisms are implemented because the terminal's choice is
 * unknown until G1:
 *   USAT: the terminal sends FETCH (80 12 ..)
 *   SAT : the card answers 91 xx and the terminal sends GET RESPONSE (.. C0 ..)
 */
#include "bz_stk.h"

#include <string.h>

void bz_stk_init(bz_stk *s)
{
    memset(s, 0, sizeof *s);
    s->state = BZ_STK_RESET;
    s->number = 1;
}

const char *bz_stk_state_name(bz_stk_state st)
{
    switch (st) {
    case BZ_STK_RESET: return "RESET";
    case BZ_STK_IDLE: return "IDLE";
    case BZ_STK_PENDING: return "PENDING";
    case BZ_STK_WAIT_RESP: return "WAIT_RESP";
    default: return "?";
    }
}

int bz_stk_arm(bz_stk *s, const uint8_t *tlv, size_t len)
{
    if (s->state == BZ_STK_PENDING || s->state == BZ_STK_WAIT_RESP) return 3;

    uint8_t type = 0;
    bz_allow_rc rc = bz_allow_check(tlv, len, &type);
    if (rc == BZ_ALLOW_MALFORMED) { s->refusals++; return 2; }
    if (rc == BZ_ALLOW_DENIED) { s->refusals++; return 1; }
    if (len == 0 || len > sizeof s->cmd) { s->refusals++; return 2; }

    memcpy(s->cmd, tlv, len);
    s->cmd_len = len;
    s->last_type = type;
    s->number = (uint8_t)(s->number + 1u);
    s->state = BZ_STK_PENDING;
    return 0;
}

/* Walk a flat TLV list looking for one tag. Returns 1 and sets val/vlen. */
static int tlv_find(const uint8_t *p, size_t n, uint8_t tag, const uint8_t **val,
                    size_t *vlen)
{
    size_t i = 0;
    while (i + 2u <= n) {
        uint8_t t = p[i];
        size_t l = p[i + 1u];
        if (i + 2u + l > n) return 0;
        if (t == tag) {
            if (val) *val = p + i + 2u;
            if (vlen) *vlen = l;
            return 1;
        }
        i += 2u + l;
    }
    return 0;
}

size_t bz_stk_handle(bz_stk *s, const bz_apdu *a, uint8_t *rsp, size_t cap,
                     uint16_t *sw)
{
    *sw = BZ_SW_INS_UNKNOWN;

    if (a->malformed) {
        *sw = BZ_SW_WRONG_LEN;
        return 0;
    }

    switch (a->ins) {
    case 0x10: { /* TERMINAL PROFILE */
        if (a->lc) {
            size_t n = a->lc > sizeof s->profile ? sizeof s->profile : a->lc;
            memcpy(s->profile, a->data, n);
            s->profile_len = n;
        }
        if (s->state == BZ_STK_RESET) s->state = BZ_STK_IDLE;
        *sw = BZ_SW_OK;
        return 0;
    }

    case 0xC2: /* ENVELOPE (menu selection, events) */
        *sw = BZ_SW_OK;
        return 0;

    case 0x12: /* FETCH (USAT) */
    case 0xC0: /* GET RESPONSE (SAT path) */
        if (s->state != BZ_STK_PENDING) {
            *sw = BZ_SW_INS_UNKNOWN;
            return 0;
        }
        if (s->cmd_len > cap) {
            *sw = BZ_SW_WRONG_LEN;
            return 0;
        }
        memcpy(rsp, s->cmd, s->cmd_len);
        s->state = BZ_STK_WAIT_RESP;
        s->delivered++;
        *sw = BZ_SW_OK;
        return s->cmd_len;

    case 0x14: { /* TERMINAL RESPONSE */
        const uint8_t *v = NULL;
        size_t vl = 0;
        if (a->lc && tlv_find(a->data, a->lc, 0x83, &v, &vl) && vl >= 1)
            s->last_result = v[0];
        else
            s->last_result = 0xFF; /* malformed response, kept as evidence */
        s->state = BZ_STK_IDLE;
        *sw = BZ_SW_OK;
        return 0;
    }

    default:
        if (s->state == BZ_STK_PENDING) {
            /* Signal "proactive command pending" on the SAT path. */
            size_t l = s->cmd_len > 0xFFu ? 0xFFu : s->cmd_len;
            *sw = (uint16_t)(0x9100u | l);
            return 0;
        }
        *sw = BZ_SW_INS_UNKNOWN;
        return 0;
    }
}
