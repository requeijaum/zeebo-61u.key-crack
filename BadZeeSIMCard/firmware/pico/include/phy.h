#ifndef BZ_PHY_H
#define BZ_PHY_H

#include <stddef.h>
#include <stdint.h>

void phy_init(void);
uint32_t phy_measure_etu(void);
uint32_t phy_etu_us(void);
int phy_wait_reset(uint32_t timeout_us);
void phy_send_atr(void);
void phy_send_block(const uint8_t *buf, size_t n);
void phy_send_response(const uint8_t *buf, size_t n, uint16_t sw);
int phy_recv_apdu(uint8_t *buf, size_t cap, uint32_t first_byte_timeout_us);

#endif /* BZ_PHY_H */
