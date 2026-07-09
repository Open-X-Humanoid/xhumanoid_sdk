from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='single_joint_control_py',
            executable='cmd_publisher',
            name='cmd_publisher',
            output='screen',
            parameters=[],
            remappings=[],
        ),
    ])