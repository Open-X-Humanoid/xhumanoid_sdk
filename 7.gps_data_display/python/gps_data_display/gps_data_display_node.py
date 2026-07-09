#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPS Data Display Node (Python version)

This node subscribes to GPS data from the gps_ros2 driver and provides:
- Real-time GPS data display
- GPS status parsing and visualization
- Data logging to file
- Statistics calculation
"""

import os
from datetime import datetime
from typing import Optional

import rclpy
from rclpy.node import Node
from navigation_msgs.msg import GpsFix


class GPSDataDisplayNode(Node):
    """ROS2 Node for GPS data display"""

    # Status strings
    STATUS_STRINGS = {
        0: 'INVALID',
        1: 'SINGLE',
        2: 'DGPS/SBAS',
        4: 'RTK_FIXED',
        5: 'RTK_FLOAT',
    }

    # ANSI color codes
    STATUS_COLORS = {
        0: '\033[31m',  # Red - Invalid
        1: '\033[33m',  # Yellow - Single point
        2: '\033[36m',  # Cyan - DGPS
        4: '\033[32m',  # Green - RTK Fixed
        5: '\033[34m',  # Blue - RTK Float
    }
    RESET_COLOR = '\033[0m'

    def __init__(self):
        super().__init__('gps_data_display_node')

        # Statistics
        self.total_messages = 0
        self.valid_messages = 0

        # Position bounds
        self.min_lat = 90.0
        self.max_lat = -90.0
        self.min_lon = 180.0
        self.max_lon = -180.0
        self.max_speed = 0.0
        self.max_sats = 0

        # Log file
        self.log_file = None

        # Declare parameters
        self.declare_parameter('gps_topic', 'gps/fix')
        self.declare_parameter('save_to_file', False)
        self.declare_parameter('log_file', '/tmp/gps_data.txt')
        self.declare_parameter('log_interval', 1.0)
        self.declare_parameter('show_raw_data', True)
        self.declare_parameter('show_status', True)

        # Get parameters
        self.gps_topic = self.get_parameter('gps_topic').get_parameter_value().string_value
        self.save_to_file = self.get_parameter('save_to_file').get_parameter_value().bool_value
        self.log_file_path = self.get_parameter('log_file').get_parameter_value().string_value
        self.log_interval = self.get_parameter('log_interval').get_parameter_value().double_value
        self.show_raw_data = self.get_parameter('show_raw_data').get_parameter_value().bool_value
        self.show_status = self.get_parameter('show_status').get_parameter_value().bool_value

        # Create subscriber
        self.subscription = self.create_subscription(
            GpsFix,
            self.gps_topic,
            self.gps_callback,
            10
        )

        # Create statistics timer
        self.stats_timer = self.create_timer(
            self.log_interval,
            self.log_statistics
        )

        # Open log file if enabled
        if self.save_to_file:
            try:
                self.log_file = open(self.log_file_path, 'a')
                self.log_file.write(f'# GPS Data Log - Started at {self._get_current_time_string()}\n')
                self.log_file.write('# timestamp,lat,lon,alt,status,sats,hdop,speed,heading,tx_ms\n')
                self.get_logger().info(f'Log file opened: {self.log_file_path}')
            except Exception as e:
                self.get_logger().error(f'Failed to open log file: {e}')
                self.save_to_file = False

        self.get_logger().info('GPS Data Display Node initialized')
        self.get_logger().info(f'  GPS topic: {self.gps_topic}')
        self.get_logger().info(f'  Save to file: {self.save_to_file}')
        if self.save_to_file:
            self.get_logger().info(f'  Log file: {self.log_file_path}')

    def __del__(self):
        if self.log_file is not None:
            self.log_file.close()

    def gps_callback(self, msg):
        """GPS data callback"""
        self.total_messages += 1

        # Parse GPS status
        status_str = self._get_status_string(msg.status)
        is_valid = msg.status > 0

        if is_valid:
            self.valid_messages += 1

            # Update statistics
            self._update_statistics(msg)

            # Update position bounds
            if -90.0 <= msg.latitude <= 90.0:
                self.min_lat = min(self.min_lat, msg.latitude)
                self.max_lat = max(self.max_lat, msg.latitude)
            if -180.0 <= msg.longitude <= 180.0:
                self.min_lon = min(self.min_lon, msg.longitude)
                self.max_lon = max(self.max_lon, msg.longitude)

        # Display raw data
        if self.show_raw_data:
            self._display_gps_data(msg, status_str)

        # Show status summary
        if self.show_status:
            self._display_status_summary(msg, status_str)

        # Save to file if enabled
        if self.save_to_file and self.log_file is not None:
            self._save_to_log(msg)

    def _get_status_string(self, status):
        """Get status string from status code"""
        return self.STATUS_STRINGS.get(status, f'UNKNOWN({status})')

    def _get_status_color(self, status):
        """Get ANSI color code for status"""
        return self.STATUS_COLORS.get(status, self.RESET_COLOR)

    def _display_gps_data(self, msg, status_str):
        """Display GPS data"""
        color = self._get_status_color(msg.status)

        self.get_logger().info('')
        self.get_logger().info('========== GPS Data ==========')
        self.get_logger().info(f'  Timestamp: {self._get_current_time_string()}')
        self.get_logger().info(f'  Status: {color}{status_str}{self.RESET_COLOR}')
        self.get_logger().info('  Position:')
        lat_dir = 'N' if msg.latitude >= 0 else 'S'
        lon_dir = 'E' if msg.longitude >= 0 else 'W'
        self.get_logger().info(f'    Latitude:  {abs(msg.latitude):.6f}° {lat_dir}')
        self.get_logger().info(f'    Longitude: {abs(msg.longitude):.6f}° {lon_dir}')
        self.get_logger().info(f'    Altitude:  {msg.altitude:.3f} m')
        self.get_logger().info('  Quality:')
        self.get_logger().info(f'    Satellites: {msg.num_sats}')
        self.get_logger().info(f'    HDOP: {msg.hdop:.2f}')
        self.get_logger().info('  Motion:')
        self.get_logger().info(f'    Speed:   {msg.speed:.3f} m/s ({msg.speed * 3.6:.1f} km/h)')
        self.get_logger().info(f'    Heading: {msg.heading:.2f}°')
        self.get_logger().info('  Timing:')
        self.get_logger().info(f'    GPS-PPS diff: {msg.tx:.3f} ms')
        self.get_logger().info('==============================')

    def _display_status_summary(self, msg, status_str):
        """Display status summary"""
        color = self._get_status_color(msg.status)

        # Single line summary
        self.get_logger().info(
            f'{color}[GPS]{self.RESET_COLOR} {status_str} | '
            f'Sats:{msg.num_sats} | HDOP:{msg.hdop:.1f} | '
            f'{msg.latitude:.6f},{msg.longitude:.6f} | '
            f'Alt:{msg.altitude:.1f}m | Spd:{msg.speed * 3.6:.1f}km/h | Head:{msg.heading:.1f}°'
        )

    def _update_statistics(self, msg):
        """Update statistics"""
        if msg.speed > self.max_speed:
            self.max_speed = msg.speed
        if msg.num_sats > self.max_sats:
            self.max_sats = msg.num_sats

    def _save_to_log(self, msg):
        """Save GPS data to log file"""
        timestamp = datetime.now().timestamp()
        self.log_file.write(
            f'{timestamp:.6f},{msg.latitude},{msg.longitude},{msg.altitude},'
            f'{msg.status},{msg.num_sats},{msg.hdop},{msg.speed},'
            f'{msg.heading},{msg.tx}\n'
        )

    def log_statistics(self):
        """Log statistics"""
        if self.total_messages == 0:
            self.get_logger().info('No GPS data received yet...')
            return

        valid_rate = 100.0 * self.valid_messages / self.total_messages if self.total_messages > 0 else 0.0

        self.get_logger().info('')
        self.get_logger().info('======= GPS Statistics =======')
        self.get_logger().info(f'  Total messages: {self.total_messages}')
        self.get_logger().info(f'  Valid messages: {self.valid_messages} ({valid_rate:.1f}%)')
        self.get_logger().info('  Position bounds:')
        self.get_logger().info(f'    Latitude:  [{self.min_lat:.6f}, {self.max_lat:.6f}]')
        self.get_logger().info(f'    Longitude: [{self.min_lon:.6f}, {self.max_lon:.6f}]')
        self.get_logger().info(f'  Max speed: {self.max_speed:.3f} m/s ({self.max_speed * 3.6:.1f} km/h)')
        self.get_logger().info(f'  Max satellites: {self.max_sats}')
        self.get_logger().info('==============================')

    def _get_current_time_string(self):
        """Get current time string"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]


def main(args=None):
    rclpy.init(args=args)
    node = GPSDataDisplayNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()