/*
 * test_core.c — native unit tests for the portable core.
 *
 * The menu test compares against a real capture (SET UP MENU from a commercial
 * card, reproduced in spec/REFERENCE.md §3), so an encoding regression fails
 * here rather than on the bench.
 */
#include <stdio.h>
#include <string.h>

#include "bz_core.h"
#include "bz_stk.h"

static int checks;
static int failures;

#define CHECK(c)                                                                     \
    do {                                                                             \
        checks++;                                                                    \
        if (!(c)) {                                                                   \
            failures++;                                                               \
            printf("FAIL line %d: %s\n", __LINE__, #c);                               \
        }                                                                             \
    } while (0)

#define CHECK_EQ(a, b)                                                                \
    do {                                                                              \
        checks++;                                                                     \
        long long _a = (long long)(a), _b = (long long)(b);                            \
        if (_a != _b) {                                                               \
            failures++;                                                               \
            printf("FAIL line %d: %s == %s (%lld vs %lld)\n", __LINE__, #a, #b, _a,    \
                   _b);                                                               \
        }                                                                             \
    } while (0)

static void test_crc(void)
{
    /* CRC-16/CCITT-FALSE check value for "123456789" is 0x29B1. */
    CHECK_EQ(bz_crc16((const uint8_t *)"123456789", 9), 0x29B1);
    CHECK_EQ(bz_crc16(NULL, 0), 0xFFFF);
}

static void test_tlv(void)
{
    uint8_t b[64];
    bz_tlv t;

    bz_tlv_init(&t, b, sizeof b);
    bz_tlv_u8(&t, 0x01, 0x42);
    bz_tlv_text(&t, 0x85, "Menu");
    CHECK(bz_tlv_ok(&t));
    CHECK_EQ(t.len, 3 + 6);
    CHECK_EQ(b[0], 0x01);
    CHECK_EQ(b[1], 1);
    CHECK_EQ(b[2], 0x42);
    CHECK_EQ(b[3], 0x85);
    CHECK_EQ(b[4], 4);
    CHECK_EQ(b[5], 'M');

    bz_tlv_init(&t, b, sizeof b);
    bz_tlv_begin(&t, 0xD0);
    bz_tlv_u8(&t, 0x81, 0x99);
    bz_tlv_end(&t);
    CHECK(bz_tlv_ok(&t));
    CHECK_EQ(b[0], 0xD0);
    CHECK_EQ(b[1], 3);

    /* nested two levels */
    bz_tlv_init(&t, b, sizeof b);
    bz_tlv_begin(&t, 0xD0);
    bz_tlv_begin(&t, 0x8F);
    bz_tlv_u8(&t, 0x01, 0x01);
    bz_tlv_end(&t);
    bz_tlv_end(&t);
    CHECK(bz_tlv_ok(&t));
    CHECK_EQ(b[0], 0xD0);
    CHECK_EQ(b[1], 5);
    CHECK_EQ(b[2], 0x8F);
    CHECK_EQ(b[3], 3);

    /* overflow is an error, not a silent truncation */
    uint8_t small[4];
    bz_tlv_init(&t, small, sizeof small);
    bz_tlv_put(&t, 0x01, "abcdef", 6);
    CHECK(!bz_tlv_ok(&t));
}

static void test_apdu(void)
{
    bz_apdu a;

    uint8_t fetch[] = {0x80, 0x12, 0x00, 0x00, 0x28};
    CHECK(bz_apdu_parse(fetch, sizeof fetch, &a));
    CHECK_EQ(a.ins, 0x12);
    CHECK(a.has_le);
    CHECK_EQ(a.le, 0x28);
    CHECK_EQ(a.lc, 0);
    CHECK(!a.malformed);

    /* TERMINAL RESPONSE with 12 data bytes, as captured. */
    uint8_t tr[] = {0x80, 0x14, 0x00, 0x00, 0x0C, 0x81, 0x03, 0x01, 0x25, 0x00,
                    0x82, 0x02, 0x82, 0x81, 0x83, 0x01, 0x00};
    CHECK(bz_apdu_parse(tr, sizeof tr, &a));
    CHECK_EQ(a.lc, 12);
    CHECK(!a.malformed);

    uint8_t bad[] = {0x80, 0x14, 0x00, 0x00, 0x0C, 0x81};
    CHECK(bz_apdu_parse(bad, sizeof bad, &a));
    CHECK(a.malformed);

    uint8_t zero[] = {0x80, 0x12, 0x00, 0x00, 0x00};
    CHECK(bz_apdu_parse(zero, sizeof zero, &a));
    CHECK(a.p3_zero);
    CHECK(a.has_le);

    uint8_t short_cmd[] = {0x80, 0x10, 0x00, 0x00};
    CHECK(bz_apdu_parse(short_cmd, sizeof short_cmd, &a));
    CHECK_EQ(a.ins, 0x10);
}

static void test_allow(void)
{
    uint8_t cmd[128];
    uint8_t type = 0;

    int n = bz_cmd_menu(cmd, sizeof cmd, 1, "Menu", NULL, 0);
    CHECK(n > 0);
    CHECK_EQ(bz_allow_check(cmd, (size_t)n, &type), BZ_ALLOW_OK);
    CHECK_EQ(type, 0x25);

    uint8_t other[16];
    int m = bz_cmd_build(other, sizeof other, 1, 0x13 /* SEND SHORT MESSAGE */, 0, NULL, 0);
    CHECK(m > 0);
    CHECK_EQ(bz_allow_check(other, (size_t)m, &type), BZ_ALLOW_DENIED);
    CHECK_EQ(type, 0x13);

    int u = bz_cmd_build(other, sizeof other, 1, 0x77, 0, NULL, 0);
    CHECK(u > 0);
    CHECK_EQ(bz_allow_check(other, (size_t)u, &type), BZ_ALLOW_DENIED);

    /* OPEN CHANNEL (bearer) must be denied */
    int oc = bz_cmd_build(other, sizeof other, 1, 0x40, 0, NULL, 0);
    CHECK(oc > 0);
    CHECK_EQ(bz_allow_check(other, (size_t)oc, &type), BZ_ALLOW_DENIED);

    const uint8_t not_a_template[] = {0x00, 0x00};
    CHECK_EQ(bz_allow_check(not_a_template, 2, &type), BZ_ALLOW_MALFORMED);

    const uint8_t truncated[] = {0xD0, 0x10, 0x81, 0x03};
    CHECK_EQ(bz_allow_check(truncated, sizeof truncated, &type), BZ_ALLOW_MALFORMED);

    CHECK(strcmp(bz_allow_name(0x25), "SET UP MENU") == 0);
    CHECK(strcmp(bz_allow_name(0x99), "UNKNOWN") == 0);
}

static void test_menu_matches_capture(void)
{
    bz_item items[2];
    memset(items, 0, sizeof items);
    items[0].id = 0x80;
    strcpy(items[0].text, "Item 1");
    items[1].id = 0x81;
    strcpy(items[1].text, "Item 2");

    uint8_t cmd[128];
    int n = bz_cmd_menu(cmd, sizeof cmd, 1, "Menu name", items, 2);
    CHECK(n > 0);

    /* Real capture (spec/REFERENCE.md §3). */
    static const uint8_t expect[] = {
        0xD0, 0x26, 0x81, 0x03, 0x01, 0x25, 0x00, 0x82, 0x02, 0x81, 0x82,
        0x85, 0x09, 'M',  'e',  'n',  'u',  ' ',  'n',  'a',  'm',  'e',
        0x8F, 0x07, 0x80, 'I',  't',  'e',  'm',  ' ',  '1',
        0x8F, 0x07, 0x81, 'I',  't',  'e',  'm',  ' ',  '2'};

    CHECK_EQ(n, (int)sizeof expect);
    CHECK_EQ(memcmp(cmd, expect, sizeof expect), 0);
}

static void test_display_text(void)
{
    uint8_t cmd[128];
    int n = bz_cmd_display_text(cmd, sizeof cmd, 1, NULL, "Hello");
    CHECK(n > 0);
    CHECK_EQ(cmd[0], 0xD0);
    CHECK_EQ(cmd[2], 0x81);
    CHECK_EQ(cmd[5], 0x21); /* DISPLAY TEXT */
    CHECK_EQ(cmd[7], 0x82);
    CHECK_EQ(cmd[11], 0x8D); /* text string */
    CHECK_EQ(cmd[12], 6);    /* 0x04 + 5 chars */
    CHECK_EQ(cmd[13], 0x04);
    CHECK_EQ(memcmp(cmd + 14, "Hello", 5), 0);
}

static void test_stk_flow(void)
{
    bz_stk s;
    uint8_t rsp[300];
    uint16_t sw = 0;
    bz_apdu a;

    bz_stk_init(&s);
    CHECK_EQ(s.state, BZ_STK_RESET);

    /* terminal profile: 80 10 00 00 0A <10 bytes> */
    uint8_t prof[] = {0x80, 0x10, 0x00, 0x00, 0x0A, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    CHECK(bz_apdu_parse(prof, sizeof prof, &a));
    CHECK_EQ(bz_stk_handle(&s, &a, rsp, sizeof rsp, &sw), 0);
    CHECK_EQ(sw, BZ_SW_OK);
    CHECK_EQ(s.profile_len, 10);
    CHECK(s.state == BZ_STK_IDLE || s.state == BZ_STK_RESET);

    /* arm the menu */
    uint8_t cmd[128];
    bz_item it;
    memset(&it, 0, sizeof it);
    it.id = 0x80;
    strcpy(it.text, "Info");
    int n = bz_cmd_menu(cmd, sizeof cmd, 1, "Service", &it, 1);
    CHECK(n > 0);
    CHECK_EQ(bz_stk_arm(&s, cmd, (size_t)n), 0);
    CHECK(s.state == BZ_STK_PENDING);

    /* a second arm while pending is refused */
    CHECK_EQ(bz_stk_arm(&s, cmd, (size_t)n), 3);

    /* any other APDU while pending answers 91 xx */
    uint8_t read_ef[] = {0xA0, 0xB0, 0x00, 0x00, 0x0A};
    CHECK(bz_apdu_parse(read_ef, sizeof read_ef, &a));
    CHECK_EQ(bz_stk_handle(&s, &a, rsp, sizeof rsp, &sw), 0);
    CHECK_EQ(sw & 0xFF00, 0x9100);
    CHECK_EQ(sw & 0x00FF, (unsigned)n);

    /* FETCH delivers it */
    uint8_t fetch[] = {0x80, 0x12, 0x00, 0x00, 0x40};
    CHECK(bz_apdu_parse(fetch, sizeof fetch, &a));
    size_t got = bz_stk_handle(&s, &a, rsp, sizeof rsp, &sw);
    CHECK_EQ(got, (size_t)n);
    CHECK_EQ(sw, BZ_SW_OK);
    CHECK(s.state == BZ_STK_WAIT_RESP);
    CHECK_EQ(memcmp(rsp, cmd, got), 0);

    /* terminal response with result 0 */
    uint8_t tr[] = {0x80, 0x14, 0x00, 0x00, 0x08, 0x81, 0x03, 0x01, 0x25, 0x00,
                    0x83, 0x01, 0x00}; /* Lc = 8: command details (5) + result (3) */
    CHECK(bz_apdu_parse(tr, sizeof tr, &a));
    CHECK_EQ(bz_stk_handle(&s, &a, rsp, sizeof rsp, &sw), 0);
    CHECK_EQ(sw, BZ_SW_OK);
    CHECK_EQ(s.last_result, 0);
    CHECK(s.state == BZ_STK_IDLE);

    /* a denied command is refused and counted */
    uint8_t sms[16];
    int m = bz_cmd_build(sms, sizeof sms, 2, 0x13, 0, NULL, 0);
    CHECK(m > 0);
    CHECK_EQ(bz_stk_arm(&s, sms, (size_t)m), 1);
    CHECK_EQ(s.refusals, 1);
    CHECK(s.state == BZ_STK_IDLE);
}

static void test_sat_path(void)
{
    bz_stk s;
    uint8_t rsp[300];
    uint16_t sw = 0;
    bz_apdu a;

    bz_stk_init(&s);
    s.state = BZ_STK_IDLE;

    uint8_t cmd[64];
    int n = bz_cmd_build(cmd, sizeof cmd, 1, BZ_CMD_LOCAL_INFO, 0x00, NULL, 0);
    CHECK(n > 0);
    CHECK_EQ(bz_stk_arm(&s, cmd, (size_t)n), 0);

    /* SAT path: GET RESPONSE (A0 C0 00 00 xx) */
    uint8_t getresp[] = {0xA0, 0xC0, 0x00, 0x00, 0x20};
    CHECK(bz_apdu_parse(getresp, sizeof getresp, &a));
    size_t got = bz_stk_handle(&s, &a, rsp, sizeof rsp, &sw);
    CHECK_EQ(got, (size_t)n);
    CHECK_EQ(sw, BZ_SW_OK);
    CHECK(s.state == BZ_STK_WAIT_RESP);
}

static void test_overflow_guard(void)
{
    uint8_t tiny[8];
    CHECK(bz_cmd_menu(tiny, sizeof tiny, 1, "Service", NULL, 0) < 0);
}

int main(void)
{
    test_crc();
    test_tlv();
    test_apdu();
    test_allow();
    test_menu_matches_capture();
    test_display_text();
    test_stk_flow();
    test_sat_path();
    test_overflow_guard();

    printf("%d checks, %d failures\n", checks, failures);
    return failures ? 1 : 0;
}
