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
