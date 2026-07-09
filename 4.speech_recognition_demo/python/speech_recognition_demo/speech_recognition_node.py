#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Speech Recognition Demo Node (Python version)

订阅 /lyre/voice_activity 话题获取ASR语音活动事件。
统一接收人脸唤醒、关键词唤醒、VAD事件、ASR识别结果等。
"""

import json

import rclpy
from rclpy.node import Node
from lyre_msgs.msg import LyreVoiceActivity


EVENT_TYPE_NAMES = {
    1: 'ASR结果',
    4: '关键词唤醒',
    5: '退出对话',
    6: 'VAD事件',
    20: '人脸识别唤醒',
}


class SpeechRecognitionNode(Node):
    """ROS2 Node for speech recognition demo via /lyre/voice_activity"""

    def __init__(self):
        super().__init__('speech_recognition_demo')

        self.voice_activity_sub = self.create_subscription(
            LyreVoiceActivity,
            '/lyre/voice_activity',
            self.voice_activity_callback,
            10
        )

        self.get_logger().info('SpeechRecognitionNode initialized')
        self.get_logger().info('Subscribed to: /lyre/voice_activity')

    def voice_activity_callback(self, msg):
        """Parse and display voice activity events"""
        try:
            data = json.loads(msg.content)
        except json.JSONDecodeError:
            self.get_logger().warn(f'Failed to parse JSON: {msg.content[:200]}')
            return

        event_type = data.get('type', '')
        content = data.get('content', {})
        trace_id = data.get('traceId', '')
        timestamp = data.get('timestamp', '')

        if event_type == 'aiui_event':
            self._handle_aiui_event(content, trace_id, timestamp)
        else:
            self.get_logger().info(f'[VoiceActivity] type={event_type}, content={msg.content[:200]}')

    def _handle_aiui_event(self, content, trace_id, timestamp):
        event_type = content.get('eventType', -1)
        event_name = EVENT_TYPE_NAMES.get(event_type, f'未知事件({event_type})')

        if event_type == 1:
            result = content.get('result', {})
            text_data = result.get('text', {})
            ws_list = text_data.get('ws', [])
            recognized_text = ''
            for ws in ws_list:
                cw_list = ws.get('cw', [])
                for cw in cw_list:
                    recognized_text += cw.get('w', '')
            self.get_logger().info(
                f'[ASR] 识别结果: "{recognized_text}" (traceId={trace_id})')

        elif event_type == 4:
            result = content.get('result', {})
            ivw = result.get('ivw', {})
            angle = ivw.get('angle', -1)
            self.get_logger().info(
                f'[唤醒] 关键词唤醒，角度: {angle}° (traceId={trace_id})')

        elif event_type == 5:
            self.get_logger().info(f'[对话] 退出对话 (traceId={trace_id})')

        elif event_type == 6:
            arg1 = content.get('arg1', -1)
            if arg1 == 0:
                self.get_logger().info(f'[VAD] 检测到语音开始 (traceId={trace_id})')
            elif arg1 == 2:
                self.get_logger().info(f'[VAD] 检测到语音结束 (traceId={trace_id})')
            else:
                self.get_logger().info(
                    f'[VAD] VAD事件 arg1={arg1} (traceId={trace_id})')

        elif event_type == 20:
            self.get_logger().info(f'[唤醒] 人脸识别唤醒 (traceId={trace_id})')

        else:
            self.get_logger().info(
                f'[事件] {event_name}, eventType={event_type} (traceId={trace_id})')


def main(args=None):
    rclpy.init(args=args)
    node = SpeechRecognitionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
