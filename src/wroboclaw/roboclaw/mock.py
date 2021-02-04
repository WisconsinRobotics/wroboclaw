from collections import defaultdict
from typing import DefaultDict, Optional, Tuple

from ..util.mock import MockVelCtrl
from .model import Roboclaw, RoboclawChain, RoboclawChainApi        

class RoboclawMock(Roboclaw):
    def __init__(self):
        self._left = MockVelCtrl()
        self._right = MockVelCtrl()

    def write_speed(self, spd_l: Optional[int] = None, spd_r: Optional[int] = None):
        if spd_l is not None:
            self._left.set_velocity(spd_l) # TODO: probably needs some tuning factor here
        if spd_r is not None:
            self._right.set_velocity(spd_r)

    def read_encs(self) -> Tuple[Optional[int], Optional[int]]:
        return round(self._left.get_position()), round(self._right.get_position())

class RoboclawChainMock(RoboclawChain, RoboclawChainApi):
    def __init__(self):
        self._claws: DefaultDict[int, RoboclawMock] = defaultdict(RoboclawMock)
    
    def __enter__(self) -> RoboclawChainApi:
        return self
    
    def __exit__(self):
        for claw in self._claws.values():
            claw.write_speed(0, 0)

    def get_roboclaw(self, address: int) -> Roboclaw:
        return self._claws[address]
