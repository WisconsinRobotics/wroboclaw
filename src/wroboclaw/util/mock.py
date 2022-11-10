from typing import Optional, Tuple

import rospy

from .util import BoundaryBehaviour, boundary_clamp

class MockVelCtrl():
    """A mock implementation of a single velocity-controlled motor."""

    def __init__(self, pos_bounds: Optional[Tuple[float, float]] = None, pos_clamp: BoundaryBehaviour = BoundaryBehaviour.clamp):
        """Constructs a new mock velocity-controller motor.

        Parameters
        ----------
        pos_bounds : Optional[Tuple[float, float]], optional
            The bounds for the motor's position, or None if the position should not be bounded. By default, None.
        pos_clamp : BoundaryBehaviour, optional
            The clamping function for the motor's position, if bounded. By default, clamps to the interval.
        """
        self.pos_bounds = pos_bounds
        self.pos_clamp = pos_clamp
        self._current_pos = 0.0
        self._current_vel = 0.0
        self._last_update_time = rospy.get_time()

    def _update_pos(self):
        """Recomputes the motor's position, assuming velocity has remained constant since the last update."""
        now = rospy.get_time()
        self._current_pos += self._current_vel * (now - self._last_update_time)
        if self.pos_bounds is not None:
            self._current_pos = boundary_clamp(self.pos_clamp, self._current_pos, *self.pos_bounds)
        self._last_update_time = now

    def _set_offset(self, offset: int):
        """Sets an offset for the current encoder. Intended to be called before the motor starts
        
        Parameters
        ----------
        offset : int
            The offset to be set for this encoder
        """
        self._current_pos = offset

    def _set_counts_per_rotation(self, counts_per_rotation: int):
        """Sets a value for the counts per rotation for the current encoder. Also intended to be called before the motor starts
        
        Parameters
        ----------
        counts_per_rotation: int
            The counts per rotation for this encoder
        """
        self.pos_bounds = (0, counts_per_rotation)

    def set_velocity(self, vel: float):
        """Changes the velocity of the motor.

        Parameters
        ----------
        vel : float
            The new velocity, in units per second.
        """
        self._update_pos()
        self._current_vel = vel

    def get_velocity(self) -> float:
        """Retrieves the current velocity of the motor.

        Returns
        -------
        float
            The motor's current velocity, in units per second.
        """
        return self._current_vel

    def get_position(self) -> float:
        """Retrieves the current position of the motor.

        Returns
        -------
        float
            The motor's current position.
        """
        self._update_pos()
        return self._current_pos
