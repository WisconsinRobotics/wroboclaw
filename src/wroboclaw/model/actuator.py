from abc import abstractmethod
from typing import Optional

from .device import Device

class VelocityControllable1D(Device):
    """Represents a device that supports velocity control with one degree of freedom."""

    @abstractmethod
    def set_velocity_target(self, vel: float):
        """Sets the target velocity for this device.

        The exact interpretation of the speed value is not defined here and is left to the implementation. However,
        negative numbers should in general correspond to "reverse" and positive numbers should correspond to "forwards",
        assuming that these are meaningful concepts in the relevant system. Moreover, the values -1 and 1 should
        correspond to full speed in the respective directions and the value 0 should correspond to a full stop.

        Parameters
        ----------
        vel : float
            The target velocity, represented as a real number on the interval [-1, 1].
        """
        raise NotImplementedError()

    def get_velocity_target(self) -> Optional[float]:
        """Retrieves the current target velocity for this device.

        The target velocity is the velocity that the device is attempting to drive at. This is distinct from the actual
        velocity, which is the true velocity that the device is currently driving at.

        Returns
        -------
        Optional[float]
            The current target velocity, represented as a real number on the interval [-1, 1]. If the system does not
            support retriving a target velocity, then `None`.

        See Also
        --------
        get_velocity : Retrieves actual velocity.
        """
        return None

    def get_velocity(self) -> Optional[float]:
        """Retrieves the current actual velocity for this device.

        The actual velocity is the velocity that the device is actually driving at. This is distinct from the target
        velocity, which is the velocity that the device would *like to* drive at.

        Returns
        -------
        Optional[float]
            The current target velocity, represented as a real number on the interval [-1, 1]. If the system does not
            support retriving a target velocity, then `None`.

        See Also
        --------
        get_velocity_target : Retrieves target velocity.
        """
        return None

class PositionControllable1D(Device): # TODO
    """Represents a device that supports position control with one degree of freedom."""
