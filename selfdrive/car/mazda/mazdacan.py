from selfdrive.car.mazda.values import CAR, DBC

def create_steering_control(packer, bus, car_fingerprint, idx, steer1, byte2, checksum):
  if car_fingerprint == CAR.CX5:
    values = {
      "Byte0": idx,
      "Byte1": steer1,
      "Byte2": byte2,
      "Byte3": 1 if steer1 + byte2 != 0 else 0,
      "Checksum": checksum
    }
    
  return packer.make_can_msg("ES_LKAS", 0, values)
