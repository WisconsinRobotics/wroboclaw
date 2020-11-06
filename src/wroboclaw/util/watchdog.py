from abc import ABC, abstractmethod

import rospy

class Watchdog(ABC):
    """Represents a timeout-based watchdog."""

    @abstractmethod
    def feed(self):
        """Feeds the watchdog."""
        raise NotImplementedError()

    @abstractmethod
    def check(self) -> bool:
        """Checks the watchdog's state.

        Returns
        -------
        bool
            Whether the watchdog is still happy or not. If `False` is returned, then the watchdog has timed out.
        """        
        raise NotImplementedError()

class SimpleWatchdog(Watchdog):
    """A simple timeout-based watchdog implementation."""

    def __init__(self, timeout: float):
        """Creates a new simple timeout-based watchdog.

        Parameters
        ----------
        timeout : float
            The timeout period, in seconds.
        """        
        self.timeout = timeout
        self._last_update = rospy.get_time()

    def feed(self):
        self._last_update = rospy.get_time()

    def check(self) -> bool:
        return rospy.get_time() - self._last_update < self.timeout

class NoopWatchdog(Watchdog):
    """A no-op watchdog that never times out."""

    def feed(self):
        pass

    def check(self) -> bool:
        return True
