#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MuJoCo simulator node for the BrainCo-style dexterous hands.

Serves the topics used by brainco_hand_gesture_control and
brainco_hand_touch_display, for each hand in the `hands` parameter:

  subscribes  /<hand>/set_motor_multi  brainco_hand_msgs/SetMotorMulti
  publishes   /<hand>/motor_status     brainco_hand_msgs/MotorStatus
              /<hand>/touch_status     brainco_hand_msgs/TouchStatus

Only mode 1 (position) is simulated. The default speed (command speed 0)
covers the full 1..1000 range in `full_stroke_s` seconds; this value and the
hand geometry are placeholders, not measurements of the real hand.
Tangential force, direction and proximity are not simulated.
"""

import time

import mujoco
import numpy as np
import rclpy
from rclpy.node import Node

from brainco_hand_msgs.msg import MotorStatus, SetMotorMulti, TouchStatus
from brainco_hand_msgs.msg import TouchStatusItem

from xhumanoid_mujoco_sim.hand_model import (
    MOTOR_RANGE, POS_MAX, POS_MIN, build_hand_mjcf,
)

MODE_POSITION = 1
N_MOTORS = 6
# Motor index -> actuator name in hand_model.build_hand_mjcf.
ACTUATORS = ['thumb_flex', 'thumb_rotate', 'index', 'middle', 'ring', 'pinky']
# Touch sensor order of TouchStatus.data: thumb, index, middle, ring, little.
TOUCH_SENSORS = ['touch_thumb', 'touch_index', 'touch_middle', 'touch_ring',
                 'touch_pinky']
INVALID_DIRECTION = 65535


class Hand:
    """One simulated hand and its protocol-level state."""

    def __init__(self, name: str, side: float):
        self.name = name
        self.model = mujoco.MjModel.from_xml_string(build_hand_mjcf(side))
        self.data = mujoco.MjData(self.model)
        m = self.model
        self.act_id = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, n)
                       for n in ACTUATORS]
        self.qpos_adr = [int(m.jnt_qposadr[m.actuator_trnid[a, 0]])
                         for a in self.act_id]
        self.dof_adr = [int(m.jnt_dofadr[m.actuator_trnid[a, 0]])
                        for a in self.act_id]
        self.touch_adr = []
        for n in TOUCH_SENSORS:
            sid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SENSOR, n)
            self.touch_adr.append(int(m.sensor_adr[sid]))
        self.scale = np.array(MOTOR_RANGE) / float(POS_MAX - POS_MIN)
        self.target = np.full(N_MOTORS, float(POS_MIN))     # protocol units
        self.setpoint = self.target.copy()                  # rate-limited

    def to_angle(self, units):
        return (np.asarray(units) - POS_MIN) * self.scale

    def to_units(self, angle):
        return np.asarray(angle) / self.scale + POS_MIN

    def step(self, dt: float, max_rate: float):
        """Advance one physics step; max_rate in protocol units per second."""
        delta = float(max_rate) * dt
        self.setpoint += np.clip(self.target - self.setpoint, -delta, delta)
        self.data.ctrl[self.act_id] = self.to_angle(self.setpoint)
        mujoco.mj_step(self.model, self.data)

    def motor_units(self):
        q = self.data.qpos[self.qpos_adr]
        dq = self.data.qvel[self.dof_adr]
        return self.to_units(q), dq / self.scale


class HandSimNode(Node):

    def __init__(self):
        super().__init__('brainco_hand_mujoco_sim')
        self.declare_parameter('hands', ['left_hand', 'right_hand'])
        self.declare_parameter('state_rate_hz', 50.0)
        self.declare_parameter('full_stroke_s', 0.8)

        self.full_stroke_s = float(self.get_parameter('full_stroke_s').value)
        self.max_rate = (POS_MAX - POS_MIN) / self.full_stroke_s
        self.warned = set()
        self.hands = {}
        self.status_pubs, self.touch_pubs = {}, {}
        for name in self.get_parameter('hands').value:
            side = -1.0 if name.startswith('left') else 1.0
            self.hands[name] = Hand(name, side)
            self.create_subscription(
                SetMotorMulti, f'/{name}/set_motor_multi',
                lambda msg, n=name: self.on_command(n, msg), 10)
            self.status_pubs[name] = self.create_publisher(
                MotorStatus, f'/{name}/motor_status', 10)
            self.touch_pubs[name] = self.create_publisher(
                TouchStatus, f'/{name}/touch_status', 10)

        self.tick_dt = 1.0 / float(self.get_parameter('state_rate_hz').value)
        self.last_wall = time.monotonic()
        self.create_timer(self.tick_dt, self.on_tick)
        self.get_logger().info(
            f'Hand simulator ready for: {", ".join(self.hands)}')

    def on_command(self, name: str, msg: SetMotorMulti):
        if msg.mode != MODE_POSITION:
            if msg.mode not in self.warned:
                self.warned.add(msg.mode)
                self.get_logger().warn(
                    f'SetMotorMulti mode {msg.mode} is not simulated, '
                    'command ignored (only mode 1, position, is supported)')
            return
        positions = np.asarray(list(msg.positions), dtype=float)
        self.hands[name].target = np.clip(positions, POS_MIN, POS_MAX)

    def on_tick(self):
        now = time.monotonic()
        wall_dt = min(now - self.last_wall, 0.05)
        self.last_wall = now
        for hand in self.hands.values():
            dt = hand.model.opt.timestep
            for _ in range(max(1, round(wall_dt / dt))):
                hand.step(dt, self.max_rate)
            self.publish(hand)

    def publish(self, hand: Hand):
        units, speed = hand.motor_units()
        status = MotorStatus()
        status.positions = [int(v) for v in np.clip(
            np.rint(units), 0, 65535)]
        status.speeds = [int(v) for v in np.clip(np.rint(speed), -32768, 32767)]
        status.currents = [0] * N_MOTORS
        status.states = [0] * N_MOTORS
        self.status_pubs[hand.name].publish(status)

        touch = TouchStatus()
        items = []
        for adr in hand.touch_adr:
            item = TouchStatusItem()
            force = float(hand.data.sensordata[adr])        # N, normal
            item.normal_force1 = int(np.clip(round(force * 100.0), 0, 65535))
            item.tangential_force1 = 0
            item.tangential_direction1 = INVALID_DIRECTION
            item.self_proximity1 = 0
            item.status = 0
            items.append(item)
        touch.data = items
        self.touch_pubs[hand.name].publish(touch)


def main(args=None):
    rclpy.init(args=args)
    node = HandSimNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
