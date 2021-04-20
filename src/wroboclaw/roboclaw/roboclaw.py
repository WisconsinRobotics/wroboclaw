from .mock import RoboclawChainMock
from .model import RoboclawChain
from .serial_interface import RoboclawChainSerial

def init(com_port: str, baud: int, timeout: float = 0.01, mock: bool = False) -> RoboclawChain:
    """Constructs a Roboclaw chain.

    Parameters
    ----------
    com_port : str
        The path to a communications port over which a UART connection to the Roboclaw chain can be established.
    baud : int
        The baud rate of the UART connection to the Roboclaw chain.
    timeout : float, optional
        The timeout on the UART serial port in seconds. By default, 0.01.
    mock : bool, optional
        Whether to use a mock Roboclaw chain or not. By default, a real chain will be constructed.

    Returns
    -------
    RoboclawChain
        The newly-constructed Roboclaw chain instance.
    """
    return RoboclawChainMock() if mock else RoboclawChainSerial(com_port, baud, timeout)
