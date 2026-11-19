#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check the hand simulator through brainco_hand_gesture_control.

Run inside the sim container with the simulator (sim.launch.py) and
brainco_hand_gesture_control_py already running. For each gesture it calls the
/gesture_command service and checks the finger positions reported on
/right_hand/motor_status and the touch readings on /right_hand/touch_status.

Motor order: 0 thumb flex, 1 thumb rotate, 2 index, 3 middle, 4 ring, 5 pinky.
"open" means position < 100, "closed" means position > 500 (range 1..1000).
"""

import sys
import time

import rclpy
from rclpy.node import Node

from brainco_hand_gesture_interfaces.srv import GestureCommand
from brainco_hand_msgs.msg import MotorStatus, TouchStatus

HAND = 'right_hand'
SETTLE_S = 3.0

# gesture -> (open motors, closed motors, expect touch > 0)
EXPECTED = {
    'paper': ([0, 2, 3, 4, 5], [], False),
    'ok': ([3, 4, 5], [], False),
    'rock': ([], [2, 3, 4, 5], True),
    'scissors': ([2, 3], [4, 5], False),
}
# 'ok' also requires index and thumb flex to be partly bent.
PARTLY_BENT = {'ok': [0, 2]}


class Checker(Node):

    def __init__(self):
        super().__init__('hand_sim_check')
        self.status = None
        self.touch = None
        self.create_subscription(
            MotorStatus, f'/{HAND}/motor_status',
            lambda m: setattr(self, 'status', m), 10)
        self.create_subscription(
            TouchStatus, f'/{HAND}/touch_status',
            lambda m: setattr(self, 'touch', m), 10)
        self.client = self.create_client(GestureCommand, '/gesture_command')

    def spin_for(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            rclpy.spin_once(self, timeout_sec=0.05)

    def wait_ready(self, timeout=30.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            rclpy.spin_once(self, timeout_sec=0.1)
            if (self.status is not None and self.touch is not None
                    and self.client.service_is_ready()):
                return True
        return False

    def call(self, gesture):
        req = GestureCommand.Request()
        req.gesture = gesture
        future = self.client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        return future.result()


def main():
    rclpy.init()
    node = Checker()
    if not node.wait_ready():
        print('FAIL: no motor_status/touch_status or /gesture_command service')
        return 1

    failures = []
    for gesture in ['paper', 'ok', 'rock', 'scissors', 'paper']:
        resp = node.call(gesture)
        if resp is None or not resp.success:
            failures.append(f'{gesture}: service call failed ({resp})')
            continue
        node.spin_for(SETTLE_S)
        pos = list(node.status.positions)
        force = [item.normal_force1 for item in node.touch.data]
        print(f'{gesture:9s} positions={pos} normal_force(0.01N)={force}')
        opened, closed, want_touch = EXPECTED[gesture]
        for i in opened:
            if pos[i] >= 100:
                failures.append(f'{gesture}: motor {i} = {pos[i]}, expected open')
        for i in closed:
            if pos[i] <= 500:
                failures.append(f'{gesture}: motor {i} = {pos[i]}, expected closed')
        for i in PARTLY_BENT.get(gesture, []):
            if not 250 < pos[i] < 700:
                failures.append(f'{gesture}: motor {i} = {pos[i]}, expected partly bent')
        if want_touch and max(force) == 0:
            failures.append(f'{gesture}: expected a non-zero touch reading')
        if not want_touch and gesture == 'paper' and max(force) != 0:
            failures.append(f'{gesture}: unexpected touch reading {force}')

    bad = node.call('wave')
    if bad is None or bad.success:
        failures.append('unknown gesture "wave" should be rejected')

    node.destroy_node()
    rclpy.shutdown()
    if failures:
        print('HAND CHECK FAILED')
        for f in failures:
            print(' -', f)
        return 1
    print('HAND CHECK PASSED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
