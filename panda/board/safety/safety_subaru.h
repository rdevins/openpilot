// subaru Safety

static int subaru_ign_hook() {
  return true;
}
static void subaru_init(int16_t param) {
  controls_allowed = 1;
}

static int subaru_tx_hook(CAN_FIFOMailBox_TypeDef *to_send) {
  // Steering Value Safety Check
  
  return true;
}

static int subaru_tx_lin_hook(int lin_num, uint8_t *data, int len) {
  return true;
}

static int subaru_fwd_hook(int bus_num, CAN_FIFOMailBox_TypeDef *to_fwd) {
  return -1;
}

const safety_hooks subaru_hooks = {
  .init = subaru_init,
  .rx = default_rx_hook,
  .tx = subaru_tx_hook,
  .tx_lin = subaru_tx_lin_hook,
  .ignition = subaru_ign_hook,
  .fwd = subaru_fwd_hook,
};

