from abc import ABC, abstractmethod
from typing import Optional, Tuple

class Roboclaw(ABC):
    """Represents a single Roboclaw, which controls a left and a right motor."""
    
    def set_enc_left_enabled(self, enabled: bool):
        """Enable or disable encoder handling for the left motor.

        Parameters
        ----------
        enabled : bool
            Whether encoders should be handled or not.
        """
        pass

    def set_enc_right_enabled(self, enabled: bool):
        """Enable or disable encoder handling for the right motor.

        Parameters
        ----------
        enabled : bool
            Whether encoders should be handled or not.
        """
        pass

    def set_enc_left_max_speed(self, max_enc_speed: int):
        """Sets the expected maximum speed, in encoder counts per second, of the left motor.

        Parameters
        ----------
        max_enc_speed : int
            The expected maximum speed in encoder counts per second.
        """
        pass

    def set_enc_right_max_speed(self, max_enc_speed: int):
        """Sets the expected maximum speed, in encoder counts per second, of the right motor.

        Parameters
        ----------
        max_enc_speed : int
            The expected maximum speed in encoder counts per second.
        """
        pass

    @abstractmethod
    def write_speed(self, spd_l: Optional[int] = None, spd_r: Optional[int] = None):
        """Updates the current velocities of the motors.

        Parameters
        ----------
        spd_l : Optional[int], optional
            The new velocity for the left motor, or None if it should not be updated. By default, None.
        spd_r : Optional[int], optional
            The new velocity for the right motor, or None if it should not be updated. By default, None.
        """
        raise NotImplementedError('Abstract method!')

    @abstractmethod
    def read_encs(self) -> Tuple[Optional[int], Optional[int]]:
        """Queries the current encoder counts.

        Returned data may not be meaningful if encoder handling has not been explicitly enabled.

        Returns
        -------
        Tuple[Optional[int], Optional[int]]
            The encoder counts, producing None if the counts are not known or could be queried.

        See Also
        --------
        set_enc_left_enabled : Enable or disable encoder handling for the left motor.
        set_enc_right_enabled : Enable or disable encoder handling for the right motor.
        """
        raise NotImplementedError('Abstract method!')

    @abstractmethod
    def read_currents(self) -> Tuple[Optional[float], Optional[float]]:
        """Queries the present currents (in Amps, resolution to the nearest 10mA).

        May return None if the current has not been polled.

        Returns
        -------
        Tuple[Optional[float], Optional[float]]
            The current in the left and right motors for the RoboClaw
        """
        raise NotImplementedError('Abstract method!')

    @abstractmethod
    def set_current_limits(self, left_limit: Optional[bool], right_limit: Optional[bool]) -> None:
        """Sets software current limits for each channel of a Roboclaw.  Either parameter may be None if no current is specified.

        Parameters
        ----------
        left_limit : (Optional[bool])
            The current limit (in Amps) for the left channel
        right_limit : (Optional[bool])
            The current limit (in Amps) for the right channel
        """
        raise NotImplementedError('Abstract method!')

    @abstractmethod
    def get_over_current_status(self) -> Tuple[Optional[bool], Optional[bool]]:
        """Gets whether each channel is over its current limit.

        If the current limit for a channel is not set, then the corresponding status is None

        Returns
        -------
        Tuple[Optional[bool], Optional[bool]]
            The statuses of each channel being over its current limit
        """
        raise NotImplementedError('Abstract method!')

    @abstractmethod
    def set_counts_per_rotation(self, counts_per_rotation_l : int = None, counts_per_rotation_r : int = None) -> None:
        """Sets the counts per rotation for a given encoder

        Parameters
        ----------
        counts_per_rotation_l : int
            Counts per rotation for the left encoder
        counts_per_rotation_r : int
            Counts per rotation for the right encoder
        """
        raise NotImplementedError('Abstract method!')

    @abstractmethod
    def set_offset(self, offset_l : int = None, offset_r : int = None) -> None:
        """Sets the offset for a given encoder

        Parameters
        ----------
        offset_l : int
            The offset for the left encoder
        offset_r : int
            The offset for the right encoder
        """
        raise NotImplementedError('Abstract method!')
    def get_watchdog_stop(self) -> bool:
        """Gets whether or note the watchdog stop is engaged

        Returns:
            bool: Whether or not the watchdog stop is engaged
        """
        raise NotImplementedError('AbstractMethod')

class RoboclawChainApi(ABC):
    """Allows for extracting individual Roboclaw instances from a chain."""
    
    @abstractmethod
    def get_roboclaw(self, address: int) -> Roboclaw:
        """Retrieves a single Roboclaw from the chain.

        Parameters
        ----------
        address : int
            The address of the Roboclaw.

        Returns
        -------
        Roboclaw
            The addressed Roboclaw instance.
        """
        raise NotImplementedError('Abstract method!')

class RoboclawChain(ABC):
    """Represents a chain of Roboclaws on a single UART line."""
    
    @abstractmethod
    def __enter__(self) -> RoboclawChainApi:
        raise NotImplementedError('Abstract method!')

    def __exit__(self, e_type, value, traceback):
        pass
