import rospy
from serial import Serial
from struct import Struct
from threading import Lock, Thread
from typing import Any, Dict, List, Optional, Tuple

from ..util.checksum import crc16
from ..util.watchdog import SimpleWatchdog
from .model import Roboclaw, RoboclawChain, RoboclawChainApi

def param_struct(struct_def: str) -> Struct:
    return Struct(f'>{struct_def}') # checksum is sent in separate write

def res_struct(struct_def: str) -> Struct:
    return Struct(f'>{struct_def}H') # parse out 16-bit checksum

STRUCT_HEADER = param_struct('BB')
STRUCT_CRC16 = param_struct('H')

STRUCT_INDIV_DUTY = param_struct('h')
STRUCT_MIXED_DUTY = param_struct('hh')
STRUCT_INDIV_ENC_CNT = res_struct('I')
STRUCT_MIXED_ENC_CNT = res_struct('II')

class SerialCommandHandler:
    """Handles Roboclaw serial packet commands (T -> ()).
    
    See Also
    --------
    SerialRequestHandler : Handles requests (() -> T).
    """
    
    def __init__(self, serial: Serial, address: int, opcode: int, param_struct: Struct):
        """Constructs a new command handler.

        Parameters
        ----------
        serial : Serial
            The serial port to the Roboclaw.
        address : int
            The Roboclaw's address.
        opcode : int
            The opcode for the command.
        param_struct : Struct
            A struct describing the format of the request parameters.
        """
        self._serial = serial
        rospy.loginfo(f"Serial processed:  {serial}")
        self._header = STRUCT_HEADER.pack(address, opcode)
        self._header_csum = crc16(self._header)
        self._param_struct = param_struct

    def invoke(self, *args: Any) -> bool:
        """Executes the command.

        Returns
        -------
        args : Any
            The parameters to the command, which are serialized using the param struct.
        bool
            Whether the request was successfully sent and acknowledged or not.
        """
        data = self._param_struct.pack(*args)
        csum = crc16(data, initial=self._header_csum)
        rospy.loginfo(f"Write Status (Header):  {self._serial.write(self._header)}")
        rospy.loginfo(f"Write Status (Data):  {self._serial.write(data)}")
        rospy.loginfo(f"Write Status (CRC):  {self._serial.write(STRUCT_CRC16.pack(csum & 0xFFFF))}")
        rospy.loginfo(f"CRC Value:  {STRUCT_CRC16.pack(csum & 0xFFFF)}")
        res = self._serial.read(1)
        rospy.loginfo(f"Read result:  {res}")
        return len(res) > 0 and res[0] == 0xFF

class SerialRequestHandler:
    """Handles Roboclaw serial packet requests (() -> T).
    
    See Also
    --------
    SerialCommandHandler : Handles commands (T -> ()).
    """
    
    def __init__(self, serial: Serial, address: int, opcode: int, res_struct: Struct):
        """Constructs a new request handler.

        Parameters
        ----------
        serial : Serial
            The serial port to the Roboclaw.
        address : int
            The Roboclaw's address.
        opcode : int
            The opcode for the request.
        res_struct : Struct
            A struct describing the format of the response.
        """
        self._serial = serial
        rospy.loginfo(f"Serial processed:  {serial}")
        self._header = STRUCT_HEADER.pack(address, opcode)
        self._header_csum = crc16(self._header)
        self._res_struct = res_struct

    def invoke(self) -> Optional[Tuple]:
        """Executes the request.

        Returns
        -------
        Optional[Tuple]
            The results, or None if the request fails.
        """
        rospy.loginfo(f"Write status (Header, SerialRequest):  {self._serial.write(self._header)}")
        data = self._serial.read(self._res_struct.size)
        rospy.loginfo(f"Read data (SerialRequest):  {data}")
        if len(data) != self._res_struct.size:
            return None
        csum = crc16(data[:-2], initial=self._header_csum)
        res = self._res_struct.unpack(data)
        return res[:-1] if res[-1] == csum else None

class RoboclawSerialInstance(Roboclaw):
    """Represents a single Roboclaw on a chain."""
    
    def __init__(self, serial: Serial, address: int):
        """Constructs a single Roboclaw instance.

        Parameters
        ----------
        serial : Serial
            The UART serial port through which the Roboclaw can be communicated with.
        address : int
            The address of the Roboclaw.
        """
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
            return self._enc_l, self._enc_r

    def _tick(self) -> bool: # TODO serial invocations ignore errors; maybe handle them
        """Updates this Roboclaw's state, taking control of the UART port for the duration.
        
        This method should never be called by anything except the Roboclaw comms thread!

        Returns
        -------
        bool
            Whether this Roboclaw instance is still alive and usable or not.
        """
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
        """Terminates Roboclaw communications."""
        with self._state_lock:
            self._alive = False

class RoboclawSerialApi(RoboclawChainApi):
    """Handles communications with individual Roboclaws in a chain.
    
    As communications on a serial port must not overlap, synchronization between communications for
    multiple Roboclaw instances is managed by the comms thread maintained by this class. At any time,
    at most a single Roboclaw should be able to read/write to the UART port.
    """
    
    def __init__(self, serial: Serial):
        """Constructs a new serial Roboclaw chain API instance.

        Parameters
        ----------
        serial : Serial
            The UART serial port on which the Roboclaw chain is attached.
        """
        self._serial = serial
        self._claws: Dict[int, RoboclawSerialInstance] = dict()
        self._claws_lock = Lock()
        self._alive_claws = 0
        self._alive = True
        self._alive_lock = Lock()
        self._comms_thread = Thread(target=self._comms_loop, name=f'Roboclaw Comms: {serial.portstr}')
        self._comms_thread.start()

    def _comms_loop(self):
        """The UART communications loop maintained in the comms thread."""
        while True:
            with self._claws_lock:
                if self._alive_claws <= 0:
                    with self._alive_lock:
                        if not self._alive:
                            self._serial.close()
                            break
                dead_claws: List[int] = []
                for claw_addr, claw in self._claws.items():
                    if not claw._tick():
                        dead_claws.append(claw_addr)
                        self._alive_claws -= 1
                for claw_addr in dead_claws:
                    del self._claws[claw_addr]

    def _close(self):
        """Kills all Roboclaw instances and termiantes communication with the Roboclaw chain."""
        with self._claws_lock:
            for claw in self._claws.values():
                claw._kill()
        with self._alive_lock:
            self._alive = False
        self._comms_thread.join()

    def get_roboclaw(self, address: int) -> Roboclaw:
        with self._claws_lock:
            claw = self._claws.get(address)
            if claw is None:
                claw = RoboclawSerialInstance(self._serial, address)
                self._claws[address] = claw
                self._alive_claws += 1
        return claw

class RoboclawChainSerial(RoboclawChain):
    """A Roboclaw chain on a UART serial port."""
    
    def __init__(self, com_port: str, baud: int, timeout: float):
        """Constructs a new Roboclaw chain with the given serial port parameters.

        Parameters
        ----------
        com_port : str
            The path to the communications port over which UART comms can be established.
        baud : int
            The baud rate for the UART comms.
        timeout : float
            The serial port timeout, in seconds.
        """
        self.com_port = com_port
        self.baud = baud
        self.timeout = timeout
        self._instance: Optional[RoboclawSerialApi] = None

    def __enter__(self) -> RoboclawChainApi:
        self._instance = RoboclawSerialApi(Serial(self.com_port, self.baud, timeout=self.timeout))
        rospy.loginfo(f"Serial established {self._instance._serial}")
        return self._instance

    def __exit__(self, e_type, value, traceback):
        self._instance._close()
        self._instance = None
