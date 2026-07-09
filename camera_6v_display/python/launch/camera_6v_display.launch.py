import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Declare launch arguments
    display_width_arg = DeclareLaunchArgument(
        'display_width',
        default_value='320',
        description='Width of each camera display in pixels'
    )

    display_height_arg = DeclareLaunchArgument(
        'display_height',
        default_value='240',
        description='Height of each camera display in pixels'
    )

    use_compressed_arg = DeclareLaunchArgument(
        'use_compressed',
        default_value='false',
        description='Use compressed image topics instead of raw images'
    )

    show_fps_arg = DeclareLaunchArgument(
        'show_fps',
        default_value='true',
        description='Show FPS on each camera display'
    )

    window_name_arg = DeclareLaunchArgument(
        'window_name',
        default_value='6V Camera Display',
        description='Name of the OpenCV display window'
    )

    topic_prefix_arg = DeclareLaunchArgument(
        'topic_prefix',
        default_value='camera',
        description='Prefix for camera topics (e.g., "camera" for camera0/image_raw)'
    )

    # Camera 6v display node
    camera_6v_display_node = Node(
        package='camera_6v_display_py',
        executable='camera_6v_display_node',
        name='camera_6v_display_node',
        output='screen',
        parameters=[{
            'display_width': LaunchConfiguration('display_width'),
            'display_height': LaunchConfiguration('display_height'),
            'use_compressed': LaunchConfiguration('use_compressed'),
            'show_fps': LaunchConfiguration('show_fps'),
            'window_name': LaunchConfiguration('window_name'),
            'topic_prefix': LaunchConfiguration('topic_prefix'),
        }]
    )

    return LaunchDescription([
        display_width_arg,
        display_height_arg,
        use_compressed_arg,
        show_fps_arg,
        window_name_arg,
        topic_prefix_arg,
        camera_6v_display_node,
    ])