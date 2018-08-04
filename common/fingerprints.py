import os
from common.basedir import BASEDIR

def get_fingerprint_list():
  # read all the folders in selfdrive/car and return a dict where:
  # - keys are all the car models for which we have a fingerprint
  # - values are lists dicts of messages that constitute the unique 
  #   CAN fingerprint of each car model and all its variants
  fingerprints = {}
  for car_folder in [x[0] for x in os.walk(BASEDIR + '/selfdrive/car')]:
    try:
      car_name = car_folder.split('/')[-1]
      values = __import__('selfdrive.car.%s.values' % car_name, fromlist=['FINGERPRINTS'])
      if hasattr(values, 'FINGERPRINTS'):
        car_fingerprints = values.FINGERPRINTS
      else:
        continue
      for f, v in car_fingerprints.items():
        fingerprints[f] = v
    except (ImportError, IOError):
      pass
  return fingerprints


_FINGERPRINTS = get_fingerprint_list()

_DEBUG_ADDRESS = {1880: 8}   # reserved for debug purposes

def is_valid_for_fingerprint(msg, car_fingerprint):
  adr = msg.address
  bus = msg.src
  # ignore addresses that are more than 11 bits
  return (adr in car_fingerprint and car_fingerprint[adr] == len(msg.dat)) or \
         bus != 0 or adr >= 0x800


def eliminate_incompatible_cars(msg, candidate_cars):
  """Removes cars that could not have sent msg.

     Inputs:
      msg: A cereal/log CanData message from the car.
      candidate_cars: A list of cars to consider.

     Returns:
      A list containing the subset of candidate_cars that could have sent msg.
  """
  compatible_cars = []

  for car_name in candidate_cars:
    car_fingerprints = _FINGERPRINTS[car_name]

    for fingerprint in car_fingerprints:
      fingerprint.update(_DEBUG_ADDRESS)  # add alien debug address

      if is_valid_for_fingerprint(msg, fingerprint):
        compatible_cars.append(car_name)
        break

  return compatible_cars


def all_known_cars():
  """Returns a list of all known car strings."""
  return _FINGERPRINTS.keys()

  # for usb controller
def fingerprint(logcan):
  import selfdrive.messaging as messaging
  from cereal import car
  from common.realtime import sec_since_boot
  import os
  if os.getenv("SIMULATOR") is not None or logcan is None:
    # send message
    ret = car.CarParams.new_message()

    ret.carName = "simulator"
    ret.carFingerprint = "THE LOW QUALITY SIMULATOR"

    #ret.enableSteer = True
    #ret.enableBrake = True
    #ret.enableGas = True
    #ret.enableCruise = False

    #ret.wheelBase = 2.67
    #ret.steerRatio = 15.3
    #ret.slipFactor = 0.0014

    ret.steerKpDEPRECATED, ret.steerKiDEPRECATED = 12.0, 1.0
    return ret

  print "waiting for fingerprint..."
  brake_only = True

  candidate_cars = all_known_cars()
  finger = {}
  st = None
  while 1:
    for a in messaging.drain_sock(logcan, wait_for_one=True):
      if st is None:
        st = sec_since_boot()
      for can in a.can:
        # pedal
        if can.address == 0x201 and can.src == 0:
          brake_only = False
        if can.src == 0:
          finger[can.address] = len(can.dat)
        candidate_cars = eliminate_incompatible_cars(can, candidate_cars)

    # if we only have one car choice and it's been 100ms since we got our first message, exit
    if len(candidate_cars) == 1 and st is not None and (sec_since_boot()-st) > 0.1:
      break
    elif len(candidate_cars) == 0:
      print map(hex, finger.keys())
      raise Exception("car doesn't match any fingerprints")

  print "fingerprinted", candidate_cars[0]

  # send message
  ret = car.CarParams.new_message()

  ret.carName = "subaru"
  ret.carFingerprint = candidate_cars[0]

  #ret.enableSteer = True
  #ret.enableBrake = True
  #ret.enableGas = not brake_only
  #ret.enableCruise = brake_only
  #ret.enableCruise = False

  #ret.wheelBase = 2.67
  #ret.steerRatio = 15.3
  #ret.slipFactor = 0.0014

  if candidate_cars[0] == "HONDA CIVIC 2016 TOURING":
    ret.steerKp, ret.steerKi = 12.0, 1.0
  elif candidate_cars[0] == "ACURA ILX 2016 ACURAWATCH PLUS":
    if not brake_only:
      # assuming if we have an interceptor we also have a torque mod
      ret.steerKp, ret.steerKi = 6.0, 0.5
    else:
      ret.steerKp, ret.steerKi = 12.0, 1.0
  elif candidate_cars[0] == "HONDA ACCORD 2016 TOURING":
    ret.steerKp, ret.steerKi = 12.0, 1.0
  elif candidate_cars[0] == "SUBARU XV ACTIVE 2018":
  # FIXME: add real values
    ret.steerKpDEPRECATED, ret.steerKiDEPRECATED = 12.0, 1.0
  else:
    raise ValueError("unsupported car %s" % candidate_cars[0])

  return ret