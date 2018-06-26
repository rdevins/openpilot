#!/usr/bin/env python
from cereal import car
from common.realtime import sec_since_boot
from selfdrive.config import Conversions as CV
from selfdrive.controls.lib.drive_helpers import create_event, EventTypes as ET
from selfdrive.controls.lib.vehicle_model import VehicleModel
from selfdrive.car.subaru.values import DBC, CAR
from selfdrive.car.subaru.carstate import CarState, CruiseButtons, get_powertrain_can_parser

try:
  from selfdrive.car.subaru.carcontroller import CarController
except ImportError:
  CarController = None


class CanBus(object):
  def __init__(self):
    self.powertrain = 0
    self.obstacle = 1
    self.chassis = 2
    self.sw_gmlan = 3

class CarInterface(object):
  def __init__(self, CP, sendcan=None):
    self.CP = CP

    self.frame = 0
    self.gas_pressed_prev = False
    self.brake_pressed_prev = False
    self.can_invalid_count = 0
    self.acc_active_prev = 0

    # *** init the major players ***
    canbus = CanBus()
    self.CS = CarState(CP, canbus)
    self.pt_cp = get_powertrain_can_parser(CP, canbus)
    self.ch_cp_dbc_name = DBC[CP.carFingerprint]['powertrain']

    # sending if read only is False
    if sendcan is not None:
      self.sendcan = sendcan
      self.CC = CarController(canbus, CP.carFingerprint)

  @staticmethod
  def compute_gb(accel, speed):
    return float(accel) / 4.0

  @staticmethod
  def calc_accel_override(a_ego, a_target, v_ego, v_target):
    return 1.0

  @staticmethod
  def get_params(candidate, fingerprint):
    ret = car.CarParams.new_message()

    ret.carName = "subaru"
    ret.carFingerprint = candidate

    ret.enableCruise = False

    # TODO: gate this on detection
    ret.enableCamera = True
	
	
    std_cargo = 136
    mass_outback = 3642 + std_cargo
    wheelbase_outback = 2.75
    centerToFront_outback = wheelbase_outback * 0.5 + 1
    centerToRear_outback = wheelbase_outback - centerToFront_outback
    rotationalInertia_outback = 2500
    tireStiffnessFront_outback = 85400
    tireStiffnessRear_outback = 90000
    centerToRear = ret.wheelbase - ret.centerToFront

    if candidate == CAR.OUTBACK:
      ret.mass = mass_outback
      ret.safetyModel = car.CarParams.SafetyModels.subaru
      ret.wheelbase = wheelbase_outback
      ret.centerToFront = centerToFront_outback
      ret.steerRatio = 14
      ret.rotationalInertia = rotationalInertia_outback * \
                            ret.mass * ret.wheelbase**2 / (mass_outback * wheelbase_outback**2)

    ret.tireStiffnessFront = tireStiffnessFront_outback * \
                             ret.mass / mass_outback * \
                             (centerToRear / ret.wheelbase) / (centerToRear_outback / wheelbase_outback)
    ret.tireStiffnessRear = tireStiffnessRear_outback * \
                            ret.mass / mass_outback * \
                            (ret.centerToFront / ret.wheelbase) / (centerToFront_outback / wheelbase_outback)


    # same tuning for Volt and CT6 for now
    ret.steerKiBP, ret.steerKpBP = [[0.], [0.]]
    ret.steerKpV, ret.steerKiV = [[0.2], [0.00]]
    ret.steerKf = 0.00004   # full torque for 20 deg at 80mph means 0.00007818594

    ret.steerMaxBP = [0.] # m/s
    ret.steerMaxV = [1.]
    ret.gasMaxBP = [0.]
    ret.gasMaxV = [.5]
    ret.brakeMaxBP = [0.]
    ret.brakeMaxV = [1.]
    ret.longPidDeadzoneBP = [0.]
    ret.longPidDeadzoneV = [0.]

    ret.longitudinalKpBP = [5., 35.]
    ret.longitudinalKpV = [2.4, 1.5]
    ret.longitudinalKiBP = [0.]
    ret.longitudinalKiV = [0.36]

    ret.steerLimitAlert = True

    ret.stoppingControl = True
    ret.startAccel = 0.8

    ret.steerActuatorDelay = 0.1  # Default delay, not measured yet
    ret.steerRateCost = 0.5
    ret.steerControlType = car.CarParams.SteerControlType.torque

    return ret

  # returns a car.CarState
  def update(self, c):

    self.pt_cp.update(int(sec_since_boot() * 1e9), False)
    self.CS.update(self.pt_cp)

    # create message
    ret = car.CarState.new_message()

    # speeds
    ret.vEgo = self.CS.v_ego
    ret.aEgo = self.CS.a_ego
    ret.vEgoRaw = self.CS.v_ego_raw
    ret.yawRate = self.VM.yaw_rate(self.CS.angle_steers * CV.DEG_TO_RAD, self.CS.v_ego)
    ret.standstill = self.CS.standstill

    # steering wheel
    ret.steeringAngle = self.CS.angle_steers

    # torque and user override. Driver awareness
    # timer resets when the user uses the steering wheel.
    ret.steeringTorque = self.CS.steer_torque_driver

    # cruise state
    ret.cruiseState.available = bool(self.CS.main_on)
    ret.leftBlinker = self.CS.left_blinker_on
    ret.rightBlinker = self.CS.right_blinker_on


    buttonEvents = []

    # blinkers
    if self.CS.left_blinker_on != self.CS.prev_left_blinker_on:
      be = car.CarState.ButtonEvent.new_message()
      be.type = 'leftBlinker'
      be.pressed = self.CS.left_blinker_on
      buttonEvents.append(be)

    if self.CS.right_blinker_on != self.CS.prev_right_blinker_on:
      be = car.CarState.ButtonEvent.new_message()
      be.type = 'rightBlinker'
      be.pressed = self.CS.right_blinker_on
      buttonEvents.append(be)


    events = []
    if not self.CS.can_valid:
      self.can_invalid_count += 1
      if self.can_invalid_count >= 5:
        events.append(create_event('commIssue', [ET.NO_ENTRY, ET.IMMEDIATE_DISABLE]))
    else:
      self.can_invalid_count = 0

    if self.CS.acc_active and not self.acc_active_prev:
      events.append(create_event('pcmEnable', [ET.ENABLE]))
    if not self.CS.acc_active:
      events.append(create_event('pcmDisable', [ET.USER_DISABLE]))
		
    ret.events = events

    # update previous brake/gas pressed
    self.acc_active_prev = self.CS.acc_active


    # cast to reader so it can't be modified
    return ret.as_reader()

 def apply(self, c):

    self.CC.update(self.sendcan, c.enabled, self.CS, self.frame, c.actuators)

    self.frame += 1
