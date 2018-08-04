def create_steering_control(packer, idx, apply_steer, left3, lkas_request, checksum):

  values = {
    "Counter": idx,
    "LKAS_Output": apply_steer,
    "Left_Turn_Is_3": left3,
    "LKAS_Request": lkas_request,
    "Checksum": checksum
  }

  return packer.make_can_msg("ES_LKAS", 0, values)