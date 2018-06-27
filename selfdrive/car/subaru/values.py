from cereal import car
from selfdrive.car import dbc_dict

class CAR:
  OUTBACK = "SUBARU OUTBACK PREMIUM 2015"
  XV2018  = "SUBARU XV ACTIVE 2018"

FINGERPRINTS = {
CAR.OUTBACK: [{
    2L: 8, 320L: 8, 321L: 8, 328L: 8, 329L: 8, 208L: 8, 209L: 8, 210L: 8, 211L: 8, 212L: 8, 324L: 8, 336L: 8, 346L: 8, 356L: 8, 640L: 8, 881L: 8, 392L: 8, 880L: 8, 352L: 8, 353L: 8, 354L: 8, 358L: 8, 359L: 8, 864L: 8, 865L: 8, 866L: 8, 872L: 8, 338L: 8, 342L: 8, 642L: 8, 977L: 8, 644L: 8, 882L: 8, 1632L: 8, 884L: 8, 1745L: 8, 1786L: 8, 352L: 8, 353L: 8, 354L: 8, 358L: 8, 359L: 8,
    # sent messages
    0x164: 8,
  }],
CAR.XV2018: [{
        2: 8, 64: 8, 65: 8, 72: 8, 73: 8, 280: 8, 281: 8, 290: 8, 312: 8, 313: 8, 314: 8, 315: 8, 316: 8, 326: 8, 372: 8, 544: 8, 545: 8, 546: 8, 554: 8, 557: 8, 576: 8, 577: 8, 722: 8, 801: 8, 802: 8, 805: 8, 808: 8, 811: 8, 826: 8, 837: 8, 838: 8, 839: 8, 842: 8, 912: 8, 915: 8, 940: 8, 1614: 8, 1617: 8, 1632: 8, 1650: 8, 1657: 8, 1658: 8, 1677: 8, 1697: 8, 1759: 8, 1786: 5, 1787: 5, 1788: 8
          }],
}

DBC = {
  CAR.OUTBACK: dbc_dict('subaru_outback_2015_eyesight', 'subaru_outback_2015_eyesight_object'),
  CAR.XV2018: dbc_dict('subaru_xv_2018_eyesight', 'subaru_xv_2018_eyesight_object'),
}