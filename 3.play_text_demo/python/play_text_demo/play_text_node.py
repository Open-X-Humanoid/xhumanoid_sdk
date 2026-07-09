#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Play Text Node (Python version)

通过调用 /intelligent_interaction/tts/play 服务实现文字转语音播放。
支持三种资源类型：文本(text)、本地音频文件(file)、远端URL(url)。
"""

import rclpy
from rclpy.node import Node
from interaction_msgs.srv import TtsService


class PlayTextNode(Node):
    """ROS2 Node for TTS text playback via interaction_msgs/TtsService"""

    def __init__(self):
        super().__init__('play_text_demo')

        self.declare_parameter('text', '你好，我是天工机器人，很高兴认识你。')
        self.declare_parameter('type', 'text')  # text / file / url
        self.declare_parameter('cmd', 'append')  # append / stop / query

        self.client = self.create_client(
            TtsService, '/intelligent_interaction/tts/play')

        self.timer = self.create_timer(0.5, self.call_tts_service)

        self.get_logger().info('PlayTextNode initialized')
        self.get_logger().info(
            f'Text: {self.get_parameter("text").get_parameter_value().string_value}')

    def call_tts_service(self):
        self.timer.cancel()

        while not self.client.wait_for_service(timeout_sec=1.0):
            if not rclpy.ok():
                self.get_logger().error('Interrupted while waiting for TTS service. Exiting.')
                return
            self.get_logger().info('TTS service not available, waiting...')

        request = TtsService.Request()
        request.text = self.get_parameter('text').get_parameter_value().string_value
        request.type = self.get_parameter('type').get_parameter_value().string_value
        request.cmd = self.get_parameter('cmd').get_parameter_value().string_value

        self.get_logger().info(
            f'Calling TTS service: text="{request.text}", type={request.type}, cmd={request.cmd}')

        self.future = self.client.call_async(request)
        self.future.add_done_callback(self.response_callback)

    def response_callback(self, future):
        try:
            response = future.result()
            if response.success:
                self.get_logger().info(
                    f'TTS service success. Status: {response.status}')
            else:
                self.get_logger().error(
                    f'TTS service failed. Status: {response.status}')
        except Exception as e:
            self.get_logger().error(f'Service call failed: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = PlayTextNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
