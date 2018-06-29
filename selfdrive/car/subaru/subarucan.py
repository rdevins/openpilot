def create_steering_control(packer, bus, apply_steer, idx, left_3, lkas_active):

  values = {
    "RollingCounter": idx, #counts 0 to 7 in 3 bits
    "LKAS_Output": apply_steer,
    "Left_Turn_Is_3": left_3, #needs if statement in carcontroller when LKAS_Output is a negative value
    "LKAS_Request": lkas_active,
    "Checksum": ((idx + apply_steer + left_3 + lkas_active) % 256) #placeholder checksum, needs bits shifted
  }

  return packer.make_can_msg("ES_LKAS", bus, values)
