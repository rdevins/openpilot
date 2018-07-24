def create_steering_control(packer, bus, idx, steer2, byte2, lkas_request, checksum):

  values = {
    "Byte0": idx,
    "Byte1": steer2,
    "Byte2": byte2,
    "Byte3": lkas_request,
    "Checksum": checksum,
  }

  return packer.make_can_msg("ES_LKAS", 0, values)

def create_es_brake(packer, bus, message_brake):

  values = {
    "Message": message_brake,
  }

  return packer.make_can_msg("ES_Brake", 0, values)

def create_es_rpm(packer, bus, message_rpm):

  values = {
    "Message": message_rpm,
  }

  return packer.make_can_msg("ES_RPM", 0, values)

def create_es_ldw(packer, bus, message_ldw):

  values = {
    "Message": message_ldw,
  }

  return packer.make_can_msg("ES_LDW", 0, values)

def create_es_cruisethrottle(packer, bus, message_ct):

  values = {
    "Message": message_ct,
  }

  return packer.make_can_msg("ES_CruiseThrottle", 0, values)

def create_es_status(packer, bus, message_status):

  values = {
    "Message": message_status,
  }

  return packer.make_can_msg("ES_Status", 0, values)
