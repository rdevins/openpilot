def create_steering_control(packer, bus, apply_steer, idx, lkas_active):

  values = 
    "RollingCounter": idx,
    "LKAS_Output": apply_steer,
	"Left_Turn_Is_3": left_3,
    "LKAS_Request": lkas_active,
    "LKASteeringCmdChecksum": ((lkas_active << 11) - (apply_steer & 0x7ff) + idx) % 256
  }

  return packer.make_can_msg("ES_LKAS", bus, values)
