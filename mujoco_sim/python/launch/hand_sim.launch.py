from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'full_stroke_s', default_value='0.8',
            description='Seconds to travel positions 1..1000 at default speed'),
        Node(
            package='xhumanoid_mujoco_sim',
            executable='hand_sim_node',
            name='brainco_hand_mujoco_sim',
            output='screen',
            parameters=[{
                'full_stroke_s': LaunchConfiguration('full_stroke_s'),
            }],
        ),
    ])
