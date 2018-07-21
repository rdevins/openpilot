from selfdrive.car.subaru.values import CAR, DBC
from selfdrive.can.parser import CANParser
from selfdrive.config import Conversions as CV
from common.kalman.simple_kalman import KF1D
import numpy as np


def parse_gear_shifter(can_gear, car_fingerprint):
    return "drive"


def get_can_parser(CP):

  signals = [
    # sig_name, sig_address, default
    ("FL", "WHEEL_SPEEDS", 0),
    ("FR", "WHEEL_SPEEDS", 0),
    ("RL", "WHEEL_SPEEDS", 0),
    ("RR", "WHEEL_SPEEDS", 0),
    ("Steering_Angle", "Steering", 0),
    ("Steer_Torque_Sensor", "Steering_Torque", 0),
    ("Cruise_Activated", "ES_Status", 0),
    ("LEFT_BLINKER", "Dashlights", 0), 
    ("RIGHT_BLINKER", "Dashlights", 0),
    ("Gear", "Transmission", 0),
  ]
  checks = [
    # sig_address, frequency
    ("Dashlights", 10),
    ("ES_Status", 20),
    ("Steering", 100),
    ("WHEEL_SPEEDS", 50),
    ("Steering_Torque", 100),
    ("Transmission", 100),
  ]

  return CANParser(DBC[CP.carFingerprint]['pt'], signals, checks, 0)


class CarState(object):
  def __init__(self, CP):

    self.CP = CP
    self.left_blinker_on = 0
    self.right_blinker_on = 0

    # initialize can parser
    self.car_fingerprint = CP.carFingerprint

    # vEgo kalman filter
    dt = 0.01
    # Q = np.matrix([[10.0, 0.0], [0.0, 100.0]])
    # R = 1e3
    self.v_ego_kf = KF1D(x0=np.matrix([[0.0], [0.0]]),
                         A=np.matrix([[1.0, dt], [0.0, 1.0]]),
                         C=np.matrix([1.0, 0.0]),
                         K=np.matrix([[0.12287673], [0.29666309]]))
    self.v_ego = 0.0

  def update(self, cp):
    # copy can_valid
    self.can_valid = cp.can_valid

    # update prevs, update must run once per loop
    self.prev_left_blinker_on = self.left_blinker_on
    self.prev_right_blinker_on = self.right_blinker_on

    self.door_all_closed = cp.vl["ES_Status"]['Cruise_Activated']
    self.seatbelt = cp.vl["ES_Status"]['Cruise_Activated']
    
    self.brake_pressed = not cp.vl["ES_Status"]['Cruise_Activated']
    self.esp_disabled = False
    self.park_brake = False
    self.acc_active = cp.vl["ES_Status"]['Cruise_Activated']
    self.pcm_acc_status = int(self.acc_active)
    self.pedal_gas = 0
    self.car_gas = 0
    self.main_on = cp.vl["ES_Status"]['Cruise_Activated']

    # calc best v_ego estimate, by averaging two opposite corners
    self.v_wheel_fl = cp.vl["WHEEL_SPEEDS"]['FL'] * CV.KPH_TO_MS
    self.v_wheel_fr = cp.vl["WHEEL_SPEEDS"]['FR'] * CV.KPH_TO_MS
    self.v_wheel_rl = cp.vl["WHEEL_SPEEDS"]['RL'] * CV.KPH_TO_MS
    self.v_wheel_rr = cp.vl["WHEEL_SPEEDS"]['RR'] * CV.KPH_TO_MS
    self.v_wheel = (self.v_wheel_fl + self.v_wheel_fr + self.v_wheel_rl + self.v_wheel_rr) / 4.
    if self.car_fingerprint == CAR.OUTBACK:
      self.v_wheel = self.v_wheel * 1.03 # There is a 3.4 percent error on OUTBACK.

    # Kalman filter
    if abs(self.v_wheel - self.v_ego) > 2.0:  # Prevent large accelerations when car starts at non zero speed
      self.v_ego_x = np.matrix([[self.v_wheel], [0.0]])

    self.v_ego_raw = self.v_wheel
    v_ego_x = self.v_ego_kf.update(self.v_wheel)
    self.v_ego = float(v_ego_x[0])
    self.a_ego = float(v_ego_x[1])
    self.standstill = not self.v_wheel > 0.001

    self.angle_steers = pt_cp.vl["Steering"]['Steering_Angle']
    self.left_blinker_on = cp.vl["Dashlights"]['LEFT_BLINKER']
    self.right_blinker_on = cp.vl["Dashlights"]['RIGHT_BLINKER']

    self.steer_torque_driver = cp.vl["Steering_Torque"]['Steer_Torque_Sensor']
    self.steer_override = abs(self.steer_torque_driver) > 500.0
    self.steer_torque_motor = cp.vl["Steering_Torque"]['Steering_Motor_LeftRight']

    # 2 is standby, 10 is active. TODO: check that everything else is really a faulty state
    self.steer_state = cp.vl["ES_Status"]['Cruise_Activated'] #0 NOT ACTIVE, 1 ACTIVE
    self.steer_error = False  #not cp.vl["MDPS12"]['CF_Mdps_FailStat'] or cp.vl["MDPS12"]['CF_Mdps_ToiUnavail'] ## TODO: VERIFY THIS
    self.brake_error = False

    self.user_brake = 0

    can_gear = cp.vl["Transmission"]['Gear']
    self.brake_pressed = cp.vl["ES_Status"]['Cruise_Activated']
    self.brake_lights = bool(self.brake_pressed)
    self.gear_shifter = parse_gear_shifter(can_gear, self.car_fingerprint)

    #For LKAS Passthrough
