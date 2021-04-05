from typing import Optional, Tuple

import rospy

from .util import BoundaryBehaviour, boundary_clamp

class MockVelCtrl():
    """A mock implementation of a single velocity-controlled motor."""

    def __init__(self, pos_bounds: Optional[Tuple[float, float]] = None, pos_clamp: BoundaryBehaviour = BoundaryBehaviour.clamp, max_enc_speed: int = 1):    
        self.pos_bounds = pos_bounds
        self.pos_clamp = pos_clamp
        self._current_pos = 0.0
        self._current_vel = 0.0
        self._max_enc_speed = max_enc_speed
        self._last_update_time = rospy.get_time()

    def _update_pos(self):
        now = rospy.get_time()
        self._current_pos += int(self._current_vel / ((1<<15) - 1) * (now - self._last_update_time) * self._max_enc_speed)
        if self.pos_bounds is not None:
            self._current_pos = boundary_clamp(self.pos_clamp, self._current_pos, *self.pos_bounds)
        self._last_update_time = now

    def set_max_speed(self, max_speed: int):
        self._update_pos()
        self._max_enc_speed = max_speed
        print(self._max_enc_speed)

    def set_velocity(self, vel: float):
        self._update_pos()
        self._current_vel = vel

    def get_velocity(self) -> Optional[float]:
        return self._current_vel

    def get_position(self) -> float:
        self._update_pos()
        return self._current_pos
