#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMU Display Node with Real-time Plotting

Supports two IMU sources on the Thor platform:
- livox:  /livox/imu, 200Hz
- xsens:  /robot_state (ImuStatus field), body IMU

This node subscribes to IMU data and provides:
- Real-time plotting of orientation (roll, pitch, yaw)
- Real-time plotting of angular velocity (gyroscope)
- Real-time plotting of linear acceleration (accelerometer)
- Save plot to node directory (works in headless mode)
- Statistics logging
- RViz marker visualization
"""

import os
import sys
import math
from collections import deque
from datetime import datetime

# Use non-interactive backend for headless mode (must be imported before matplotlib)
import matplotlib
matplotlib.use('Agg')  # Use Agg backend for saving without display

import matplotlib.pyplot as plt
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Imu
from visualization_msgs.msg import Marker, MarkerArray
from ros2_bridge_msgs.msg import RobotState

RAD_TO_DEG = 57.2957795130823

IMU_SOURCE_CONFIG = {
    'livox':  {'topic': '/livox/imu',   'type': 'sensor_msgs', 'desc': 'Livox雷达IMU'},
    'xsens':  {'topic': '/robot_state', 'type': 'robot_state', 'desc': 'Xsens体内IMU（通过/robot_state）'},
}


class IMUDisplayNode(Node):
    """ROS2 Node for IMU data visualization with plotting"""

    def __init__(self):
        super().__init__('imu_display_node')

        # Get the directory where this node script is located
        self.node_dir = os.path.dirname(os.path.abspath(__file__))

        # Declare parameters
        self.declare_parameter('imu_source', 'livox')
        self.declare_parameter('imu_topic', '')
        self.declare_parameter('frame_id', 'base_link')
        self.declare_parameter('history_size', 500)
        self.declare_parameter('plot_interval', 2.0)
        self.declare_parameter('save_format', 'png')
        self.declare_parameter('dpi', 150)
        self.declare_parameter('plot_orientation', True)
        self.declare_parameter('plot_angular_velocity', True)
        self.declare_parameter('plot_acceleration', True)

        # Get parameters
        self.imu_source = self.get_parameter('imu_source').get_parameter_value().string_value
        imu_topic_override = self.get_parameter('imu_topic').get_parameter_value().string_value
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value
        self.history_size = self.get_parameter('history_size').get_parameter_value().integer_value
        self.plot_interval = self.get_parameter('plot_interval').get_parameter_value().double_value
        self.save_format = self.get_parameter('save_format').get_parameter_value().string_value
        self.dpi = self.get_parameter('dpi').get_parameter_value().integer_value
        self.plot_orientation = self.get_parameter('plot_orientation').get_parameter_value().bool_value
        self.plot_angular_velocity = self.get_parameter('plot_angular_velocity').get_parameter_value().bool_value
        self.plot_acceleration = self.get_parameter('plot_acceleration').get_parameter_value().bool_value

        if self.imu_source not in IMU_SOURCE_CONFIG:
            self.get_logger().error(
                f'Unknown imu_source: "{self.imu_source}". '
                f'Supported: {list(IMU_SOURCE_CONFIG.keys())}. Defaulting to livox.'
            )
            self.imu_source = 'livox'

        src_cfg = IMU_SOURCE_CONFIG[self.imu_source]
        self.imu_topic = imu_topic_override if imu_topic_override else src_cfg['topic']

        # Create save directory inside node directory
        self.save_dir = os.path.join(self.node_dir, 'plots')
        os.makedirs(self.save_dir, exist_ok=True)

        # Data storage
        self.timestamps = deque(maxlen=self.history_size)
        self.roll_data = deque(maxlen=self.history_size)
        self.pitch_data = deque(maxlen=self.history_size)
        self.yaw_data = deque(maxlen=self.history_size)
        self.gyr_x_data = deque(maxlen=self.history_size)
        self.gyr_y_data = deque(maxlen=self.history_size)
        self.gyr_z_data = deque(maxlen=self.history_size)
        self.acc_x_data = deque(maxlen=self.history_size)
        self.acc_y_data = deque(maxlen=self.history_size)
        self.acc_z_data = deque(maxlen=self.history_size)

        self.total_messages = 0
        self.last_orientation = None

        # Initialize figure and axes (reuse the same figure)
        self.fig = None
        self.axes = None
        self.init_figure()

        # Create subscriber based on source type
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        if src_cfg['type'] == 'sensor_msgs':
            self.create_subscription(Imu, self.imu_topic, self.imu_callback, qos_profile)
        else:
            self.create_subscription(RobotState, self.imu_topic, self.robot_state_callback, 10)

        # Create publisher for RViz markers
        self.marker_pub = self.create_publisher(MarkerArray, '/imu/orientation_marker', 10)

        # Create timer for periodic plotting
        self.plot_timer = self.create_timer(self.plot_interval, self.plot_callback)

        # Log initialization
        self.get_logger().info('=' * 50)
        self.get_logger().info('IMU Display Node initialized')
        self.get_logger().info(f'  IMU source: {self.imu_source} - {src_cfg["desc"]}')
        self.get_logger().info(f'  IMU topic: {self.imu_topic}')
        self.get_logger().info(f'  Frame ID: {self.frame_id}')
        self.get_logger().info(f'  History size: {self.history_size}')
        self.get_logger().info(f'  Plot interval: {self.plot_interval}s')
        self.get_logger().info(f'  Save directory: {self.save_dir}')
        self.get_logger().info('=' * 50)

    def init_figure(self):
        """Initialize the matplotlib figure and axes"""
        num_plots = sum([self.plot_orientation, self.plot_angular_velocity, self.plot_acceleration])

        if num_plots == 0:
            return

        self.fig, self.axes = plt.subplots(num_plots, 1, figsize=(12, 4 * num_plots), dpi=self.dpi)
        if num_plots == 1:
            self.axes = [self.axes]

        plt.tight_layout()

    def imu_callback(self, msg: Imu):
        """Process incoming sensor_msgs/Imu data (livox)"""
        self.total_messages += 1

        timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

        roll, pitch, yaw = self.quaternion_to_euler(
            msg.orientation.w, msg.orientation.x,
            msg.orientation.y, msg.orientation.z
        )
        roll_deg = roll * RAD_TO_DEG
        pitch_deg = pitch * RAD_TO_DEG
        yaw_deg = yaw * RAD_TO_DEG

        self._store_data(timestamp, roll_deg, pitch_deg, yaw_deg,
                         msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z,
                         msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z)

        self.last_orientation = msg.orientation
        self.publish_orientation_marker(roll_deg, pitch_deg, yaw_deg)

    def robot_state_callback(self, msg: RobotState):
        """Process xsens IMU data from /robot_state"""
        self.total_messages += 1
        timestamp = self.get_clock().now().nanoseconds * 1e-9

        imu = msg.imu
        self._store_data(timestamp, imu.roll, imu.pitch, imu.yaw,
                         imu.wx, imu.wy, imu.wz,
                         imu.ax, imu.ay, imu.az)

        self.last_orientation = None
        self.publish_orientation_marker(imu.roll, imu.pitch, imu.yaw)

    def _store_data(self, timestamp, roll_deg, pitch_deg, yaw_deg,
                    gyr_x, gyr_y, gyr_z, acc_x, acc_y, acc_z):
        self.timestamps.append(timestamp)
        self.roll_data.append(roll_deg)
        self.pitch_data.append(pitch_deg)
        self.yaw_data.append(yaw_deg)
        self.gyr_x_data.append(gyr_x)
        self.gyr_y_data.append(gyr_y)
        self.gyr_z_data.append(gyr_z)
        self.acc_x_data.append(acc_x)
        self.acc_y_data.append(acc_y)
        self.acc_z_data.append(acc_z)

    def quaternion_to_euler(self, w, x, y, z):
        """Convert quaternion to Euler angles (roll, pitch, yaw)"""
        # Roll (x-axis rotation)
        sinr_cosp = 2.0 * (w * x + y * z)
        cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
        roll = np.arctan2(sinr_cosp, cosr_cosp)

        # Pitch (y-axis rotation)
        sinp = 2.0 * (w * y - z * x)
        if abs(sinp) >= 1.0:
            pitch = np.copysign(np.pi / 2.0, sinp)
        else:
            pitch = np.arcsin(sinp)

        # Yaw (z-axis rotation)
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        yaw = np.arctan2(siny_cosp, cosy_cosp)

        return roll, pitch, yaw

    def _euler_to_quaternion(self, roll_deg, pitch_deg, yaw_deg):
        """Convert Euler angles (degrees) to quaternion for RViz markers"""
        r = math.radians(roll_deg)
        p = math.radians(pitch_deg)
        y = math.radians(yaw_deg)
        from geometry_msgs.msg import Quaternion
        q = Quaternion()
        q.w = (math.cos(r/2) * math.cos(p/2) * math.cos(y/2)
               + math.sin(r/2) * math.sin(p/2) * math.sin(y/2))
        q.x = (math.sin(r/2) * math.cos(p/2) * math.cos(y/2)
               - math.cos(r/2) * math.sin(p/2) * math.sin(y/2))
        q.y = (math.cos(r/2) * math.sin(p/2) * math.cos(y/2)
               + math.sin(r/2) * math.cos(p/2) * math.sin(y/2))
        q.z = (math.cos(r/2) * math.cos(p/2) * math.sin(y/2)
               - math.sin(r/2) * math.sin(p/2) * math.cos(y/2))
        return q

    def publish_orientation_marker(self, roll_deg: float, pitch_deg: float, yaw_deg: float):
        """Publish orientation marker for RViz visualization"""
        orientation = (self.last_orientation
                       if self.last_orientation is not None
                       else self._euler_to_quaternion(roll_deg, pitch_deg, yaw_deg))

        marker_array = MarkerArray()
        axis_length = 0.1
        axis_width = 0.01
        stamp = self.get_clock().now().to_msg()
        colors = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]

        for i, (r, g, b) in enumerate(colors):
            m = Marker()
            m.header.frame_id = self.frame_id
            m.header.stamp = stamp
            m.ns = 'imu_orientation'
            m.id = i
            m.type = Marker.ARROW
            m.action = Marker.ADD
            m.pose.orientation = orientation
            m.scale.x = axis_length
            m.scale.y = axis_width
            m.scale.z = axis_width
            m.color.r, m.color.g, m.color.b, m.color.a = r, g, b, 1.0
            marker_array.markers.append(m)

        text_marker = Marker()
        text_marker.header.frame_id = self.frame_id
        text_marker.header.stamp = stamp
        text_marker.ns = 'imu_text'
        text_marker.id = 0
        text_marker.type = Marker.TEXT_VIEW_FACING
        text_marker.action = Marker.ADD
        text_marker.pose.position.z = 0.15
        text_marker.pose.orientation.w = 1.0
        text_marker.scale.z = 0.05
        text_marker.color.r = text_marker.color.g = text_marker.color.b = text_marker.color.a = 1.0
        text_marker.text = f'[{self.imu_source}] R:{roll_deg:.1f}° P:{pitch_deg:.1f}° Y:{yaw_deg:.1f}°'
        marker_array.markers.append(text_marker)

        self.marker_pub.publish(marker_array)

    def plot_callback(self):
        """Generate and save plots periodically"""
        if len(self.timestamps) == 0:
            self.get_logger().info('No IMU data received yet...')
            return

        try:
            self.update_plot()
        except Exception as e:
            self.get_logger().error(f'Error generating plots: {e}')

    def update_plot(self):
        """Update the existing figure with new data and save"""
        if self.fig is None:
            return

        # Convert deques to numpy arrays
        timestamps = np.array(self.timestamps)
        # Normalize timestamps to start from 0
        if len(timestamps) > 0:
            timestamps = timestamps - timestamps[0]

        # Clear all axes
        for ax in self.axes:
            ax.clear()

        plot_idx = 0

        # Plot orientation
        if self.plot_orientation:
            ax = self.axes[plot_idx]
            ax.plot(timestamps, list(self.roll_data), 'r-', label='Roll', linewidth=1.5)
            ax.plot(timestamps, list(self.pitch_data), 'g-', label='Pitch', linewidth=1.5)
            ax.plot(timestamps, list(self.yaw_data), 'b-', label='Yaw', linewidth=1.5)
            ax.set_ylabel('Angle (deg)', fontsize=11)
            ax.set_title('Orientation (Euler Angles)', fontsize=12)
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(left=0)
            plot_idx += 1

        # Plot angular velocity
        if self.plot_angular_velocity:
            ax = self.axes[plot_idx]
            ax.plot(timestamps, list(self.gyr_x_data), 'r-', label='X', linewidth=1.5)
            ax.plot(timestamps, list(self.gyr_y_data), 'g-', label='Y', linewidth=1.5)
            ax.plot(timestamps, list(self.gyr_z_data), 'b-', label='Z', linewidth=1.5)
            ax.set_ylabel('Angular Velocity (rad/s)', fontsize=11)
            ax.set_title('Gyroscope', fontsize=12)
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(left=0)
            plot_idx += 1

        # Plot acceleration
        if self.plot_acceleration:
            ax = self.axes[plot_idx]
            ax.plot(timestamps, list(self.acc_x_data), 'r-', label='X', linewidth=1.5)
            ax.plot(timestamps, list(self.acc_y_data), 'g-', label='Y', linewidth=1.5)
            ax.plot(timestamps, list(self.acc_z_data), 'b-', label='Z', linewidth=1.5)
            ax.set_ylabel('Acceleration (m/s²)', fontsize=11)
            ax.set_xlabel('Time (s)', fontsize=11)
            ax.set_title('Accelerometer', fontsize=12)
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(left=0)
            plot_idx += 1

        # Update title with current time
        self.fig.suptitle(f'IMU Data - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                         fontsize=14, fontweight='bold')

        plt.tight_layout()

        # Save plot to single file
        filepath = os.path.join(self.save_dir, f'imu_plot.{self.save_format}')
        self.fig.savefig(filepath, dpi=self.dpi, bbox_inches='tight',
                        facecolor='white', edgecolor='none')

        self.get_logger().info(f'Plot updated: {filepath}')
        self.get_logger().info(f'Statistics: Messages={self.total_messages}, '
                               f'History samples={len(self.timestamps)}')


def main(args=None):
    rclpy.init(args=args)

    node = IMUDisplayNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Generate final plot before shutdown
        if len(node.timestamps) > 0:
            node.get_logger().info('Saving final plot before shutdown...')
            node.update_plot()
        # Close the figure
        if node.fig is not None:
            plt.close(node.fig)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()