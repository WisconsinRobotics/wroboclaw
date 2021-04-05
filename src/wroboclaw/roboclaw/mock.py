from collections import defaultdict
from typing import DefaultDict, Optional, Tuple

from ..util.mock import MockVelCtrl
from ..util.util import BoundaryBehaviour
from .model import Roboclaw, RoboclawChain, RoboclawChainApi        

UINT32_BOUNDS = (0, (1 << 32) - 1)

class RoboclawMock(Roboclaw):
    def __init__(self):
        self._left = MockVelCtrl(UINT32_BOUNDS, BoundaryBehaviour.wrap)
        self._right = MockVelCtrl(UINT32_BOUNDS, BoundaryBehaviour.wrap)

    def set_enc_left_max_speed(self, max_enc_speed: int):
        self._left.set_max_speed(max_enc_speed)

    def set_enc_right_max_speed(self, max_enc_speed: int):
        self._right.set_max_speed(max_enc_speed)

    def write_speed(self, spd_l: Optional[int] = None, spd_r: Optional[int] = None):
        if spd_l is not None:
            self._left.set_velocity(spd_l) # TODO: probably needs some tuning factor here; possibly corrected in fix for issue #1
        if spd_r is not None:
            self._right.set_velocity(spd_r)

    def read_encs(self) -> Tuple[Optional[int], Optional[int]]:
        return round(self._left.get_position()), round(self._right.get_position())

class RoboclawChainMock(RoboclawChain, RoboclawChainApi):
    def __init__(self):
        self._claws: DefaultDict[int, RoboclawMock] = defaultdict(RoboclawMock)
    
    def __enter__(self) -> RoboclawChainApi:
        return self
    
    def __exit__(self, e_type, value, traceback):
        for claw in self._claws.values():
            claw.write_speed(0, 0)

    def get_roboclaw(self, address: int) -> Roboclaw:
        return self._claws[address]
