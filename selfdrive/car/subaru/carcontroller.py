from common.numpy_fast import clip, interp
from selfdrive.boardd.boardd import can_list_to_can_capnp
from selfdrive.car.subaru.subarucan import make_can_msg, create_steer
from selfdrive.car.subaru.values import ECU, STATIC_MSGS
from selfdrive.can.packer import CANPacker


# Steer torque limits
STEER_MAX = 240
STEER_DELTA = 25      
STEER_DELTA_UP = 10            # ~0.75s time to peak torque (255/50hz/0.75s)
STEER_DELTA_DOWN = 50         # ~0.3s from peak torque to zero
TARGET_IDS = [0x164]


class CarController(object):
  def __init__(self, dbc_name, car_fingerprint, enable_camera):
    self.braking = False
    self.controls_allowed = True
    self.last_steer = 0
    self.car_fingerprint = car_fingerprint
    self.angle_control = False
    self.idx = 0
    self.lkas_request = 0
    self.lanes = 0
    self.steer_angle_enabled = False
    self.ipas_reset_counter = 0
    self.turning_inhibit = 0
    self.apply_steer_last = 0

    self.fake_ecus = set()
    if enable_camera: self.fake_ecus.add(ECU.CAM)
    self.packer = CANPacker(dbc_name)

  def update(self, sendcan, enabled, CS, frame, actuators):
  
    P = self.params

    # Send CAN commands.
    can_sends = []
    canbus = self.canbus
    
    ### STEER ###

    if (frame % P.STEER_STEP) == 0:
      final_steer = actuators.steer if enabled else 0.
      apply_steer = final_steer * P.STEER_MAX

      # limits due to driver torque
      driver_max_torque = P.STEER_MAX + (P.STEER_DRIVER_ALLOWANCE + CS.steer_torque_driver * P.STEER_DRIVER_FACTOR) * P.STEER_DRIVER_MULTIPLIER
      driver_min_torque = -P.STEER_MAX + (-P.STEER_DRIVER_ALLOWANCE + CS.steer_torque_driver * P.STEER_DRIVER_FACTOR) * P.STEER_DRIVER_MULTIPLIER
      max_steer_allowed = max(min(P.STEER_MAX, driver_max_torque), 0)
      min_steer_allowed = min(max(-P.STEER_MAX, driver_min_torque), 0)
      apply_steer = clip(apply_steer, min_steer_allowed, max_steer_allowed)

      # slow rate if steer torque increases in magnitude
      if self.apply_steer_last > 0:
        apply_steer = clip(apply_steer, max(self.apply_steer_last - P.STEER_DELTA_DOWN, -P.STEER_DELTA_UP), self.apply_steer_last + P.STEER_DELTA_UP)
      else:
        apply_steer = clip(apply_steer, self.apply_steer_last - P.STEER_DELTA_UP, min(self.apply_steer_last + P.STEER_DELTA_DOWN, P.STEER_DELTA_UP))

      apply_steer = int(round(apply_steer))
      self.apply_steer_last = apply_steer

    # Inhibits *outside of* alerts
    #    Because the Turning Indicator Status is based on Lights and not Stalk, latching is 
    #    needed for the disable to work.
    if CS.left_blinker_on == 1 or CS.right_blinker_on == 1:
      self.turning_inhibit = 50  # Disable for 0.5 Seconds after blinker turned off

    if self.turning_inhibit > 0:
      self.turning_inhibit = self.turning_inhibit - 1

    if not enabled or self.turning_inhibit > 0:
      apply_steer = 0
      final_steer = 0

      
    can_sends = []

    # Limit Terminal Debugging to 5Hz
    if (frame % 20) == 0:
      print "controlsdDebug steer", actuators.steer, "bi", self.turning_inhibit, "spd", \
        CS.v_ego, "strAng", CS.angle_steers, "strToq", CS.steer_torque_driver
      
    if self.car_fingerprint == CAR.OUTBACK:

      if abs(actuators.steer) > 0.001:
        lkas_request = 1
      else :
        lkas_request = 0
      
      #counts from 0 to 7 then back to 0
      idx = frame % 8 

      if not lkas_enabled:
        apply_steer = 0

      if apply_steer < 0:
        left3 = 24
      else:
        left3 = 0
       
      #Max steer = 1023
      if actuators.steer < 0:
        chksm_steer = 1024-abs(apply_steer)
      else:
        chksm_steer = apply_steer
        
      steer2 = (chksm_steer >> 8) & 0x7
      steer1 =  chksm_steer - (steer2 << 8)
      checksum = (idx + steer1 + steer2 + left3 + lkas_request) % 256
      
      if (frame % 2) == 0:
        can_sends.append(subarucan.create_steering_control(self.packer, idx, apply_steer, left3, lkas_request, checksum))

    sendcan.send(can_list_to_can_capnp(can_sends, msgtype='sendcan').to_bytes())