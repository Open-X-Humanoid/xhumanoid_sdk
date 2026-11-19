from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import EnvironmentVariable, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'model_path',
            default_value=EnvironmentVariable('XHUMANOID_SIM_MODEL',
                                              default_value=''),
            description='Path to the tiangong3 MJCF (see scripts/fetch_model.sh)'),
        DeclareLaunchArgument(
            'with_hands', default_value='true',
            description='Attach a simulated dexterous hand to each wrist'),
        DeclareLaunchArgument(
            'viewer_port',
            default_value=EnvironmentVariable('XHUMANOID_SIM_VIEWER_PORT',
                                              default_value='0'),
            description='Port of the browser viewer, 0 to disable'),
        Node(
            package='xhumanoid_mujoco_sim',
            executable='sim_node',
            name='xhumanoid_mujoco_sim',
            output='screen',
            parameters=[{
                'model_path': LaunchConfiguration('model_path'),
                'with_hands': LaunchConfiguration('with_hands'),
                'viewer_port': LaunchConfiguration('viewer_port'),
            }],
        ),
    ])
