import numpy as np
from cereal import car
from common.kalman.simple_kalman import KF1D
from selfdrive.config import Conversions as CV
from selfdrive.can.parser import CANParser
from selfdrive.car.subaru.values import DBC, CAR

def get_powertrain_can_parser(CP, canbus):
  # this function generates lists for signal, messages and initial values
  signals = [
    # sig_name, sig_address, default
    ("LEFT_BLINKER", "Dashlights", 0), 
    ("RIGHT_BLINKER", "Dashlights", 0),
    ("Steering_Angle", "Steering", 0),
    ("Steering_Angle", "Steering_Torque", 0),
    ("FL", "WHEEL_SPEEDS", 0), 
    ("FR", "WHEEL_SPEEDS", 0),
    ("RL", "WHEEL_SPEEDS", 0), 
    ("RR", "WHEEL_SPEEDS", 0), 
    ("Steer_Torque_Sensor", "Steering_Torque", 0),
    ("Cruise_On", "CruiseControl", 0), 
    ("Cruise_Activated", "CruiseControl", 0), 
  ]
  
  checks = [
    # sig_address, frequency
    ("Dashlights", 10),
    ("CruiseControl", 20),
    ("Steering", 100),
    ("WHEEL_SPEEDS", 50),
    ("Steering_Torque", 100),
  ]

  return CANParser(DBC[CP.carFingerprint]['pt'], signals, checks, canbus.powertrain)

def get_camera_parser(CP, canbus):
  
  signals = [
    # sig_name, sig_address, default
    ("Cruise_On", "ES_Status", 0)
    ("Cruise_Activated", "ES_Status", 0)
    ("WHEELS_MOVING_2015", "ES_Status", 0)
    ("Cruise_On", "ES_Brake", 0)
    ("Saved_Speed", "ES_Status", 0)
    ("Cruise_On", "ES_CruiseThrottle", 0)
    ("All_depart_2015", "ES_LDW", 0)
  ]

  checks = []

  return CANParser(DBC[CP.carFingerprint]['pt'], signals, checks, canbus.camera)

class CarState(object):
  def __init__(self, CP, canbus):
    # initialize can parser
    self.CP = CP
    
    self.car_fingerprint = CP.carFingerprint
    self.left_blinker_on = False
    self.prev_left_blinker_on = False
    self.right_blinker_on = False
    self.prev_right_blinker_on = False
    self.steer_torque_driver = 0
    self.steer_not_allowed = False
    self.main_on = False

    # vEgo kalman filter
    dt = 0.01
    self.v_ego_kf = KF1D(x0=np.matrix([[0.], [0.]]),
                         A=np.matrix([[1., dt], [0., 1.]]),
                         C=np.matrix([1., 0.]),
                         K=np.matrix([[0.12287673], [0.29666309]]))
    self.v_ego = 0.

  def update(self, pt_cp, cam_cp):

    self.can_valid = True
    
    self.v_wheel_fl = pt_cp.vl["WHEEL_SPEEDS"]['FL'] * CV.KPH_TO_MS
    self.v_wheel_fr = pt_cp.vl["WHEEL_SPEEDS"]['FR'] * CV.KPH_TO_MS
    self.v_wheel_rl = pt_cp.vl["WHEEL_SPEEDS"]['RL'] * CV.KPH_TO_MS
    self.v_wheel_rr = pt_cp.vl["WHEEL_SPEEDS"]['RR'] * CV.KPH_TO_MS
    speed_estimate = float(np.mean([self.v_wheel_fl, self.v_wheel_fr, self.v_wheel_rl, self.v_wheel_rr]))

    self.v_ego_raw = speed_estimate
    v_ego_x = self.v_ego_kf.update(speed_estimate)
    self.v_ego = float(v_ego_x[0])
    self.a_ego = float(v_ego_x[1])
    self.standstill = self.v_ego_raw < 0.01

    self.prev_left_blinker_on = self.left_blinker_on
    self.prev_right_blinker_on = self.right_blinker_on
    self.left_blinker_on = pt_cp.vl["Dashlights"]['LEFT_BLINKER'] == 1
    self.right_blinker_on = pt_cp.vl["Dashlights"]['RIGHT_BLINKER'] == 1
    self.steer_torque_driver = pt_cp.vl["Steering_Torque"]['Steer_Torque_Sensor']

    if self.car_fingerprint in (CAR.OUTBACK, CAR.LEGACY):
      self.steer_override = abs(self.steer_torque_driver) > 35
      self.angle_steers = pt_cp.vl["Steering_Torque"]['Steering_Angle']
      self.acc_active = pt_cp.vl["CruiseControl"]['Cruise_Activated'] or cam_cp.vl["ES_LDW"]['All_depart_2015']
      self.main_on = pt_cp.vl["CruiseControl"]['Cruise_On'] or cam_cp.vl["ES_LDW"]['All_depart_2015']
      self.standstill = cam_cp.vl["ES_Status"]['WHEELS_MOVING_2015']
      self.saved_speed = cam_cp.vl["ES_Status"]['Saved_Speed']
      self.lead_car = cam_cp.vl["ES_Status"]['Car_Follow']
      self.lead_car_far = cam_cp.vl["ES_Status"]['Obstacle_Distance']
      self.lead_car_close = cam_cp.vl["ES_Status"]['CloseDistance']
      self.distance_swap = cam_cp.vl["ES_Status"]['DistanceSwap']

    if self.car_fingerprint == CAR.XV2018:  
      self.steer_override = abs(self.steer_torque_driver) > 250.0
      self.angle_steers = pt_cp.vl["Steering"]['Steering_Angle']
      self.acc_active = pt_cp.vl["CruiseControl"]['Cruise_Activated'] 
      self.main_on = pt_cp.vl["CruiseControl"]['Cruise_On']
