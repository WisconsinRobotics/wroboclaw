from serial import Serial
from struct import Struct
from threading import Lock, Thread
from typing import Any, Dict, Optional, Tuple

from ..util.checksum import crc16
from ..util.watchdog import SimpleWatchdog
from .model import Roboclaw, RoboclawChain, RoboclawChainApi

def param_struct(struct_def: str) -> Struct:
    return Struct(f'>{struct_def}')

def res_struct(struct_def: str) -> Struct:
    return Struct(f'>{struct_def}H')

STRUCT_HEADER = param_struct('BB')
STRUCT_CRC16 = param_struct('H')

STRUCT_INDIV_DUTY = param_struct('h')
STRUCT_MIXED_DUTY = param_struct('hh')
STRUCT_INDIV_ENC_CNT = res_struct('I')
STRUCT_MIXED_ENC_CNT = res_struct('II')

# handles a command over the serial line, i.e. T -> ()
class SerialCommandHandler:
    def __init__(self, serial: Serial, address: int, opcode: int, param_struct: Struct):
        self._serial = serial
        self._header = STRUCT_HEADER.pack(address, opcode)
        self._header_csum = crc16(self._header)
        self._param_struct = param_struct

    def invoke(self, *args: Any) -> bool:
        data = self._param_struct.pack(*args)
        csum = crc16(data, initial=self._header_csum)
        self._serial.write(self._header)
        self._serial.write(data)
        self._serial.write(STRUCT_CRC16.pack(csum))
        res = self._serial.read(1)
        return len(res) > 0 and res[0] == 0xFF

# handles a request over the serial line, i.e. () -> T
class SerialRequestHandler:
    def __init__(self, serial: Serial, address: int, opcode: int, res_struct: Struct):
        self._serial = serial
        self._header = STRUCT_HEADER.pack(address, opcode)
        self._header_csum = crc16(self._header)
        self._res_struct = res_struct

    def invoke(self) -> Optional[Tuple]:
        self._serial.write(self._header)
        data = self._serial.read(self._res_struct.size)
        if len(data) != self._res_struct.size:
            return None
        csum = crc16(data[:-2], initial=self._header_csum)
        res = self._res_struct.unpack(data)
        return res[:-1] if res[-1] == csum else None

class RoboclawSerialInstance(Roboclaw):
    def __init__(self, serial: Serial, address: int):
        self._sent_spd_l: Optional[int] = None
        self._sent_spd_r: Optional[int] = None
        self._target_spd_l = 0
        self._target_spd_r = 0
        self._watchdog = SimpleWatchdog(1) # TODO: configurable watchdog

        self._enc_l_enabled: bool = False
        self._enc_l: Optional[int] = None
        self._enc_r_enabled: bool = False
        self._enc_r: Optional[int] = None

        self._cmd_m1_duty = SerialCommandHandler(serial, address, 32, STRUCT_INDIV_DUTY)
        self._cmd_m2_duty = SerialCommandHandler(serial, address, 33, STRUCT_INDIV_DUTY)
        self._cmd_mixed_duty = SerialCommandHandler(serial, address, 34, STRUCT_MIXED_DUTY)
        self._req_get_m1_enc = SerialRequestHandler(serial, address, 16, STRUCT_INDIV_ENC_CNT)
        self._req_get_m2_enc = SerialRequestHandler(serial, address, 17, STRUCT_INDIV_ENC_CNT)
        self._req_get_mixed_enc = SerialRequestHandler(serial, address, 78, STRUCT_MIXED_ENC_CNT)

        self._alive = True
        self._state_lock = Lock()

    def set_enc_left_enabled(self, enabled: bool):
        with self._state_lock:
            if enabled:
                self._enc_l_enabled = True
            else:
                self._enc_l_enabled = False
                self._enc_l = None

    def set_enc_right_enabled(self, enabled: bool):
        with self._state_lock:
            if enabled:
                self._enc_r_enabled = True
            else:
                self._enc_r_enabled = False
                self._enc_r = None

    def write_speed(self, spd_l: Optional[int], spd_r: Optional[int]):
        with self._state_lock:
            if spd_l is not None:
                self._target_spd_l = spd_l
            if spd_r is not None:
                self._target_spd_r = spd_r
            self._watchdog.feed()
    
    def read_encs(self) -> Tuple[Optional[int], Optional[int]]:
        with self._state_lock:
            if self._enc_l is None or self._enc_r is None:
                raise ValueError('No encoder data has been received!')
            return self._enc_l, self._enc_r

    def _tick(self) -> bool: # TODO serial invocations ignore errors; maybe handle them
        with self._state_lock:
            if not self._alive:
                self._cmd_mixed_duty.invoke(0, 0)
                return False
            
            # write motors
            if self._watchdog.check():
                if self._sent_spd_l != self._target_spd_l:
                    if self._sent_spd_r != self._target_spd_r:
                        self._cmd_mixed_duty.invoke(self._target_spd_l, self._target_spd_r)
                        self._sent_spd_l = self._target_spd_l
                        self._sent_spd_r = self._target_spd_r
                    else:
                        self._cmd_m1_duty.invoke(self._target_spd_l)
                        self._sent_spd_l = self._target_spd_l
                elif self._sent_spd_r != self._target_spd_r:
                    self._cmd_m2_duty.invoke(self._target_spd_r)
                    self._sent_spd_r = self._target_spd_r
            else:
                self._cmd_mixed_duty.invoke(0, 0)
            
            # read encoders
            if self._enc_l_enabled:
                if self._enc_r_enabled:
                    res = self._req_get_mixed_enc.invoke()
                    if res is not None:
                        self._enc_l, self._enc_r = res
                res = self._req_get_m1_enc.invoke()
                if res is not None:
                    self._enc_l, = res
            elif self._enc_r_enabled:
                res = self._req_get_m2_enc.invoke()
                if res is not None:
                    self._enc_r, = res
            return True

    def _kill(self):
        with self._state_lock:
            self._alive = False

class RoboclawSerialApi(RoboclawChainApi):
    def __init__(self, serial: Serial):
        self._serial = serial
        self._claws: Dict[int, RoboclawSerialInstance] = dict()
        self._alive_claws = 0
        self._alive = True
        self._alive_lock = Lock()
        self._comms_thread = Thread(target=self._comms_loop, name=f'Roboclaw Comms: {serial.portstr}')
        self._comms_thread.start()

    def _comms_loop(self):
        while True:
            if self._alive_claws <= 0:
                with self._alive_lock:
                    if not self._alive:
                        self._serial.close()
                        break
            for claw in self._claws.values():
                if not claw._tick():
                    self._alive_claws -= 1

    def _close(self):
        for claw in self._claws.values():
            claw._kill()
        with self._alive_lock:
            self._alive = False
        self._comms_thread.join()

    def get_roboclaw(self, address: int) -> Roboclaw:
        claw = self._claws.get(address)
        if claw is None:
            claw = RoboclawSerialInstance(self._serial, address)
            self._claws[address] = claw
            self._alive_claws += 1
        return claw

class RoboclawChainSerial(RoboclawChain):
    def __init__(self, com_port: str, baud: int, timeout: float):
        self.com_port = com_port
        self.baud = baud
        self.timeout = timeout
        self._instance: Optional[RoboclawSerialApi] = None

    def __enter__(self) -> RoboclawChainApi:
        self._instance = RoboclawSerialApi(Serial(self.com_port, self.baud, timeout=self.timeout))
        return self._instance

    def __exit__(self, e_type, value, traceback):
        self._instance._close()
        self._instance = None
