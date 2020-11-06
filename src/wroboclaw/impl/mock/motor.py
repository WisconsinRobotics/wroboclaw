from typing import Callable, Tuple

import rospy

from ...model.actuator import *
from ...model.sensor import *
from ...util.util import BoundaryBehaviour, boundary_clamp

# motors

class MockVelCtrlMotor(VelocityControllable1D, PositionQueryable1D):
    """A mock implementation of a single velocity-controlled motor.""" # TODO documentation

    def __init__(self, id: int, speed_modifier: Callable[[float], float] = lambda v: 30.0 * v,
                 pos_bounds: Optional[Tuple[float, float]] = None, pos_clamp: BoundaryBehaviour = BoundaryBehaviour.clamp):
        self.id = id
        self.speed_modifier = speed_modifier
        self.pos_bounds = pos_bounds
        self.pos_clamp = pos_clamp
        self._current_pos = 0.0
        self._current_vel = 0.0
        self._last_update_time = rospy.get_time()

    def get_id(self) -> int:
        return self.id

    def _update_pos(self):
        now = rospy.get_time()
        self._current_pos += self.speed_modifier(self._current_vel) * (now - self._last_update_time)
        if self.pos_bounds is not None:
            self._current_pos = boundary_clamp(self.pos_clamp, self._current_pos, *self.pos_bounds)
        self._last_update_time = now

    def set_velocity_target(self, vel: float):
        self._update_pos()
        self._current_vel = vel

    def get_velocity_target(self) -> Optional[float]:
        return self._current_vel

    def get_velocity(self) -> Optional[float]:
        return self.get_velocity_target()

    def get_position(self) -> float:
        self._update_pos()
        return self._current_pos
