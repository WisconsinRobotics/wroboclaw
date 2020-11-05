from abc import ABC, abstractmethod

class Device(ABC):
    """Represents a single instance of a low-level device."""

    @abstractmethod
    def get_id(self) -> int:
        """Produces a unique integer identifier for this device.

        If possible, the returned identifier should correspond directly with some sort of hardware ID related to the
        device. For instance, this might be some sort of unique address for a device controlled via a packet-based
        serial interface. If no such concept is applicable, then this can simply be an arbitrary UUID assigned by the
        device allocator.

        Returns
        -------
        int
            A unique identifier referring to this device.
        """        
        raise NotImplementedError()
