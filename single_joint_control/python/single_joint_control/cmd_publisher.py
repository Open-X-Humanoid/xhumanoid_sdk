#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single Joint Control Node (Python version)

This node controls a single joint motor using ROS2 topic publishing.
It demonstrates position mode and force-position hybrid mode control.
"""

import math

import rclpy
from rclpy.node import Node

from ros2_bridge_msgs.msg import ArmCtrl, MotorCtrl, RobotState


class CmdPublisher(Node):
    """ROS2 Node for single joint motor control

    Stages:
      0 - Position mode:              move joint 21 to -1.588 rad
      1 - Position mode:              move joint 21 back to 0.0 rad
      2 - Force-position hybrid mode: move joint 21 to -1.588 rad
      3 - Force-position hybrid mode: move joint 21 back to 0.0 rad
      4 - Completed
    """

    JOINT_ID = 21  # Right Shoulder Pitch
    POS_TARGET = -1.588
    POS_THRESHOLD_DEG = 5.0
    CONTROL_INTERVAL_SEC = 0.02

    # Position mode parameters
    POS_MODE = 0
    POS_SPD = 0.3
    POS_CUR = 10.0

    # Force-position hybrid mode parameters
    HYBRID_MODE = 1
    HYBRID_KP = 50.0
    HYBRID_KD = 2.0
    HYBRID_SPD = 0.0
    HYBRID_TOR = 0.0

    def __init__(self):
        super().__init__('cmd_publisher')

        self.current_pos = 0.0
        self.target_pos = 0.0
        self.stage = 0

        self.publisher = self.create_publisher(ArmCtrl, '/arm/cmd', 10)

        self.status_sub = self.create_subscription(
            RobotState, '/robot_state', self.status_callback, 10
        )

        self.timer = self.create_timer(
            self.CONTROL_INTERVAL_SEC, self.control_callback
        )

        self.get_logger().info('CmdPublisher initialized')

    def status_callback(self, msg):
        """Extract joint 21 position from RobotState"""
        for motor_status in msg.arm.status:
            if motor_status.name == self.JOINT_ID:
                self.current_pos = motor_status.pos

    def control_callback(self):
        if self.stage == 0:
            self._run_position_stage(self.POS_TARGET, next_stage=1,
                                     label='Position mode: raise arm')
        elif self.stage == 1:
            self._run_position_stage(0.0, next_stage=2,
                                     label='Position mode: lower arm')
        elif self.stage == 2:
            self._run_hybrid_stage(self.POS_TARGET, next_stage=3,
                                   label='Hybrid mode: raise arm')
        elif self.stage == 3:
            self._run_hybrid_stage(0.0, next_stage=4,
                                   label='Hybrid mode: lower arm')

    def _pos_diff_deg(self, target):
        return abs(self.current_pos - target) * 180.0 / math.pi

    def _run_position_stage(self, target, next_stage, label):
        self.target_pos = target
        diff = self._pos_diff_deg(target)
        self.get_logger().info(
            f'[Stage {self.stage}] {label}: '
            f'current={self.current_pos:.4f}, target={target:.4f}, '
            f'diff={diff:.2f} deg'
        )
        if diff < self.POS_THRESHOLD_DEG:
            self.get_logger().info(f'Stage {self.stage} completed')
            self.stage = next_stage
            if next_stage == 2:
                self.get_logger().info(
                    '--- Switching to force-position hybrid mode ---'
                )
        self._publish_position_cmd(target)

    def _run_hybrid_stage(self, target, next_stage, label):
        self.target_pos = target
        diff = self._pos_diff_deg(target)
        self.get_logger().info(
            f'[Stage {self.stage}] {label}: '
            f'current={self.current_pos:.4f}, target={target:.4f}, '
            f'diff={diff:.2f} deg'
        )
        if diff < self.POS_THRESHOLD_DEG:
            self.get_logger().info(f'Stage {self.stage} completed')
            self.stage = next_stage
            if next_stage == 4:
                self.get_logger().info('All motion stages completed!')
                self.timer.cancel()
        self._publish_hybrid_cmd(target)

    def _publish_position_cmd(self, pos):
        """Publish position mode command (mode=0)"""
        msg = ArmCtrl()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'arm'
        msg.mode = self.POS_MODE
        msg.label = 0

        ctrl = MotorCtrl()
        ctrl.name = self.JOINT_ID
        ctrl.pos = pos
        ctrl.spd = self.POS_SPD
        ctrl.cur = self.POS_CUR
        msg.ctrl.append(ctrl)

        self.publisher.publish(msg)

    def _publish_hybrid_cmd(self, pos):
        """Publish force-position hybrid mode command (mode=1)"""
        msg = ArmCtrl()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'arm'
        msg.mode = self.HYBRID_MODE
        msg.label = 0

        ctrl = MotorCtrl()
        ctrl.name = self.JOINT_ID
        ctrl.kp = self.HYBRID_KP
        ctrl.kd = self.HYBRID_KD
        ctrl.pos = pos
        ctrl.spd = self.HYBRID_SPD
        ctrl.tor = self.HYBRID_TOR
        msg.ctrl.append(ctrl)

        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = CmdPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
