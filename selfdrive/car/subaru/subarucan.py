def create_steering_control(packer, bus, apply_steer, idx, left_3, lkas_active):

  values = {
    "Counter": idx,
    "LKAS_Output": apply_steer,
    "Left_Turn_Is_3": left3,
    "LKAS_Request": lkas_request,
    "Checksum": checksum
  }

  return packer.make_can_msg("ES_LKAS", bus, values)
