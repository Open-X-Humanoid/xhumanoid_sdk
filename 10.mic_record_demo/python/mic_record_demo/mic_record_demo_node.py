#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mic Record Demo Node (Python version)

通过 /lyre/audio_control 服务开启拾音器原始音频流，
订阅 /lyre/audio_stream 话题接收音频数据并保存为 WAV 文件。
"""

import os
import struct
import threading
from datetime import datetime

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
from lyre_msgs.srv import AudioControl
from lyre_msgs.msg import AudioFrame


class MicRecordDemoNode(Node):
    """ROS2 Node for microphone recording via lyre audio stream"""

    def __init__(self):
        super().__init__('mic_record_demo_node')

        self.is_recording = False
        self.current_file = ''
        self.audio_data = bytearray()
        self.sample_rate = 0
        self.channels = 0
        self.bits_per_sample = 0
        self.frame_count = 0
        self.lock = threading.Lock()

        self.declare_parameter('output_dir', '/tmp')
        self.declare_parameter('max_duration', 60)

        self.output_dir = self.get_parameter('output_dir').get_parameter_value().string_value
        self.max_duration = self.get_parameter('max_duration').get_parameter_value().integer_value

        self.audio_control_client = self.create_client(
            AudioControl, '/lyre/audio_control')

        self.audio_stream_sub = self.create_subscription(
            AudioFrame, '/lyre/audio_stream',
            self.audio_stream_callback, 10)

        self.status_pub = self.create_publisher(String, 'mic_record/status', 10)
        self.recording_pub = self.create_publisher(Bool, 'mic_record/is_recording', 10)

        self.status_timer = self.create_timer(0.5, self.publish_status)

        from std_srvs.srv import Empty
        self.start_srv = self.create_service(
            Empty, '/mic_record/start', self.start_recording_callback)
        self.stop_srv = self.create_service(
            Empty, '/mic_record/stop', self.stop_recording_callback)

        self.get_logger().info('Mic Record Demo Node initialized')
        self.get_logger().info(f'  Output directory: {self.output_dir}')
        self.get_logger().info(f'  Max duration: {self.max_duration}s')
        self.get_logger().info('')
        self.get_logger().info('Commands:')
        self.get_logger().info('  ros2 service call /mic_record/start std_srvs/srv/Empty')
        self.get_logger().info('  ros2 service call /mic_record/stop std_srvs/srv/Empty')
        self.get_logger().info('')
        self.get_logger().info('Audio data source: /lyre/audio_stream')
        self.get_logger().info('Audio control: /lyre/audio_control')

    def start_recording_callback(self, request, response):
        self.start_recording()
        return response

    def stop_recording_callback(self, request, response):
        self.stop_recording()
        return response

    def start_recording(self):
        if self.is_recording:
            self.get_logger().warn('Already recording')
            return

        if not self.audio_control_client.wait_for_service(timeout_sec=3.0):
            self.get_logger().error('AudioControl service not available')
            return

        req = AudioControl.Request()
        req.enable = True
        future = self.audio_control_client.call_async(req)
        future.add_done_callback(self._on_audio_control_start_response)

    def _on_audio_control_start_response(self, future):
        try:
            resp = future.result()
            if resp.success:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                self.current_file = os.path.join(
                    self.output_dir, f'recording_{timestamp}.wav')
                with self.lock:
                    self.audio_data = bytearray()
                    self.frame_count = 0
                self.is_recording = True
                self._publish_status_update('recording_started')
                self.get_logger().info(
                    f'Recording started, will save to: {self.current_file}')

                if self.max_duration > 0:
                    self.max_timer = self.create_timer(
                        float(self.max_duration), self._on_max_duration)
            else:
                self.get_logger().error(
                    f'Failed to enable audio stream: {resp.message}')
        except Exception as e:
            self.get_logger().error(f'AudioControl call failed: {e}')

    def _on_max_duration(self):
        self.max_timer.cancel()
        self.get_logger().info('Max recording duration reached')
        self.stop_recording()

    def stop_recording(self):
        if not self.is_recording:
            self.get_logger().warn('Not recording')
            return

        self.is_recording = False

        if hasattr(self, 'max_timer'):
            self.max_timer.cancel()

        req = AudioControl.Request()
        req.enable = False
        if self.audio_control_client.service_is_ready():
            future = self.audio_control_client.call_async(req)
            future.add_done_callback(
                lambda f: self.get_logger().info('Audio stream disabled'))

        self._save_wav()
        self._publish_status_update('recording_stopped')

    def audio_stream_callback(self, msg: AudioFrame):
        if not self.is_recording:
            return

        with self.lock:
            if self.frame_count == 0:
                self.sample_rate = msg.sample_rate
                self.channels = msg.channels
                self.bits_per_sample = msg.bits_per_sample
                self.get_logger().info(
                    f'Audio format: {self.sample_rate}Hz, {self.channels}ch, '
                    f'{self.bits_per_sample}bit')

            self.audio_data.extend(msg.data)
            self.frame_count += 1

    def _save_wav(self):
        with self.lock:
            data = bytes(self.audio_data)
            sr = self.sample_rate or 16000
            ch = self.channels or 1
            bps = self.bits_per_sample or 16

        if not data:
            self.get_logger().warn('No audio data captured')
            return

        byte_rate = sr * ch * (bps // 8)
        block_align = ch * (bps // 8)
        data_size = len(data)

        header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF', 36 + data_size, b'WAVE',
            b'fmt ', 16, 1, ch, sr, byte_rate, block_align, bps,
            b'data', data_size
        )

        try:
            os.makedirs(os.path.dirname(self.current_file) or '.', exist_ok=True)
            with open(self.current_file, 'wb') as f:
                f.write(header)
                f.write(data)
            self.get_logger().info(
                f'Recording saved: {self.current_file} '
                f'({data_size} bytes, {self.frame_count} frames)')
        except Exception as e:
            self.get_logger().error(f'Failed to save WAV: {e}')

    def publish_status(self):
        msg = Bool()
        msg.data = self.is_recording
        self.recording_pub.publish(msg)

    def _publish_status_update(self, status: str):
        msg = String()
        msg.data = status
        self.status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = MicRecordDemoNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_recording()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
