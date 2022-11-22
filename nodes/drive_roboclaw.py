#!/usr/bin/env python3

from re import S
from typing import Any, Dict, cast

import rospy
from std_msgs.msg import Int16, UInt32, Float32, Bool

from wroboclaw.msg import Int16Pair
from wroboclaw.roboclaw import init_roboclaw
from wroboclaw.roboclaw.model import Roboclaw, RoboclawChainApi
from wroboclaw.util.util import UINT32_BOUNDS

class ClawDef:
    """A single Roboclaw definition."""
    
    def __init__(self, name: str, dto: Dict[str, Any]):
        """Parses a Roboclaw definition from a config dictionary.

        Parameters
        ----------
        name : str
            The name for the Roboclaw instance.
        dto : Dict[str, Any]
            A dictionary of parameters for the Roboclaw.
            See "Other Parameters" below for more information.
        
        Other Parameters
        ----------------
        topic : str, optional
            The namespace under which ROS topics for this Roboclaw are defined.
            By default, uses the private namespace for the node.
        address : int
            The address for this Roboclaw.
        enc_left.enabled : bool, optional
            Whether the left motor should have encoder handling enabled or not. By default, False.
        enc_left.max_speed : int, optional
            The expected maximum speed, in encoder counts per second, for the left motor. By default, 1.
            This should probably be changed if the left encoder is enabled.
        enc_right.enabled : bool, optional
            Whether the right motor should have encoder handling enabled or not. By default, False.
        enc_right.max_speed : int, optional
            The expected maximum speed, in encoder counts per second, for the right motor. By default, 1.
            This should probably be changed if the right encoder is enabled.
        """
        self.name = name
        self.topic = dto.get('topic', f'~{name}')
        self.address: int = dto['address']

        enc_l = dto.get('enc_left', None)
        enc_r = dto.get('enc_right', None)

        self.enc_l_enabled, self.enc_l_max_speed = (enc_l.get('enabled', False), enc_l.get('max_speed', 1)) if enc_l else (False, 1)
        self.enc_r_enabled, self.enc_r_max_speed = (enc_r.get('enabled', False), enc_r.get('max_speed', 1)) if enc_r else (False, 1)

        self.curr_lim_l = dto.get('current_limit_left', None)
        self.curr_lim_r = dto.get('current_limit_right', None)

        self.counts_per_rotation_l, self.offset_l = (enc_l.get('counts_per_rotation', None), enc_l.get('offset', None)) if enc_l else (UINT32_BOUNDS[1], 0)
        self.counts_per_rotation_r, self.offset_r = (enc_r.get('counts_per_rotation', None), enc_r.get('offset', None)) if enc_r else (UINT32_BOUNDS[1], 0)

    def init_claw(self, claw_chain: RoboclawChainApi) -> Roboclaw:
        """Initializes a Roboclaw instance as defined by this definition.

        Parameters
        ----------
        claw_chain : RoboclawChainApi
            The Roboclaw chain from which the Roboclaw instance should be extracted.

        Returns
        -------
        Roboclaw
            The newly-initialized Roboclaw instance.
        """
        #Set the address of the Roboclaw
        claw = claw_chain.get_roboclaw(self.address)

        #Set if either encoder is enabled
        claw.set_enc_left_enabled(self.enc_l_enabled)
        claw.set_enc_right_enabled(self.enc_r_enabled)

        #Set the max speeds of the encoders
        claw.set_enc_left_max_speed(self.enc_l_max_speed)
        claw.set_enc_right_max_speed(self.enc_r_max_speed)

        #Set the current limit of the motors
        claw.set_current_limits(self.curr_lim_l, self.curr_lim_r)

        #Set counts per rotation for the encoders
        claw.set_counts_per_rotation(counts_per_rotation_l = self.counts_per_rotation_l, counts_per_rotation_r = self.counts_per_rotation_r)

        #Set offsets for the encoders
        claw.set_offset(offset_l = self.offset_l, offset_r = self.offset_r)

        return claw

