#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Speaker Play Demo Node (Python version)

通过 /intelligent_interaction/tts/play 服务（interaction_msgs/srv/TtsService）
实现音频播放控制，支持文本/文件/URL三种播报方式。
"""

import os
import threading

import rclpy
from rclpy.node import Node
from interaction_msgs.srv import TtsService


class SpeakerPlayDemoNode(Node):
    """ROS2 Node for speaker play demo via TtsService"""

    def __init__(self):
        super().__init__('speaker_play_demo_node')

        self.declare_parameter('default_text', '你好，我是天工机器人。')
        self.declare_parameter('default_audio_path', '/tmp/test.wav')
        self.declare_parameter('auto_play_on_start', False)

        self.default_text = self.get_parameter('default_text').get_parameter_value().string_value
        self.default_audio_path = self.get_parameter('default_audio_path').get_parameter_value().string_value
        self.auto_play_on_start = self.get_parameter('auto_play_on_start').get_parameter_value().bool_value

        self.tts_client = self.create_client(
            TtsService, '/intelligent_interaction/tts/play')

        self.get_logger().info('Speaker Play Demo Node initialized')
        self.get_logger().info(f'  Default text: {self.default_text}')
        self.get_logger().info(f'  Default audio path: {self.default_audio_path}')

        self.get_logger().info('Waiting for TTS service...')
        if self.tts_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().info('TTS service is ready')
        else:
            self.get_logger().warn('TTS service not available, will retry when needed')

        if self.auto_play_on_start:
            def delayed_play():
                import time
                time.sleep(1)
                self.play_text(self.default_text)
            threading.Thread(target=delayed_play, daemon=True).start()

    def _call_tts(self, text: str, res_type: str, cmd: str):
        """Call TTS service"""
        if not self.tts_client.service_is_ready():
            self.get_logger().error('TTS service is not ready')
            return

        request = TtsService.Request()
        request.text = text
        request.type = res_type
        request.cmd = cmd

        self.get_logger().info(
            f'TTS call: text="{text[:50]}", type={res_type}, cmd={cmd}')

        future = self.tts_client.call_async(request)
        future.add_done_callback(self._tts_response_callback)

    def _tts_response_callback(self, future):
        try:
            response = future.result()
            if response.success:
                self.get_logger().info(f'TTS success. Status: {response.status}')
            else:
                self.get_logger().error(f'TTS failed. Status: {response.status}')
        except Exception as e:
            self.get_logger().error(f'TTS service call failed: {e}')

    def play_text(self, text: str):
        """Play text via TTS"""
        self._call_tts(text, 'text', 'append')

    def play_file(self, path: str):
        """Play audio file"""
        if not os.path.exists(path):
            self.get_logger().error(f'Audio file does not exist: {path}')
            return
        self._call_tts(path, 'file', 'append')

    def play_url(self, url: str):
        """Play audio from URL"""
        self._call_tts(url, 'url', 'append')

    def stop(self):
        """Stop current playback"""
        self._call_tts('', 'text', 'stop')

    def query_status(self):
        """Query playback status"""
        self._call_tts('', 'text', 'query')


def print_help():
    print('\n========================================')
    print('Speaker Play Demo - Commands:')
    print('  text <content>  - Play text via TTS')
    print('  play <path>     - Play audio file')
    print('  url <url>       - Play audio from URL')
    print('  stop            - Stop playback')
    print('  status          - Query playback status')
    print('  help            - Show this help')
    print('  quit            - Exit program')
    print('========================================')


def main(args=None):
    rclpy.init(args=args)
    node = SpeakerPlayDemoNode()

    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    try:
        print_help()

        while rclpy.ok():
            try:
                line = input()
                if not line:
                    continue

                parts = line.split(maxsplit=1)
                cmd = parts[0]

                if cmd == 'text':
                    if len(parts) > 1:
                        node.play_text(parts[1])
                    else:
                        node.play_text(node.default_text)
                elif cmd == 'play':
                    if len(parts) > 1:
                        node.play_file(parts[1])
                    else:
                        node.play_file(node.default_audio_path)
                elif cmd == 'url':
                    if len(parts) > 1:
                        node.play_url(parts[1])
                    else:
                        print('Usage: url <url>')
                elif cmd == 'stop':
                    node.stop()
                elif cmd == 'status':
                    node.query_status()
                elif cmd == 'help':
                    print_help()
                elif cmd in ('quit', 'exit'):
                    break
                else:
                    print(f'Unknown command: {cmd}')
                    print_help()
            except EOFError:
                break
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        spin_thread.join(timeout=1.0)


if __name__ == '__main__':
    main()
