def create_steering_control(packer, bus, idx, steer1, byte2, left3, lkas_request, checksum):

  values = {
    "Byte0": idx,
    "Byte1": steer2,
    "Byte2": byte2,
    "Byte3": lkas_request,
    "Checksum": checksum,
  }

  return packer.make_can_msg("ES_LKAS", 0, values)
