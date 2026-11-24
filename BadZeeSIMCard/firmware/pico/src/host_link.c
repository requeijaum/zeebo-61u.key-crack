/*
 * host_link.c — framed control channel over USB CDC (INTERFACES.md §5).
 *
 * Uses stdio_usb for the transport and owns the framing only. The message set is
 * the same on both sides; the Python implementation is host/bzsim/frame.py, and
 * both compute CRC-16/CCITT-FALSE over the payload.
 */
#include <stdio.h>
#include <string.h>

#include "pico/stdlib.h"

#include "board.h"
#include "bz_core.h"
#include "bz_stk.h"
#include "host_link.h"

#define BZ_MAGIC 0x5Au
#define BZ_VERSION 1u

enum {
    MSG_HELLO = 1,
    MSG_HELLO_ACK = 2,
    MSG_ARM = 3,
    MSG_STATUS = 4,
    MSG_LOG = 5,
    MSG_RESULT = 6,
    MSG_STOP = 7,
    MSG_ERROR = 8
};

static bz_stk *g_stk;
static uint8_t g_rx[4096];
static size_t g_rxlen;

/* --------------------------------------------------------------- transmit -- */

static void send_frame(uint8_t type, const uint8_t *payload, size_t n)
{
    if (n > 4096u) return;
    uint8_t hdr[5] = {BZ_MAGIC, BZ_VERSION, type, (uint8_t)(n & 0xFFu),
                      (uint8_t)((n >> 8) & 0xFFu)};
    uint16_t crc = bz_crc16(payload, n);
    fwrite(hdr, 1, sizeof hdr, stdout);
    if (n) fwrite(payload, 1, n, stdout);
    uint8_t tail[2] = {(uint8_t)(crc & 0xFFu), (uint8_t)(crc >> 8)};
    fwrite(tail, 1, sizeof tail, stdout);
    fflush(stdout);
}

/* ---------------------------------------------------------------- receive -- */

static void handle_frame(uint8_t type, const uint8_t *p, size_t n)
{
    switch (type) {
    case MSG_HELLO: {
        const char *id = BZ_FW_HASH;
        send_frame(MSG_HELLO_ACK, (const uint8_t *)id, strlen(id));
        break;
    }
    case MSG_ARM: {
        int rc = bz_stk_arm(g_stk, p, n);
        uint8_t out[2] = {(uint8_t)rc, (uint8_t)(rc == 0 ? 1 : 0)};
        send_frame(MSG_RESULT, out, sizeof out);
        break;
    }
    case MSG_STATUS: {
        uint8_t out[6] = {
            (uint8_t)g_stk->state,
            (uint8_t)g_stk->refusals,
            (uint8_t)g_stk->delivered,
            (uint8_t)(g_stk->cmd_len & 0xFFu),
            (uint8_t)((g_stk->cmd_len >> 8) & 0xFFu),
            0 /* reserved: drop counter on the logger side */
        };
        send_frame(MSG_STATUS, out, sizeof out);
        break;
    }
    case MSG_STOP:
        break;
    default: {
        uint8_t err = 0x01; /* unsupported message */
        send_frame(MSG_ERROR, &err, 1);
        break;
    }
    }
}

void host_link_init(bz_stk *s)
{
    g_stk = s;
    g_rxlen = 0;
}

void host_poll(void)
{
    int c;
    while ((c = getchar_timeout_us(0)) >= 0) {
        if (g_rxlen < sizeof g_rx) g_rx[g_rxlen++] = (uint8_t)c;
    }

    for (;;) {
        if (g_rxlen < 7u) return; /* header + crc */
        if (g_rx[0] != BZ_MAGIC) {
            memmove(g_rx, g_rx + 1, g_rxlen - 1);
            g_rxlen--;
            continue;
        }
        size_t n = (size_t)g_rx[3] | ((size_t)g_rx[4] << 8);
        if (n > sizeof g_rx - 7u) { /* corrupt length: drop one byte and resync */
            memmove(g_rx, g_rx + 1, g_rxlen - 1);
            g_rxlen--;
            continue;
        }
        size_t total = 5u + n + 2u;
        if (g_rxlen < total) return;

        uint16_t got = (uint16_t)g_rx[5u + n] | ((uint16_t)g_rx[6u + n] << 8);
        if (got != bz_crc16(g_rx + 5, n)) {
            memmove(g_rx, g_rx + 1, g_rxlen - 1);
            g_rxlen--;
            continue;
        }
        handle_frame(g_rx[2], g_rx + 5, n);
        memmove(g_rx, g_rx + total, g_rxlen - total);
        g_rxlen -= total;
    }
}

void host_log_exchange(const bz_apdu *a, const uint8_t *rsp, size_t rsp_len,
                       uint16_t sw)
{
    uint8_t rec[400];
    size_t k = 0;

    rec[k++] = 0; /* terminal -> card */
    rec[k++] = (uint8_t)(5u + a->lc);
    rec[k++] = a->cla;
    rec[k++] = a->ins;
    rec[k++] = a->p1;
    rec[k++] = a->p2;
    rec[k++] = (uint8_t)a->lc;
    for (size_t i = 0; i < a->lc && k < sizeof rec; i++) rec[k++] = a->data[i];

    rec[k++] = 1; /* card -> terminal */
    rec[k++] = (uint8_t)(rsp_len + 2u);
    for (size_t i = 0; i < rsp_len && k < sizeof rec; i++) rec[k++] = rsp[i];
    rec[k++] = (uint8_t)(sw >> 8);
    rec[k++] = (uint8_t)(sw & 0xFFu);

    uint32_t ms = time_us_32() / 1000u;
    rec[k++] = (uint8_t)(ms & 0xFFu);
    rec[k++] = (uint8_t)((ms >> 8) & 0xFFu);
    rec[k++] = (uint8_t)((ms >> 16) & 0xFFu);
    rec[k++] = (uint8_t)((ms >> 24) & 0xFFu);

    send_frame(MSG_LOG, rec, k);
}
