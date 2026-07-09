#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
灵巧手手势控制节点 (Python version)

该节点通过位置模式控制灵巧手实现预设手势:
- OK手势: 大拇指和食指捏合,其他手指伸直
- 石头: 所有手指弯曲握拳
- 剪刀: 食指和中指伸直,其他手指弯曲
- 布: 所有手指伸直张开

手指索引 (6个电机):
- 0: 拇指弯曲
- 1: 拇指旋转
- 2: 食指
- 3: 中指
- 4: 无名指
- 5: 小指
"""

import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup

from brainco_hand_msgs.msg import SetMotorMulti, MotorStatus
from brainco_hand_gesture_interfaces.srv import GestureCommand


class HandGestureControl(Node):
    """ROS2 Node for hand gesture control"""

    # Finger indices
    THUMB_FLEX = 0      # 拇指弯曲
    THUMB_ROTATE = 1    # 拇指旋转
    INDEX = 2           # 食指
    MIDDLE = 3          # 中指
    RING = 4            # 无名指
    PINKY = 5           # 小指

    # Motor count
    MOTOR_COUNT = 6

    # Position range
    POS_MIN = 1         # 完全伸直
    POS_MAX = 1000      # 完全弯曲

    def __init__(self):
        super().__init__('brainco_hand_gesture_control')

        # Declare parameters
        self.declare_parameter('hand_prefix', 'right_hand')
        self.declare_parameter('control_mode', 1)

        # Get parameters
        self.hand_prefix = self.get_parameter('hand_prefix').get_parameter_value().string_value
        self.control_mode = self.get_parameter('control_mode').get_parameter_value().integer_value

        # Build topic names
        motor_cmd_topic = f'{self.hand_prefix}/set_motor_multi'
        motor_status_topic = f'{self.hand_prefix}/motor_status'

        # Create motor control publisher
        self.motor_pub = self.create_publisher(
            SetMotorMulti,
            motor_cmd_topic,
            10
        )

        # Create motor status subscriber
        self.status_sub = self.create_subscription(
            MotorStatus,
            motor_status_topic,
            self.status_callback,
            10
        )

        # Callback group for concurrent service callbacks
        self.callback_group = ReentrantCallbackGroup()

        # Create gesture control service
        self.gesture_service = self.create_service(
            GestureCommand,
            'gesture_command',
            self.gesture_command_callback,
            callback_group=self.callback_group
        )

        # Initialize gesture positions
        self.gesture_positions = self._init_gesture_positions()

        # Current motor status
        self.current_status = None

        self.get_logger().info('灵巧手手势控制节点已启动')
        self.get_logger().info(f'手: {self.hand_prefix}')
        self.get_logger().info(f'控制话题: {motor_cmd_topic}')
        self.get_logger().info(f'状态话题: {motor_status_topic}')
        self.get_logger().info('服务: /gesture_command')
        self.get_logger().info('支持的手势: ok, rock(石头), scissors(剪刀), paper(布)')

    def _init_gesture_positions(self):
        """Initialize gesture position mappings"""
        return {
            'ok': [
                450,     # 拇指弯曲: 中等弯曲
                800,     # 拇指旋转: 适当旋转角度
                450,     # 食指: 弯曲与拇指捏合
                self.POS_MIN,  # 中指: 伸直
                self.POS_MIN,  # 无名指: 伸直
                self.POS_MIN   # 小指: 伸直
            ],
            'rock': [
                800,     # 拇指弯曲: 完全弯曲
                500,     # 拇指旋转: 中间位置
                900,     # 食指: 完全弯曲
                900,     # 中指: 完全弯曲
                900,     # 无名指: 完全弯曲
                900      # 小指: 完全弯曲
            ],
            'scissors': [
                800,     # 拇指弯曲: 弯曲
                500,     # 拇指旋转: 中间位置
                self.POS_MIN,  # 食指: 伸直
                self.POS_MIN,  # 中指: 伸直
                900,     # 无名指: 弯曲
                900      # 小指: 弯曲
            ],
            'paper': [
                self.POS_MIN,  # 拇指弯曲: 伸直
                200,     # 拇指旋转: 张开角度
                self.POS_MIN,  # 食指: 伸直
                self.POS_MIN,  # 中指: 伸直
                self.POS_MIN,  # 无名指: 伸直
                self.POS_MIN   # 小指: 伸直
            ]
        }

    def status_callback(self, msg):
        """Motor status callback"""
        self.current_status = msg

    def gesture_command_callback(self, request, response):
        """Gesture command service callback"""
        gesture = request.gesture.lower()

        self.get_logger().info(f'接收到手势命令: {gesture}')

        # Check if gesture exists
        if gesture not in self.gesture_positions:
            response.success = False
            response.message = f"未知手势: '{gesture}'. 支持的手势: ok, rock, scissors, paper"
            self.get_logger().warn(response.message)
            return response

        # Execute gesture
        result = self._execute_gesture(gesture)

        response.success = result
        response.message = f"手势 '{gesture}' 执行成功" if result else f"手势 '{gesture}' 执行失败"

        if result:
            self.get_logger().info(response.message)
        else:
            self.get_logger().error(response.message)

        return response

    def _execute_gesture(self, gesture):
        """Execute gesture by publishing control command"""
        msg = SetMotorMulti()
        msg.mode = self.control_mode  # 位置模式 = 1

        # Get gesture positions
        positions = self.gesture_positions[gesture]

        # Set finger positions
        for i in range(self.MOTOR_COUNT):
            msg.positions[i] = positions[i]
            msg.speeds[i] = 0     # 速度 0 表示使用默认速度
            msg.currents[i] = 0
            msg.pwms[i] = 0
            msg.durations[i] = 0

        finger_names = ['拇指弯曲', '拇指旋转', '食指', '中指', '无名指', '小指']
        self.get_logger().info(f'正在执行手势: {gesture}')
        self.get_logger().debug(
            f'位置: {finger_names[0]}={positions[0]}, {finger_names[1]}={positions[1]}, '
            f'{finger_names[2]}={positions[2]}, {finger_names[3]}={positions[3]}, '
            f'{finger_names[4]}={positions[4]}, {finger_names[5]}={positions[5]}'
        )

        # Publish control command
        self.motor_pub.publish(msg)

        return True


def main(args=None):
    rclpy.init(args=args)
    node = HandGestureControl()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()