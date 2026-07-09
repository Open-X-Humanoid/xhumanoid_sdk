#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BrainCo Hand Touch Display Node (Python version)

Real-time printing of tactile feedback status from BrainCo dexterous hands.
Subscribes to /left_hand/touch_status and /right_hand/touch_status topics.
"""

import rclpy
from rclpy.node import Node
from brainco_hand_msgs.msg import TouchStatus


FINGER_NAMES = ['Thumb', 'Index', 'Middle', 'Ring', 'Little']


class TouchDisplayNode(Node):
    """ROS2 Node for real-time BrainCo hand touch status display"""

    def __init__(self):
        super().__init__('touch_display_node')

        self.declare_parameter('enable_left', True)
        self.declare_parameter('enable_right', True)
        self.declare_parameter('print_interval', 1.0)

        self.enable_left = self.get_parameter('enable_left').get_parameter_value().bool_value
        self.enable_right = self.get_parameter('enable_right').get_parameter_value().bool_value
        print_interval = self.get_parameter('print_interval').get_parameter_value().double_value

        self.left_touch: TouchStatus = None
        self.right_touch: TouchStatus = None

        if self.enable_left:
            self.create_subscription(
                TouchStatus, '/left_hand/touch_status',
                self._left_callback, 10
            )
        if self.enable_right:
            self.create_subscription(
                TouchStatus, '/right_hand/touch_status',
                self._right_callback, 10
            )

        self.timer = self.create_timer(print_interval, self._print_callback)

        self.get_logger().info('Touch Display Node initialized')
        if self.enable_left:
            self.get_logger().info('  Subscribed: /left_hand/touch_status')
        if self.enable_right:
            self.get_logger().info('  Subscribed: /right_hand/touch_status')
        self.get_logger().info(f'  Print interval: {print_interval:.1f}s')

    def _left_callback(self, msg: TouchStatus):
        self.left_touch = msg

    def _right_callback(self, msg: TouchStatus):
        self.right_touch = msg

    def _print_callback(self):
        lines = ['=' * 70]

        if self.enable_left:
            lines.append(self._format_hand('Left Hand', self.left_touch))
        if self.enable_right:
            lines.append(self._format_hand('Right Hand', self.right_touch))

        lines.append('=' * 70)
        self.get_logger().info('\n' + '\n'.join(lines))

    @staticmethod
    def _format_hand(title: str, msg: TouchStatus) -> str:
        if msg is None:
            return f'  [{title}] No data received'

        lines = [f'  [{title}]']
        header = (
            f'  {"Finger":<8} | {"Normal(N)":>10} | {"Tangential(N)":>14} | '
            f'{"Direction(°)":>13} | {"Proximity":>10} | {"Status":>6}'
        )
        lines.append(header)
        lines.append('  ' + '-' * len(header.strip()))

        for i, name in enumerate(FINGER_NAMES):
            if i >= len(msg.data):
                break
            item = msg.data[i]

            normal = f'{item.normal_force1 / 100.0:.2f}'
            tangential = f'{item.tangential_force1 / 100.0:.2f}'

            if item.tangential_direction1 == 65535:
                direction = 'N/A'
            else:
                direction = f'{item.tangential_direction1}'

            proximity = f'{item.self_proximity1}'

            status_low = item.status & 0xFF
            if status_low == 0:
                status_str = 'OK'
            elif status_low == 1:
                status_str = 'ERR'
            elif status_low == 2:
                status_str = 'COMM'
            else:
                status_str = f'0x{item.status:04X}'

            lines.append(
                f'  {name:<8} | {normal:>10} | {tangential:>14} | '
                f'{direction:>13} | {proximity:>10} | {status_str:>6}'
            )

        return '\n'.join(lines)


def main(args=None):
    rclpy.init(args=args)
    node = TouchDisplayNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
