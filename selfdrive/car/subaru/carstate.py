import numpy as np
from cereal import car
from common.kalman.simple_kalman import KF1D
from selfdrive.config import Conversions as CV
from selfdrive.can.parser import CANParser
from selfdrive.car.subaru.values import DBC, CAR, parse_gear_shifter, \
                                    CruiseButtons, is_eps_status_ok

def get_powertrain_can_parser(CP, canbus):
  # this function generates lists for signal, messages and initial values
  signals = [
    # sig_name, sig_address, default
    ("LEFT_BLINKER", "Dashlights", 0), #SUBARU
    ("RIGHT_BLINKER", "Dashlights", 0), #SUBARU
    ("Cruise_Activated", "ES_Status", 0 #SUBARU
    ("SteeringAngle", "Steering_Angle", 0), #SUBARU
    ("FL", "WHEEL_SPEEDS", 0), #SUBARU
    ("FR", "WHEEL_SPEEDS", 0), #SUBARU
    ("RL", "WHEEL_SPEEDS", 0), #SUBARU
    ("RR", "WHEEL_SPEEDS", 0), #SUBARU
    ("Steer_Torque_Sensor", "Steering_Torque", 0), #SUBARU
    ("LKAS_Request", "ES_LKAS", 0), #SUBARU
  ]

  return CANParser(DBC[CP.carFingerprint]['pt'], signals, [], canbus.powertrain)

class CarState(object):
  def __init__(self, CP, canbus):
    # initialize can parser

    self.car_fingerprint = CP.carFingerprint
    self.left_blinker_on = False
    self.prev_left_blinker_on = False
    self.right_blinker_on = False
    self.prev_right_blinker_on = False

    # vEgo kalman filter
    dt = 0.01
    self.v_ego_kf = KF1D(x0=np.matrix([[0.], [0.]]),
                         A=np.matrix([[1., dt], [0., 1.]]),
                         C=np.matrix([1., 0.]),
                         K=np.matrix([[0.12287673], [0.29666309]]))
    self.v_ego = 0.

  def update(self, pt_cp):

    self.can_valid = pt_cp.can_valid
    self.prev_cruise_buttons = self.cruise_buttons
    self.cruise_buttons = pt_cp.vl["ES_Status"]['Cruise_Activated'] #SUBARU

    self.v_wheel_fl = pt_cp.vl["WHEEL_SPEEDS"]['FL'] * CV.KPH_TO_MS #SUBARU
    self.v_wheel_fr = pt_cp.vl["WHEEL_SPEEDS"]['FR'] * CV.KPH_TO_MS #SUBARU
    self.v_wheel_rl = pt_cp.vl["WHEEL_SPEEDS"]['RL'] * CV.KPH_TO_MS #SUBARU
    self.v_wheel_rr = pt_cp.vl["WHEEL_SPEEDS"]['RR'] * CV.KPH_TO_MS #SUBARU
    speed_estimate = (self.v_wheel_fl + self.v_wheel_fr + self.v_wheel_rl + self.v_wheel_rr) / 4.0 #SUBARU

    self.v_ego_raw = speed_estimate #SUBARU
    v_ego_x = self.v_ego_kf.update(speed_estimate) #SUBARU
    self.v_ego = float(v_ego_x[0]) #SUBARU
    self.a_ego = float(v_ego_x[1]) #SUBARU

    self.standstill = self.v_ego_raw < 0.01 #SUBARU

    self.angle_steers = pt_cp.vl["Steering_Angle"]['SteeringAngle'] #SUBARU
    self.steer_torque_driver = pt_cp.vl["Steering_Torque"]['Steer_Torque_Sensor'] #SUBARU
    self.steer_override = abs(self.steer_torque_driver) > 1.0 #SUBARU

    self.can_valid = True

    self.prev_left_blinker_on = self.left_blinker_on #SUBARU
    self.prev_right_blinker_on = self.right_blinker_on #SUBARU
    self.left_blinker_on = pt_cp.vl["Dashlights"]['LEFT_BLINKER'] == 1 #SUBARU
    self.right_blinker_on = pt_cp.vl["Dashlights"]['RIGHT_BLINKER'] == 2 #SUBARU

      self.main_on = pt_cp.vl["ES_Status"]['Cruise_On'] #SUBARU
      self.acc_active = False
    else: 
      self.main_on = False
      self.acc_active = pt_cp.vl["ES_Status"]['Cruise_Activated'] #SUBARU
    if self.car_fingerprint == CAR.OUTBACK: #SUBARU
