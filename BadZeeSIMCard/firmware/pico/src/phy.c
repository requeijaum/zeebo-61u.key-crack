/*
 * phy.c — ISO 7816 character-level PHY, bit-timed in software.
 *
 * Decision D-8 (IMPLEMENTATION.md): start with a busy-wait PHY rather than a PIO
 * program. At 3.57 MHz an ETU is 104 µs (~13 800 cycles at 133 MHz), so a
 * calibrated busy-wait holds jitter far inside the 10 % budget of SYS-P-001, and
 * the code is inspectable. A PIO version is only justified if G0 measures jitter
 * outside the budget — a change with evidence, not a guess.
 *
 * NOT COMPILED in the development environment used to write it (no Pico SDK).
 * The untested surface is deliberately limited to this file and host_link.c.
 */
#include "pico/stdlib.h"
#include "hardware/gpio.h"

#include "board.h"
#include "phy.h"

static uint32_t g_etu_us = BZ_ETU_DEFAULT_US;

/* ---------------------------------------------------------------- GPIO ----- */

static void io_release(void)
{
    gpio_set_dir(BZ_PIN_IO, GPIO_IN); /* pull-up keeps the line high when idle */
}

static void io_drive(int level)
{
    gpio_put(BZ_PIN_IO, level ? 1 : 0);
    gpio_set_dir(BZ_PIN_IO, GPIO_OUT);
}

void phy_init(void)
{
    gpio_init(BZ_PIN_IO);
    gpio_pull_up(BZ_PIN_IO);
    io_release();

    gpio_init(BZ_PIN_RST);
    gpio_set_dir(BZ_PIN_RST, GPIO_IN);
    gpio_pull_up(BZ_PIN_RST);

    gpio_init(BZ_PIN_CLK);
    gpio_set_dir(BZ_PIN_CLK, GPIO_IN);

    gpio_init(BZ_PIN_VCC_SENSE);
    gpio_set_dir(BZ_PIN_VCC_SENSE, GPIO_IN);
}

uint32_t phy_etu_us(void)
{
    return g_etu_us;
}

/* Count CLK edges for 20 ms; guards against a dead clock. */
uint32_t phy_measure_etu(void)
{
    const uint32_t window = 20000;
    uint32_t t0 = time_us_32();
    uint32_t edges = 0;
    int last = gpio_get(BZ_PIN_CLK);

    while ((uint32_t)(time_us_32() - t0) < window) {
        int now = gpio_get(BZ_PIN_CLK);
        if (now && !last) edges++;
        last = now;
    }
    if (edges < 100) { /* no usable clock: keep the default */
        g_etu_us = BZ_ETU_DEFAULT_US;
        return g_etu_us;
    }
    uint32_t hz = edges * 50u; /* 20 ms window → ×50 = Hz */
    uint32_t etu = 372000000u / hz;
    if (etu < 10u) etu = 10u;
    g_etu_us = etu;
    return etu;
}

/* -------------------------------------------------------------- characters -- */

static int parity_even(uint8_t b)
{
    int p = 0;
    for (int i = 0; i < 8; i++) p ^= (b >> i) & 1;
    return p;
}

static void send_byte(uint8_t b)
{
    io_drive(0); /* start bit */
    busy_wait_us_32(g_etu_us);
    for (int i = 0; i < 8; i++) {
        io_drive((b >> i) & 1);
        busy_wait_us_32(g_etu_us);
    }
    io_drive(parity_even(b));
    busy_wait_us_32(g_etu_us);
    io_release(); /* stop bit is the pull-up */
    busy_wait_us_32(g_etu_us);
}

/* Returns the byte, -1 on idle timeout, -2 on parity error. */
static int recv_byte(uint32_t idle_timeout_us)
{
    uint32_t t0 = time_us_32();
    while (gpio_get(BZ_PIN_IO)) {
        if ((uint32_t)(time_us_32() - t0) > idle_timeout_us) return -1;
    }

    busy_wait_us_32(g_etu_us + g_etu_us / 2u); /* centre of bit 0 */
    uint8_t b = 0;
    for (int i = 0; i < 8; i++) {
        if (gpio_get(BZ_PIN_IO)) b |= (uint8_t)(1u << i);
        if (i != 7) busy_wait_us_32(g_etu_us);
    }
    busy_wait_us_32(g_etu_us);
    int p = gpio_get(BZ_PIN_IO);
    if (p != parity_even(b)) return -2;
    return (int)b;
}

/* -------------------------------------------------------------- framing ----- */

int phy_wait_reset(uint32_t timeout_us)
{
    uint32_t t0 = time_us_32();
    while (!gpio_get(BZ_PIN_RST)) {
        if ((uint32_t)(time_us_32() - t0) > timeout_us) return 0;
    }
    return 1;
}

void phy_send_atr(void)
{
    static const uint8_t atr[] = BZ_ATR_BYTES;
    /* 400 clock cycles = 400 × (ETU / 372) µs, per ISO 7816-3 t0. */
    busy_wait_us_32((400u * g_etu_us) / 372u);
    for (size_t i = 0; i < sizeof atr; i++) send_byte(atr[i]);
}

void phy_send_block(const uint8_t *buf, size_t n)
{
    for (size_t i = 0; i < n; i++) send_byte(buf[i]);
}

void phy_send_response(const uint8_t *buf, size_t n, uint16_t sw)
{
    phy_send_block(buf, n);
    send_byte((uint8_t)(sw >> 8));
    send_byte((uint8_t)(sw & 0xFF));
}

/* Reads one command: bytes until the line is idle for three ETUs.
 * Returns the byte count, -1 if the terminal never started, -3 on parity error. */
int phy_recv_apdu(uint8_t *buf, size_t cap, uint32_t first_byte_timeout_us)
{
    size_t n = 0;
    while (n < cap) {
        uint32_t to = (n == 0) ? first_byte_timeout_us : (3u * g_etu_us + 200u);
        int c = recv_byte(to);
        if (c == -1) break;
        if (c == -2) return -3;
        buf[n++] = (uint8_t)c;
    }
    return (int)n;
}
