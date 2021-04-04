#!/usr/bin/env python3

from typing import Any, Dict, cast

import rospy
from std_msgs.msg import Int16, UInt32

from wroboclaw.msg import Int16Pair
from wroboclaw.roboclaw import init_roboclaw
from wroboclaw.roboclaw.model import Roboclaw, RoboclawChainApi

class ClawDef:
    def __init__(self, name: str, dto: Dict[str, Any]):
        self.name = name
        self.topic = dto.get('topic', f'~{name}')
        self.address: int = dto['address']
        self.enc_l_enabled = dto.get('enc_left', False)
        self.enc_r_enabled = dto.get('enc_right', False)

    def init_claw(self, claw_chain: RoboclawChainApi) -> Roboclaw:
        claw = claw_chain.get_roboclaw(self.address)
        claw.set_enc_left_enabled(self.enc_l_enabled)
        claw.set_enc_right_enabled(self.enc_r_enabled)
        return claw

class ClawInst:
    def __init__(self, claw_def: ClawDef, claw: Roboclaw):
        self.claw_def = claw_def
        self.claw = claw

        self.spd_sub_l = rospy.Subscriber(f'{self.claw_def.topic}/cmd/left', Int16, lambda m: self.claw.write_speed(spd_l=m.data))
        self.spd_sub_r = rospy.Subscriber(f'{self.claw_def.topic}/cmd/right', Int16, lambda m: self.claw.write_speed(spd_r=m.data))
        self.spd_sub = rospy.Subscriber(f'{self.claw_def.topic}/cmd', Int16Pair, lambda m: self.claw.write_speed(m.left, m.right))

        self.enc_pub_l = rospy.Publisher(f'{self.claw_def.topic}/enc/left', UInt32, queue_size=10)
        self.enc_pub_r = rospy.Publisher(f'{self.claw_def.topic}/enc/right', UInt32, queue_size=10)

    def tick(self):
        enc_left, enc_right = self.claw.read_encs()
        if enc_left is not None:
            self.enc_pub_l.publish(UInt32(enc_left))
        if enc_right is not None:
            self.enc_pub_r.publish(UInt32(enc_right))

def main():
    rospy.init_node('drive_roboclaw')

    com_port = cast(str, rospy.get_param('~com_port'))
    baud = rospy.get_param('~baud', 115200)
    timeout = rospy.get_param('~timeout', 0.01)
    mock = rospy.get_param('~mock', False)
    time_warp = rospy.get_param('~time_warp', 1)
    claw_defs_dto = cast(Dict[str, Dict[str, Any]], rospy.get_param('~claws'))

    claw_defs = [ClawDef(name, dto) for name, dto in claw_defs_dto.items()]

    with init_roboclaw(com_port, baud, timeout, mock, time_warp) as claw_chain:
        claws = [ClawInst(claw_def, claw_def.init_claw(claw_chain)) for claw_def in claw_defs]

        sleeper = rospy.Rate(30)
        while not rospy.is_shutdown():
            for claw in claws:
                claw.tick()
            sleeper.sleep()

if __name__ == '__main__':
    main()
