#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Camera 6V Display Node (Python version)

This node subscribes to 6 camera image topics and displays them
in a grid layout using OpenCV.

Camera indices: 0, 1, 2, 4, 5, 6 (skipping 3 and 7)
"""

import threading
from datetime import datetime

import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge


class Camera6vDisplayNode(Node):
    """ROS2 Node for 6 camera visualization"""

    def __init__(self):
        super().__init__('camera_6v_display_node')

        # Parameters
        self.declare_parameter('display_width', 320)
        self.declare_parameter('display_height', 240)
        self.declare_parameter('use_compressed', False)
        self.declare_parameter('show_fps', True)
        self.declare_parameter('window_name', '6V Camera Display')
        self.declare_parameter('topic_prefix', 'camera')

        self.display_width = self.get_parameter('display_width').get_parameter_value().integer_value
        self.display_height = self.get_parameter('display_height').get_parameter_value().integer_value
        self.use_compressed = self.get_parameter('use_compressed').get_parameter_value().bool_value
        self.show_fps = self.get_parameter('show_fps').get_parameter_value().bool_value
        self.window_name = self.get_parameter('window_name').get_parameter_value().string_value
        self.topic_prefix = self.get_parameter('topic_prefix').get_parameter_value().string_value

        # CV Bridge
        self.bridge = CvBridge()

        # Camera indices (skipping 3 and 7)
        self.camera_indices = [0, 1, 2, 4, 5, 6]

        # Subscribers and frame storage
        self.subscribers = {}
        self.latest_frames = {}
        self.frame_counts = {}
        self.fps_values = {}
        self.frame_lock = threading.Lock()

        # Initialize subscribers
        for idx in self.camera_indices:
            topic = f'{self.topic_prefix}{idx}/image_raw'
            compressed_topic = f'{self.topic_prefix}{idx}/image/compressed'

            if self.use_compressed:
                sub = self.create_subscription(
                    CompressedImage,
                    compressed_topic,
                    lambda msg, i=idx: self.compressed_image_callback(msg, i),
                    10
                )
            else:
                sub = self.create_subscription(
                    Image,
                    topic,
                    lambda msg, i=idx: self.image_callback(msg, i),
                    10
                )
            self.subscribers[idx] = sub

            # Initialize frame statistics
            self.frame_counts[idx] = 0
            self.fps_values[idx] = 0.0

            # Initialize placeholder image
            placeholder = np.zeros((self.display_height, self.display_width, 3), dtype=np.uint8)
            placeholder[:] = (50, 50, 50)
            cv2.putText(placeholder, f'CAM {idx}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
            cv2.putText(placeholder, 'Waiting...', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
            self.latest_frames[idx] = placeholder.copy()

        # Create display timer (30 Hz)
        self.display_timer = self.create_timer(0.033, self.update_display)

        # Create FPS calculation timer (1 Hz)
        self.fps_timer = self.create_timer(1.0, self.calculate_fps)

        # Create OpenCV window
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.display_width * 3, self.display_height * 2)

        self.get_logger().info('Camera 6V Display Node initialized')
        self.get_logger().info(f'  Display size: {self.display_width}x{self.display_height} per camera')
        self.get_logger().info(f'  Use compressed: {self.use_compressed}')
        for idx in self.camera_indices:
            topic = f'{self.topic_prefix}{idx}/image/compressed' if self.use_compressed else f'{self.topic_prefix}{idx}/image_raw'
            self.get_logger().info(f'  Subscribed to: {topic}')

    def image_callback(self, msg, camera_idx):
        """Image callback"""
        try:
            # Convert ROS image to OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
            self.process_frame(cv_image, camera_idx)
        except Exception as e:
            self.get_logger().error(f'cv_bridge exception for camera {camera_idx}: {e}')

    def compressed_image_callback(self, msg, camera_idx):
        """Compressed image callback"""
        try:
            # Decode compressed image
            np_arr = np.frombuffer(msg.data, np.uint8)
            cv_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if cv_image is not None:
                # Convert BGR to RGB
                cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
                self.process_frame(cv_image, camera_idx)
        except Exception as e:
            self.get_logger().error(f'Exception decoding compressed image for camera {camera_idx}: {e}')

    def process_frame(self, frame, camera_idx):
        """Process frame"""
        # Resize frame
        resized = cv2.resize(frame, (self.display_width, self.display_height))

        # Add camera label
        label = f'CAM {camera_idx}'
        cv2.putText(resized, label, (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Add FPS if enabled
        if self.show_fps and self.fps_values[camera_idx] > 0:
            fps_text = f'{int(self.fps_values[camera_idx])} FPS'
            cv2.putText(resized, fps_text, (self.display_width - 70, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Update frame counter and store
        with self.frame_lock:
            self.frame_counts[camera_idx] += 1
            self.latest_frames[camera_idx] = resized.copy()

    def calculate_fps(self):
        """Calculate FPS for each camera"""
        with self.frame_lock:
            for idx in self.camera_indices:
                self.fps_values[idx] = self.frame_counts[idx]
                self.frame_counts[idx] = 0

    def update_display(self):
        """Update display"""
        # Create a 2x3 grid layout
        # Row 0: CAM0, CAM1, CAM2
        # Row 1: CAM4, CAM5, CAM6

        with self.frame_lock:
            # Get frames for row 0 (cameras 0, 1, 2)
            row0 = np.hstack([
                self.latest_frames[0],
                self.latest_frames[1],
                self.latest_frames[2]
            ])

            # Get frames for row 1 (cameras 4, 5, 6)
            row1 = np.hstack([
                self.latest_frames[4],
                self.latest_frames[5],
                self.latest_frames[6]
            ])

        # Combine rows
        grid = np.vstack([row0, row1])

        # Add timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cv2.putText(grid, timestamp, (10, grid.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Convert RGB to BGR for display
        display = cv2.cvtColor(grid, cv2.COLOR_RGB2BGR)

        # Show the image
        cv2.imshow(self.window_name, display)
        key = cv2.waitKey(1)

        if key == 27 or key == ord('q'):  # ESC or 'q' to quit
            self.get_logger().info('User requested shutdown')
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = Camera6vDisplayNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()