from abc import abstractmethod

from .device import Device

class PositionQueryable1D(Device):
    """Represents a device that supports querying for position on one degree of freedom."""

    @abstractmethod
    def get_position(self) -> float:
        """Retrieves the current position reported by this device.

        The exact interpretation of the value returned by `get_position` is not defined here and is left to the
        implementation.

        Returns
        -------
        float
            The position value reported by this device.
        """
        raise NotImplementedError()
