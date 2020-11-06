from abc import abstractmethod
from contextlib import AbstractContextManager
from typing import Generic, Optional, TypeVar

from .device import Device

D = TypeVar('D', bound=Device)

class DeviceAlloc(Generic[D]):
    """Provides an interface for creating and retrieving instances of a specific type of low-level device."""
    
    @abstractmethod
    def get_or_alloc_device(self, id: int) -> D:
        """Retrieves a device by ID, or creates a handle to it if none exists.

        The identifier for a device is a unique integer that refers to that specific instance. The identifier itself may
        be meaningful; this is implementation-defined. Otherwise, it may be merely an arbitrary identifier managed by
        the device manager. An example of a meaningful device ID might be a Roboclaw motor controller's packet-serial
        address, which is used to identify a specific device on a UART chain.

        Parameters
        ----------
        id : int
            The unique integer identifier referring to the device.

        Returns
        -------
        D
            The device instance corresponding to the given ID.

        Raises
        ------
        ValueError
            The given ID is not a valid device ID for this device type.

        See Also
        --------
        get_device : Retrieves a device, but does not create a new one if none exists.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_device(self, id: int) -> Optional[D]:
        
        """Retrieves a device by ID, if it exists.

        The counterpart to `get_or_alloc_device` that doesn't create a new device handle if the given ID does not
        already have an associated device instance. See the documentation for that method for more details.

        Parameters
        ----------
        id : int
            The unique integer identifier referring to the device.

        Returns
        -------
        Optional[D]
            The device instance corresponding to the given ID, or `None` if no such device instance yet exists.

        Raises
        ------
        ValueError
            The given ID is not a valid device ID for this device type.

        See Also
        --------
        get_or_alloc_device : Retrieves a device instance, or creates it if it does not yet exist.
        """
        raise NotImplementedError()

class DeviceManager(Generic[D], AbstractContextManager):
    """Manages device instances for a specific type of low-level device.
    
    A device manager object itself is opaque. In order to access it, one should use it as a context manager for a `with`
    block. This produces an instance of `DeviceAlloc`, which can be used to create and retrieve device instances.
    Implementors need not implement `__exit__` if they do not require any particular clean-up funcionality.

    Notes
    -----
    The device manager's design as a `with` context manager allows for the automatic cleanup of device instances once
    the device manager is no longer needed. This means programmers do not need to remember to "close" the device manager
    after they are done using it; resources are freed by construction, as there is no way to obtain and interact with
    device instances without entering a `with` context associated with this device manager.
    """

    @abstractmethod
    def __enter__(self) -> DeviceAlloc[D]:
        """Retrieves a device allocator associatied with this device manager.
        
        This method should not be called directly! Instead, programmers should use a `DeviceManager` instance in a
        `with` block, from which this method is implicitly called. See the documentation for `DeviceManager` for more
        details.

        Returns
        -------
        DeviceAlloc[D]
            A device allocator instance associated with this device manager.

        Raises
        ------
        RuntimeError
            An unclosed device allocator instance already exists.
        """
        raise NotImplementedError()
