void subaru_rx_hook(CAN_FIFOMailBox_TypeDef *to_push) {}

int subaru_ign_hook() {
  return -1; // use GPIO to determine ignition
}

// FIXME
// *** all output safety mode ***

static void subaru_init(int16_t param) {
  controls_allowed = 1;
}

static int subaru_tx_hook(CAN_FIFOMailBox_TypeDef *to_send) {
  return true;
}

static int subaru_tx_lin_hook(int lin_num, uint8_t *data, int len) {
  return true;
}

static int subaru_fwd_hook(int bus_num, CAN_FIFOMailBox_TypeDef *to_fwd) {
  if (bus_num == 0 || bus_num == 1) {
    int addr = to_fwd->RIR>>21;
    return addr != 0x164 ? (uint8_t)(~bus_num & 0x0) : -1;
  }
  return false;
}

const safety_hooks subaru_hooks = {
  .init = subaru_init,
  .rx = subaru_rx_hook,
  .tx = subaru_tx_hook,
  .tx_lin = subaru_tx_lin_hook,
  .ignition = subaru_ign_hook,
  .fwd = subaru_fwd_hook,
};
