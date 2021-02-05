from abc import ABC, abstractmethod
from typing import Optional, Tuple

class Roboclaw(ABC):
    def set_enc_left_enabled(self, enabled: bool):
        pass

    def set_enc_right_enabled(self, enabled: bool):
        pass

    @abstractmethod
    def write_speed(self, spd_l: Optional[int] = None, spd_r: Optional[int] = None):
        raise NotImplementedError('Abstract method!')

    @abstractmethod
    def read_encs(self) -> Tuple[Optional[int], Optional[int]]:
        raise NotImplementedError('Abstract method!')

class RoboclawChainApi(ABC):
    @abstractmethod
    def get_roboclaw(self, address: int) -> Roboclaw:
        raise NotImplementedError('Abstract method!')

class RoboclawChain(ABC):
    @abstractmethod
    def __enter__(self) -> RoboclawChainApi:
        raise NotImplementedError('Abstract method!')

    def __exit__(self):
        pass
