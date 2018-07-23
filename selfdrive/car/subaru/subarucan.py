def create_steering_control(packer, bus, idx, steer1, steer2, left3, lkas_request, checksum):

  values = {
    "Byte0": idx,
    "Byte1": steer1,
    "Byte2": steer2,
    "Left_Turn_Is_3": left3,
    "Byte3": lkas_request,
    "Checksum": checksum,
  }

  return packer.make_can_msg("ES_LKAS", 0, values)
