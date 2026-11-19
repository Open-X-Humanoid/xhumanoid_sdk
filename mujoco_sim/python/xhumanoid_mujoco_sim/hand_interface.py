"""ROS interface of the simulated BrainCo-style dexterous hands.

Serves the topics used by brainco_hand_gesture_control and
brainco_hand_touch_display for one hand of the scene built by
xhumanoid_mujoco_sim.scene:

  subscribes  /<hand>/set_motor_multi  brainco_hand_msgs/SetMotorMulti
  publishes   /<hand>/motor_status     brainco_hand_msgs/MotorStatus
              /<hand>/touch_status     brainco_hand_msgs/TouchStatus

Only mode 1 (position) is simulated. The default speed (command speed 0)
covers the full 1..1000 range in `full_stroke_s` seconds; this value and the
hand geometry are placeholders, not measurements of the real hand.
Tangential force, direction and proximity are not simulated.
"""

import mujoco
import numpy as np

from brainco_hand_msgs.msg import (
    MotorStatus, SetMotorMulti, TouchStatus, TouchStatusItem,
)

from xhumanoid_mujoco_sim.hand_model import (
    ACTUATORS, MOTOR_RANGE, POS_MAX, POS_MIN, TOUCH_SENSORS,
)
from xhumanoid_mujoco_sim.scene import hand_prefix

MODE_POSITION = 1
N_MOTORS = 6
INVALID_DIRECTION = 65535


class Hand:
    """One hand inside a shared MjModel/MjData, with protocol-level state."""

    def __init__(self, name: str, model: mujoco.MjModel, data: mujoco.MjData):
        self.name = name
        self.model = model
        self.data = data
        prefix = hand_prefix(name)
        m = model
        self.act_id = [
            mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, prefix + n)
            for n in ACTUATORS]
        self.qpos_adr = [int(m.jnt_qposadr[m.actuator_trnid[a, 0]])
                         for a in self.act_id]
        self.dof_adr = [int(m.jnt_dofadr[m.actuator_trnid[a, 0]])
                        for a in self.act_id]
        self.touch_adr = [
            int(m.sensor_adr[mujoco.mj_name2id(
                m, mujoco.mjtObj.mjOBJ_SENSOR, prefix + n)])
            for n in TOUCH_SENSORS]
        self.scale = np.array(MOTOR_RANGE) / float(POS_MAX - POS_MIN)
        self.target = np.full(N_MOTORS, float(POS_MIN))     # protocol units
        self.setpoint = self.target.copy()                  # rate-limited

    def to_angle(self, units):
        return (np.asarray(units) - POS_MIN) * self.scale

    def to_units(self, angle):
        return np.asarray(angle) / self.scale + POS_MIN

    def update_ctrl(self, dt: float, max_rate: float):
        """Move the setpoint towards the target; max_rate in units per second."""
        delta = float(max_rate) * dt
        self.setpoint += np.clip(self.target - self.setpoint, -delta, delta)
        self.data.ctrl[self.act_id] = self.to_angle(self.setpoint)

    def motor_units(self):
        q = self.data.qpos[self.qpos_adr]
        dq = self.data.qvel[self.dof_adr]
        return self.to_units(q), dq / self.scale


class HandPorts:
    """Subscription and publishers of one hand on a ROS node."""

    def __init__(self, node, hand: Hand):
        self.node = node
        self.hand = hand
        node.create_subscription(
            SetMotorMulti, f'/{hand.name}/set_motor_multi', self.on_command, 10)
        self.status_pub = node.create_publisher(
            MotorStatus, f'/{hand.name}/motor_status', 10)
        self.touch_pub = node.create_publisher(
            TouchStatus, f'/{hand.name}/touch_status', 10)

    def on_command(self, msg: SetMotorMulti):
        if msg.mode != MODE_POSITION:
            self.node.warn_once(
                ('hand_mode', msg.mode),
                f'SetMotorMulti mode {msg.mode} is not simulated, command '
                'ignored (only mode 1, position, is supported)')
            return
        positions = np.asarray(list(msg.positions), dtype=float)
        self.hand.target = np.clip(positions, POS_MIN, POS_MAX)

    def publish(self):
        units, speed = self.hand.motor_units()
        status = MotorStatus()
        status.positions = [int(v) for v in np.clip(np.rint(units), 0, 65535)]
        status.speeds = [int(v) for v in np.clip(np.rint(speed),
                                                 -32768, 32767)]
        status.currents = [0] * N_MOTORS
        status.states = [0] * N_MOTORS
        self.status_pub.publish(status)

        touch = TouchStatus()
        items = []
        for adr in self.hand.touch_adr:
            item = TouchStatusItem()
            force = float(self.hand.data.sensordata[adr])    # N, normal
            item.normal_force1 = int(np.clip(round(force * 100.0), 0, 65535))
            item.tangential_force1 = 0
            item.tangential_direction1 = INVALID_DIRECTION
            item.self_proximity1 = 0
            item.status = 0
            items.append(item)
        touch.data = items
        self.touch_pub.publish(touch)
