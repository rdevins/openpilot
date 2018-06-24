from common.numpy_fast import clip, interp
from common.realtime import sec_since_boot
from selfdrive.config import Conversions as CV
from selfdrive.boardd.boardd import can_list_to_can_capnp
from selfdrive.car.subaru import subarucan
from selfdrive.car.subaru.values import CAR, DBC
from selfdrive.can.packer import CANPacker


class CarControllerParams():
  def __init__(self, car_fingerprint):
    self.STEER_MAX = 1023
    self.STEER_STEP = 1                # how often we update the steer cmd
    self.STEER_DELTA_UP = 7            # ~0.75s time to peak torque (255/50hz/0.75s)
    self.STEER_DELTA_DOWN = 17         # ~0.3s from peak torque to zero
    self.STEER_DRIVER_ALLOWANCE = 50   # allowed driver torque before start limiting
    self.STEER_DRIVER_MULTIPLIER = 4   # weight driver torque heavily
    self.STEER_DRIVER_FACTOR = 100     # from dbc


class CarController(object):
  def __init__(self, canbus, car_fingerprint):
    self.start_time = sec_since_boot()
    self.lkas_active = False
    self.steer_idx = 0
    self.apply_steer_last = 0
    self.car_fingerprint = car_fingerprint

    # Setup detection helper. Routes commands to
    # an appropriate CAN bus number.
    self.canbus = canbus
    self.params = CarControllerParams(car_fingerprint)
    self.packer_ch = CANPacker(DBC[car_fingerprint]['powertrain'])

  def update(self, sendcan, enabled, CS, frame, actuators, ):
    """ Controls thread """

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

      lkas_enabled = enabled and not CS.steer_not_allowed and CS.v_ego > 3.

      if not lkas_enabled:
        apply_steer = 0

      apply_steer = int(round(apply_steer))
      self.apply_steer_last = apply_steer
      idx = (frame / P.STEER_STEP) % 4

      
      can_sends.append(subarucan.create_steering_control(self.packer_pt, canbus.powertrain, apply_steer, idx, lkas_enabled))

    sendcan.send(can_list_to_can_capnp(can_sends, msgtype='sendcan').to_bytes())
	
	'''
	commands only old:
class CarController(object):
  def __init__(self, dbc_name, enable_camera=True):
    self.enable_camera = enable_camera
    self.packer = CANPacker(dbc_name)

  def update(self, sendcan, enabled, CS, frame, actuators):
  if not self.enable_camera:
      return
	  
    STEER_MAX = 0x3FF
    apply_steer = int(clip(-actuators.steer * STEER_MAX, -STEER_MAX, STEER_MAX))
    lkas_active = enabled and not CS.steer_not_allowed
    can_sends = []
    idx = frame % 4
    can_sends.append(subarucan.create_steering_control(self.packer, apply_steer, lkas_active, CS.CP.carFingerprint, idx))

    sendcan.send(can_list_to_can_capnp(can_sends, msgtype='sendcan').to_bytes())

    '''
	
	
'''
from collections import namedtuple
import os
from selfdrive.boardd.boardd import can_list_to_can_capnp
from selfdrive.controls.lib.drive_helpers import rate_limit
from common.numpy_fast import clip
from . import subarucan
from .values import AH
from common.fingerprints import SUBARU as CAR
from selfdrive.can.packer import CANPacker



class CarController(object):
  def __init__(self, dbc_name, enable_camera=True):
    self.enable_camera = enable_camera
    self.packer = CANPacker(dbc_name)

  def update(self, sendcan, enabled, CS, frame, actuators):

    """ Controls thread """

    if not self.enable_camera:
      return

    # **** process the car messages ****

    # *** compute control surfaces ***
    STEER_MAX = 0x3FF

    # steer torque is converted back to CAN reference (positive when steering right)
    apply_steer = int(clip(-actuators.steer * STEER_MAX, -STEER_MAX, STEER_MAX))

    # any other cp.vl[0x18F]['STEER_STATUS'] is common and can happen during user override. sending 0 torque to avoid EPS sending error 5
    lkas_active = enabled and not CS.steer_not_allowed

    # Send CAN commands.
    can_sends = []

    # Send steering command.
    idx = frame % 4
    can_sends.append(subarucan.create_steering_control(self.packer, apply_steer, lkas_active, CS.CP.carFingerprint, idx))

    sendcan.send(can_list_to_can_capnp(can_sends, msgtype='sendcan').to_bytes())
	'''
	
