import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Declare launch arguments
    default_audio_path_arg = DeclareLaunchArgument(
        'default_audio_path',
        default_value='/tmp/test.wav',
        description='Default audio file path to play'
    )

    auto_play_arg = DeclareLaunchArgument(
        'auto_play_on_start',
        default_value='false',
        description='Automatically play default audio on node start'
    )

    loop_playback_arg = DeclareLaunchArgument(
        'loop_playback',
        default_value='false',
        description='Enable loop playback mode'
    )

    loop_interval_arg = DeclareLaunchArgument(
        'loop_interval',
        default_value='1.0',
        description='Interval between loop playbacks in seconds'
    )

    # Speaker play demo node
    speaker_play_demo_node = Node(
        package='speaker_play_demo_cpp',
        executable='speaker_play_demo_node',
        name='speaker_play_demo_node',
        output='screen',
        parameters=[{
            'default_audio_path': LaunchConfiguration('default_audio_path'),
            'auto_play_on_start': LaunchConfiguration('auto_play_on_start'),
            'loop_playback': LaunchConfiguration('loop_playback'),
            'loop_interval': LaunchConfiguration('loop_interval'),
        }]
    )

    return LaunchDescription([
        default_audio_path_arg,
        auto_play_arg,
        loop_playback_arg,
        loop_interval_arg,
        speaker_play_demo_node,
    ])