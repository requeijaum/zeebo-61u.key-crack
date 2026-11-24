/*
 * main.c — session loop: ATR, APDU service, host link.
 *
 * One rule shapes the loop: a command is armed by the host *before* the console
 * is powered on (PROCEDURE.md §2), so an armed stimulus must survive the card
 * reset that follows power-on. The state machine is therefore not re-initialised
 * on reset; only an interrupted exchange is returned to IDLE.
 */
#include <stdio.h>
#include <string.h>

#include "pico/stdlib.h"

#include "board.h"
#include "bz_core.h"
#include "bz_stk.h"
#include "host_link.h"
#include "phy.h"

static bz_stk g_stk;

int main(void)
{
    stdio_usb_init();
    phy_init();

    bz_stk_init(&g_stk);
    host_link_init(&g_stk);

    for (;;) {
        host_poll();

        /* Wait for RST to be released by the terminal (polled, 200 ms). */
        if (!phy_wait_reset(200000u)) continue;

        phy_measure_etu();
        phy_send_atr();

        /* A reset ends any exchange in flight but keeps an armed command. */
        if (g_stk.state == BZ_STK_WAIT_RESP) g_stk.state = BZ_STK_IDLE;

        for (;;) {
            uint8_t buf[300];
            int n = phy_recv_apdu(buf, sizeof buf, 500000u);
            if (n <= 0) break; /* terminal went quiet or reset */

            bz_apdu a;
            if (!bz_apdu_parse(buf, (size_t)n, &a)) {
                phy_send_response(NULL, 0, BZ_SW_WRONG_LEN);
                continue;
            }

            uint8_t rsp[300];
            uint16_t sw = BZ_SW_INS_UNKNOWN;
            size_t rl = bz_stk_handle(&g_stk, &a, rsp, sizeof rsp, &sw);
            host_log_exchange(&a, rsp, rl, sw);
            phy_send_response(rsp, rl, sw);
        }
    }
}
