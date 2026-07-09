import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Declare launch arguments
    sample_rate_arg = DeclareLaunchArgument(
        'sample_rate',
        default_value='16000',
        description='Audio sample rate in Hz'
    )

    channels_arg = DeclareLaunchArgument(
        'channels',
        default_value='1',
        description='Number of audio channels'
    )

    bits_per_sample_arg = DeclareLaunchArgument(
        'bits_per_sample',
        default_value='16',
        description='Bits per sample (16 or 24)'
    )

    output_dir_arg = DeclareLaunchArgument(
        'output_dir',
        default_value='/tmp',
        description='Output directory for recordings'
    )

    device_arg = DeclareLaunchArgument(
        'device',
        default_value='default',
        description='Audio device name (e.g., "default", "plughw:0,0")'
    )

    max_duration_arg = DeclareLaunchArgument(
        'max_duration',
        default_value='60',
        description='Maximum recording duration in seconds (0 = unlimited)'
    )

    # Mic record demo node
    mic_record_demo_node = Node(
        package='mic_record_demo_cpp',
        executable='mic_record_demo_node',
        name='mic_record_demo_node',
        output='screen',
        parameters=[{
            'sample_rate': LaunchConfiguration('sample_rate'),
            'channels': LaunchConfiguration('channels'),
            'bits_per_sample': LaunchConfiguration('bits_per_sample'),
            'output_dir': LaunchConfiguration('output_dir'),
            'device': LaunchConfiguration('device'),
            'max_duration': LaunchConfiguration('max_duration'),
        }]
    )

    return LaunchDescription([
        sample_rate_arg,
        channels_arg,
        bits_per_sample_arg,
        output_dir_arg,
        device_arg,
        max_duration_arg,
        mic_record_demo_node,
    ])