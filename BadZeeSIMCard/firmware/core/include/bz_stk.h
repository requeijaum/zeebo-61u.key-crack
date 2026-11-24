/*
 * bz_stk.h — toolkit state machine of the instrument.
 *
 * States matter here because two different fetch mechanisms must both work and
 * because a command may only be armed when nothing is pending (the terminal
 * talks to one proactive command at a time).
 */
#ifndef BZ_STK_H
#define BZ_STK_H

#include "bz_core.h"

typedef enum {
    BZ_STK_RESET = 0, /* no terminal profile yet */
    BZ_STK_IDLE,      /* profile received, nothing pending */
    BZ_STK_PENDING,   /* a command is armed, not yet fetched */
    BZ_STK_WAIT_RESP  /* command fetched, waiting for TERMINAL RESPONSE */
} bz_stk_state;

#define BZ_STK_CMD_MAX 256
#define BZ_STK_PROFILE_MAX 64

typedef struct {
    bz_stk_state state;
    uint8_t cmd[BZ_STK_CMD_MAX];
    size_t cmd_len;
    uint8_t profile[BZ_STK_PROFILE_MAX];
    size_t profile_len;
    uint8_t last_type;
    uint8_t last_result;
    uint8_t number; /* command sequence number, starts at 1 */
    unsigned refusals;
    unsigned delivered;
} bz_stk;

void bz_stk_init(bz_stk *s);

/* Arm a command. Returns 0 armed, 1 denied by allowlist, 2 malformed,
 * 3 already pending. Refusals are counted (SYS-F-013 evidence). */
int bz_stk_arm(bz_stk *s, const uint8_t *tlv, size_t len);

/* Handle one APDU. Writes at most cap response bytes; always sets the status
 * word. Returns the response length. */
size_t bz_stk_handle(bz_stk *s, const bz_apdu *a, uint8_t *rsp, size_t cap,
                     uint16_t *sw);

const char *bz_stk_state_name(bz_stk_state st);

#endif /* BZ_STK_H */
