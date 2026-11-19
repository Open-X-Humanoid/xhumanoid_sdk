#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MuJoCo simulator node exposing the xhumanoid_sdk robot interface.

Subscribes /arm/cmd (ros2_bridge_msgs/ArmCtrl) and publishes /robot_state
(ros2_bridge_msgs/RobotState), so SDK examples such as single_joint_control
can run without the robot. The base is fixed to the world; there is no
balance controller.

Supported ArmCtrl modes: 0 (position) and 1 (force-position hybrid).
Mode 0 is approximated: the setpoint moves towards `pos` at `spd` rad/s and
is tracked by a PD law using the gains of the model's position actuators.
`cur` is ignored because the model has no motor current model.
"""

import math
import os
import time

import mujoco
import numpy as np
import rclpy
from rclpy.node import Node

from ros2_bridge_msgs.msg import (
    ArmCtrl, ImuStatus, MotorStatus, MotorStatusGroup, RobotState,
)

# Motor id -> MJCF joint name (xSIM_MUJOCO 'full' config for tiangong3).
MOTOR_ID_TO_JOINT = {
    1: 'head_roll_joint', 2: 'head_pitch_joint', 3: 'head_yaw_joint',
    11: 'shoulder_pitch_l_joint', 12: 'shoulder_roll_l_joint',
    13: 'shoulder_yaw_l_joint', 14: 'elbow_pitch_l_joint',
    15: 'elbow_yaw_l_joint', 16: 'wrist_pitch_l_joint',
    17: 'wrist_roll_l_joint',
    21: 'shoulder_pitch_r_joint', 22: 'shoulder_roll_r_joint',
    23: 'shoulder_yaw_r_joint', 24: 'elbow_pitch_r_joint',
    25: 'elbow_yaw_r_joint', 26: 'wrist_pitch_r_joint',
    27: 'wrist_roll_r_joint',
    31: 'waist_pitch_joint', 32: 'waist_roll_joint', 33: 'waist_yaw_joint',
    51: 'hip_pitch_l_joint', 52: 'hip_roll_l_joint', 53: 'hip_yaw_l_joint',
    54: 'knee_pitch_l_joint', 55: 'ankle_pitch_l_joint',
    56: 'ankle_roll_l_joint',
    61: 'hip_pitch_r_joint', 62: 'hip_roll_r_joint', 63: 'hip_yaw_r_joint',
    64: 'knee_pitch_r_joint', 65: 'ankle_pitch_r_joint',
    66: 'ankle_roll_r_joint',
}
ARM_MOTOR_IDS = [i for i in sorted(MOTOR_ID_TO_JOINT) if 11 <= i <= 27]

MODE_POSITION = 0
MODE_HYBRID = 1


def load_model(path: str, fix_base: bool) -> mujoco.MjModel:
    """Load the MJCF, optionally welding the pelvis to the world."""
    if not fix_base:
        return mujoco.MjModel.from_xml_path(path)
    spec = mujoco.MjSpec.from_file(path)
    pelvis = spec.body('pelvis')
    for joint in list(pelvis.joints):
        spec.delete(joint)
    return spec.compile()


class JointCommand:
    """Last command received for one joint."""

    def __init__(self, hold_pos: float):
        self.mode = MODE_POSITION
        self.pos = hold_pos
        self.spd = 0.0
        self.kp = 0.0
        self.kd = 0.0
        self.tor = 0.0
        self.setpoint = hold_pos  # rate-limited setpoint for mode 0


class SimNode(Node):

    def __init__(self):
        super().__init__('xhumanoid_mujoco_sim')

        default_model = os.environ.get('XHUMANOID_SIM_MODEL', '')
        self.declare_parameter('model_path', default_model)
        self.declare_parameter('fix_base', True)
        self.declare_parameter('state_rate_hz', 100.0)
        self.declare_parameter('realtime_factor', 1.0)

        model_path = self.get_parameter('model_path').value
        if not model_path or not os.path.isfile(model_path):
            raise RuntimeError(
                f'MJCF model not found: "{model_path}". Run '
                'mujoco_sim/scripts/fetch_model.sh and set the model_path '
                'parameter or XHUMANOID_SIM_MODEL.')
        self.fix_base = bool(self.get_parameter('fix_base').value)
        self.model = load_model(model_path, self.fix_base)
        self.data = mujoco.MjData(self.model)
        mujoco.mj_forward(self.model, self.data)

        self._index_model()
        self.commands = {
            jid: JointCommand(0.0) for jid in MOTOR_ID_TO_JOINT
            if self.joint_ids[jid] >= 0
        }
        self.warned = set()
        self.sim_steps = 0

        self.create_subscription(ArmCtrl, '/arm/cmd', self.on_arm_cmd, 10)
        self.state_pub = self.create_publisher(RobotState, '/robot_state', 10)

        self.tick_dt = 1.0 / float(self.get_parameter('state_rate_hz').value)
        self.rt_factor = float(self.get_parameter('realtime_factor').value)
        self.last_wall = time.monotonic()
        self.create_timer(self.tick_dt, self.on_tick)
        self.get_logger().info(
            f'Loaded {model_path}: {self.model.nu} actuators, '
            f'timestep={self.model.opt.timestep}s, '
            f'fix_base={self.fix_base}')

    def _index_model(self):
        m = self.model

        def sensor_adr(name):
            sid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SENSOR, name)
            return -1 if sid < 0 else int(m.sensor_adr[sid])

        self.joint_ids, self.qpos_adr, self.dof_adr = {}, {}, {}
        self.motor_act, self.pd_gains = {}, {}
        for mid, jname in MOTOR_ID_TO_JOINT.items():
            jid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, jname)
            self.joint_ids[mid] = jid
            if jid < 0:
                continue
            self.qpos_adr[mid] = int(m.jnt_qposadr[jid])
            self.dof_adr[mid] = int(m.jnt_dofadr[jid])
            self.motor_act[mid] = mujoco.mj_name2id(
                m, mujoco.mjtObj.mjOBJ_ACTUATOR, f'motor_{jname}')
            pos_act = mujoco.mj_name2id(
                m, mujoco.mjtObj.mjOBJ_ACTUATOR, f'pos_{jname}')
            # <position kp kv>: gainprm[0]=kp, biasprm[1]=-kp, biasprm[2]=-kv
            self.pd_gains[mid] = (
                float(m.actuator_gainprm[pos_act, 0]),
                float(-m.actuator_biasprm[pos_act, 2]))
        self.imu_quat = sensor_adr('orientation')
        self.imu_gyro = sensor_adr('angular-velocity')
        self.imu_acc = sensor_adr('linear-acceleration')
        self.imu_site = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, 'imu')

    def warn_once(self, key, text):
        if key not in self.warned:
            self.warned.add(key)
            self.get_logger().warn(text)

    def on_arm_cmd(self, msg: ArmCtrl):
        if msg.mode not in (MODE_POSITION, MODE_HYBRID):
            self.warn_once(('mode', msg.mode),
                           f'ArmCtrl mode {msg.mode} is not supported by the '
                           'simulator, command ignored')
            return
        for ctrl in msg.ctrl:
            cmd = self.commands.get(ctrl.name)
            if cmd is None:
                self.warn_once(('id', ctrl.name),
                               f'unknown motor id {ctrl.name}, ignored')
                continue
            cmd.mode = msg.mode
            cmd.pos = float(ctrl.pos)
            cmd.spd = float(ctrl.spd)
            cmd.kp = float(ctrl.kp)
            cmd.kd = float(ctrl.kd)
            cmd.tor = float(ctrl.tor)

    def apply_control(self):
        dt = self.model.opt.timestep
        d = self.data
        for mid, cmd in self.commands.items():
            q = d.qpos[self.qpos_adr[mid]]
            dq = d.qvel[self.dof_adr[mid]]
            if cmd.mode == MODE_HYBRID:
                torque = (cmd.kp * (cmd.pos - q) + cmd.kd * (cmd.spd - dq)
                          + cmd.tor)
            else:
                if cmd.spd > 0.0:
                    step = cmd.spd * dt
                    cmd.setpoint += float(
                        np.clip(cmd.pos - cmd.setpoint, -step, step))
                else:
                    cmd.setpoint = cmd.pos
                kp, kv = self.pd_gains[mid]
                torque = kp * (cmd.setpoint - q) - kv * dq
            d.ctrl[self.motor_act[mid]] = torque  # clipped to ctrlrange by MuJoCo

    def on_tick(self):
        now = time.monotonic()
        wall_dt = min(now - self.last_wall, 0.05)  # cap catch-up after stalls
        self.last_wall = now
        n_steps = max(1, round(wall_dt * self.rt_factor
                               / self.model.opt.timestep))
        for _ in range(n_steps):
            self.apply_control()
            mujoco.mj_step(self.model, self.data)
        self.sim_steps += n_steps
        self.publish_state()

    def publish_state(self):
        d = self.data
        msg = RobotState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'

        quat = d.sensordata[self.imu_quat:self.imu_quat + 4]  # w x y z
        w, x, y, z = (float(v) for v in quat)
        roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
        pitch = math.asin(max(-1.0, min(1.0, 2 * (w * y - z * x))))
        yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
        gyro = d.sensordata[self.imu_gyro:self.imu_gyro + 3]
        if self.fix_base:
            # MuJoCo reports zero for a body welded to the world; a resting IMU
            # reads the reaction to gravity, expressed in the sensor frame.
            acc = d.site_xmat[self.imu_site].reshape(3, 3).T @ np.array(
                [0.0, 0.0, -self.model.opt.gravity[2]])
        else:
            acc = d.sensordata[self.imu_acc:self.imu_acc + 3]
        imu = ImuStatus()
        imu.roll, imu.pitch, imu.yaw = (math.degrees(v)
                                        for v in (roll, pitch, yaw))
        imu.wx, imu.wy, imu.wz = (float(v) for v in gyro)
        imu.ax, imu.ay, imu.az = (float(v) for v in acc)
        msg.imu = imu

        arm = MotorStatusGroup()
        for mid in ARM_MOTOR_IDS:
            if mid not in self.commands:
                continue
            st = MotorStatus()
            st.name = mid
            st.pos = float(d.qpos[self.qpos_adr[mid]])
            st.speed = float(d.qvel[self.dof_adr[mid]])
            st.current = float(d.actuator_force[self.motor_act[mid]])
            arm.status.append(st)
        msg.arm = arm
        self.state_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SimNode()
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
