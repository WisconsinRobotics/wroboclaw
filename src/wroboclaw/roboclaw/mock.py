from collections import defaultdict
from typing import DefaultDict, Optional, Tuple

from ..util.mock import MockVelCtrl
from ..util.util import BoundaryBehaviour
from .model import Roboclaw, RoboclawChain, RoboclawChainApi        

UINT32_BOUNDS = (0, (1 << 32) - 1)
INT16_MAX = (1 << 15) - 1

class RoboclawMock(Roboclaw):
    """A mock Roboclaw that uses simulated motors to produce mock data."""
    
    def __init__(self):
        self._left = MockVelCtrl(UINT32_BOUNDS, BoundaryBehaviour.wrap)
        self._left_max_speed = 1
        self._right = MockVelCtrl(UINT32_BOUNDS, BoundaryBehaviour.wrap)
        self._right_max_speed = 1

    def set_enc_left_max_speed(self, max_speed: int):
        self._left_max_speed = max_speed

    def set_enc_right_max_speed(self, max_speed: int):
        self._right_max_speed = max_speed

    def write_speed(self, spd_l: Optional[int] = None, spd_r: Optional[int] = None):
        if spd_l is not None:
            self._left.set_velocity(spd_l / INT16_MAX * self._left_max_speed)
        if spd_r is not None:
            self._right.set_velocity(spd_r / INT16_MAX * self._right_max_speed)

    def read_encs(self) -> Tuple[Optional[int], Optional[int]]:
        return round(self._left.get_position()), round(self._right.get_position())

    def read_currents(self) -> Tuple[Optional[float], Optional[float]]:
        return 0,0 # a controller that does not exist draws no current

class RoboclawChainMock(RoboclawChain, RoboclawChainApi):
    """A mock Roboclaw chain that provides simulated Roboclaws."""
    
    def __init__(self):
        self._claws: DefaultDict[int, RoboclawMock] = defaultdict(RoboclawMock)
    
    def __enter__(self) -> RoboclawChainApi:
        return self
    
    def __exit__(self, e_type, value, traceback):
        for claw in self._claws.values():
            claw.write_speed(0, 0)

    def get_roboclaw(self, address: int) -> Roboclaw:
        return self._claws[address]