class ClawInst:
    """Represents a single Roboclaw."""
    
    def __init__(self, claw_def: ClawDef, claw: Roboclaw):
        """Constructs a Roboclaw wrapper for the given Roboclaw, creating ROS publishers and subscribers.

        Parameters
        ----------
        claw_def : ClawDef
            The Roboclaw definition for this Roboclaw.
        claw : Roboclaw
            The Roboclaw instance.
        """
        self.claw_def = claw_def
        self.claw = claw

        self.spd_sub_l = rospy.Subscriber(f'{self.claw_def.topic}/cmd/left', Int16, lambda m: self.claw.write_speed(spd_l=m.data))
        self.spd_sub_r = rospy.Subscriber(f'{self.claw_def.topic}/cmd/right', Int16, lambda m: self.claw.write_speed(spd_r=m.data))
        self.spd_sub = rospy.Subscriber(f'{self.claw_def.topic}/cmd', Int16Pair, lambda m: self.claw.write_speed(m.left, m.right))

        self.enc_pub_l = rospy.Publisher(f'{self.claw_def.topic}/enc/left', UInt32, queue_size=10)
        self.enc_pub_r = rospy.Publisher(f'{self.claw_def.topic}/enc/right', UInt32, queue_size=10)

        self.curr_pub_l = rospy.Publisher(f'{self.claw_def.topic}/curr/left', Float32, queue_size=10)
        self.curr_pub_r = rospy.Publisher(f'{self.claw_def.topic}/curr/right', Float32, queue_size=10)

        self.over_curr_pub_l = rospy.Publisher(f'{self.claw_def.topic}/curr/over_lim/left', Bool, queue_size=10)
        self.over_curr_pub_r = rospy.Publisher(f'{self.claw_def.topic}/curr/over_lim/right', Bool, queue_size=10)

    def tick(self):
        """Ticks publications for this Roboclaw instance."""
        enc_left, enc_right = self.claw.read_encs()
        if enc_left is not None:
            self.enc_pub_l.publish(UInt32(enc_left))
        if enc_right is not None:
            self.enc_pub_r.publish(UInt32(enc_right))

        curr_left, curr_right = self.claw.read_currents()
        if curr_left is not None:
            self.curr_pub_l.publish(Float32(curr_left))
            self.curr_pub_r.publish(Float32(curr_right))

        over_curr_lim_l, over_curr_lim_r = self.claw.get_over_current_status()
        if over_curr_lim_l is not None:
            self.over_curr_pub_l.publish(Bool(over_curr_lim_l))
        if over_curr_lim_r is not None:
            self.over_curr_pub_r.publish(Bool(over_curr_lim_r))

def main():
    """A driver node for Roboclaws.

    Each instance of this node corresponds to a single chain of
    Roboclaws on a single UART serial port. Various ROS params
    are used to configure this node, which are listed below.

    Other Parameters
    ----------------
    com_port : str
        The UART serial port to which the Roboclaw chain is
        connected.
    baud : int, optional
        The baud rate for the serial port. Defaults to 115200.
    timeout : float, optional
        The timeout time, in seconds, for the serial port.
        Defaults to 0.01 seconds, which is the timeout for
        Roboclaw packet-serial instructions[1]_.
    mock: bool, optional
        Whether the Roboclaw should be run in mock mode or
        not. Defaults to False.
    claws: Dict[str, ClawDef]
        A table of specifications for individual Roboclaws.
        Each entry should consist of a name identifying the
        Roboclaw mapped to a Roboclaw configuration object.

    References
    ----------
    .. [1] https://downloads.basicmicro.com/docs/roboclaw_user_manual.pdf

    See Also
    --------
    ClawDef : A specification for a single Roboclaw.
    """
    rospy.init_node('drive_roboclaw')

    # collect ROS params
    com_port = cast(str, rospy.get_param('~com_port'))
    baud = rospy.get_param('~baud', 115200)
    timeout = rospy.get_param('~timeout', 0.01)
    mock = rospy.get_param('~mock', False)
    claw_defs_dto = cast(Dict[str, Dict[str, Any]], rospy.get_param('~claws'))

    # parse out roboclaw definitions
    claw_defs = [ClawDef(name, dto) for name, dto in claw_defs_dto.items()]

    # construct roboclaws
    with init_roboclaw(com_port, baud, timeout, mock) as claw_chain:
        claws = [ClawInst(claw_def, claw_def.init_claw(claw_chain)) for claw_def in claw_defs]

        # main ROS loop
        sleeper = rospy.Rate(30)
        while not rospy.is_shutdown():
            for claw in claws:
                claw.tick()
            sleeper.sleep()

if __name__ == '__main__':
    main()
