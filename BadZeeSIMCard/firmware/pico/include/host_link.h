#ifndef BZ_HOST_LINK_H
#define BZ_HOST_LINK_H

#include <stddef.h>
#include <stdint.h>

#include "bz_core.h"
#include "bz_stk.h"

void host_link_init(bz_stk *s);
void host_poll(void);
void host_log_exchange(const bz_apdu *a, const uint8_t *rsp, size_t rsp_len,
                       uint16_t sw);

#endif /* BZ_HOST_LINK_H */
