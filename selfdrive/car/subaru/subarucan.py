def create_steering_control(packer, bus, apply_steer, idx, lkas_active):

  values = 
    "RollingCounter": idx, #needs to count from 0 to 7, incrementing by 1 for every message sent. After 7, reset to 0
    "LKAS_Output": apply_steer,
    "Left_Turn_Is_3": left_3, #needs if statement implemented somewhere when LKAS_Output is a negative value
    "LKAS_Request": lkas_active,
    "Checksum": ((lkas_active << 11) - (apply_steer & 0x7ff) + idx) % 256 #placeholder checksum
  }

  return packer.make_can_msg("ES_LKAS", bus, values)
