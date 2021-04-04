from .mock import RoboclawChainMock
from .model import RoboclawChain
from .serial_interface import RoboclawChainSerial

def init(com_port: str, baud: int, timeout: float = 0.01, mock: bool = False, time_warp: int = 1) -> RoboclawChain:
    return RoboclawChainMock(time_warp) if mock else RoboclawChainSerial(com_port, baud, timeout)
