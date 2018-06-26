from cereal import car
from selfdrive.car import dbc_dict

class CAR:
  OUTBACK = "SUBARU OUTBACK PREMIUM 2015"


FINGERPRINTS = {
CAR.OUTBACK: [{
    2L: 8, 320L: 8, 321L: 8, 328L: 8, 329L: 8, 208L: 8, 209L: 8, 210L: 8, 211L: 8, 212L: 8, 324L: 8, 336L: 8, 346L: 8, 356L: 8, 640L: 8, 881L: 8, 392L: 8, 880L: 8, 352L: 8, 353L: 8, 354L: 8, 358L: 8, 359L: 8, 864L: 8, 865L: 8, 866L: 8, 872L: 8, 338L: 8, 342L: 8, 642L: 8, 977L: 8, 644L: 8, 882L: 8, 1632L: 8, 884L: 8, 1745L: 8, 1786L: 8, 352L: 8, 353L: 8, 354L: 8, 358L: 8, 359L: 8,
    # sent messages
    0x164: 8,
  }],
}

DBC = {
  CAR.OUTBACK: dbc_dict('subaru_outback_2015_eyesight', 'powertrain'),
}