from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    enable_left_arg = DeclareLaunchArgument(
        'enable_left', default_value='true',
        description='Enable left hand touch status display'
    )
    enable_right_arg = DeclareLaunchArgument(
        'enable_right', default_value='true',
        description='Enable right hand touch status display'
    )
    print_interval_arg = DeclareLaunchArgument(
        'print_interval', default_value='1.0',
        description='Print interval in seconds'
    )

    touch_display_node = Node(
        package='brainco_hand_touch_display_py',
        executable='touch_display_node',
        name='touch_display_node',
        output='screen',
        parameters=[{
            'enable_left': LaunchConfiguration('enable_left'),
            'enable_right': LaunchConfiguration('enable_right'),
            'print_interval': LaunchConfiguration('print_interval'),
        }]
    )

    return LaunchDescription([
        enable_left_arg,
        enable_right_arg,
        print_interval_arg,
        touch_display_node,
    ])
