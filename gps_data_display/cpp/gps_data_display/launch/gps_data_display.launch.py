import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Declare launch arguments
    gps_topic_arg = DeclareLaunchArgument(
        'gps_topic',
        default_value='gps/fix',
        description='GPS data topic from GPS driver'
    )

    save_to_file_arg = DeclareLaunchArgument(
        'save_to_file',
        default_value='false',
        description='Save GPS data to log file'
    )

    log_file_arg = DeclareLaunchArgument(
        'log_file',
        default_value='/tmp/gps_data.txt',
        description='Path to log file for GPS data'
    )

    log_interval_arg = DeclareLaunchArgument(
        'log_interval',
        default_value='1.0',
        description='Interval for logging statistics (seconds)'
    )

    show_raw_data_arg = DeclareLaunchArgument(
        'show_raw_data',
        default_value='true',
        description='Show raw GPS data in console'
    )

    show_status_arg = DeclareLaunchArgument(
        'show_status',
        default_value='true',
        description='Show status summary in console'
    )

    # GPS data display node
    gps_data_display_node = Node(
        package='gps_data_display_cpp',
        executable='gps_data_display_node',
        name='gps_data_display_node',
        output='screen',
        parameters=[{
            'gps_topic': LaunchConfiguration('gps_topic'),
            'save_to_file': LaunchConfiguration('save_to_file'),
            'log_file': LaunchConfiguration('log_file'),
            'log_interval': LaunchConfiguration('log_interval'),
            'show_raw_data': LaunchConfiguration('show_raw_data'),
            'show_status': LaunchConfiguration('show_status'),
        }]
    )

    return LaunchDescription([
        gps_topic_arg,
        save_to_file_arg,
        log_file_arg,
        log_interval_arg,
        show_raw_data_arg,
        show_status_arg,
        gps_data_display_node,
    ])