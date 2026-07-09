from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    colormap_arg = DeclareLaunchArgument(
        'colormap', default_value='2',
        description='Colormap for depth visualization (0=GRAY, 1=JET, 2=RAINBOW, 3=TURBO)'
    )
    max_depth_arg = DeclareLaunchArgument(
        'max_depth', default_value='5000.0',
        description='Maximum depth value in mm for visualization'
    )
    min_depth_arg = DeclareLaunchArgument(
        'min_depth', default_value='0.0',
        description='Minimum depth value in mm for visualization'
    )
    display_scale_arg = DeclareLaunchArgument(
        'display_scale', default_value='0.5',
        description='Display scale factor'
    )
    show_histogram_arg = DeclareLaunchArgument(
        'show_histogram', default_value='true',
        description='Show depth histogram'
    )
    show_statistics_arg = DeclareLaunchArgument(
        'show_statistics', default_value='true',
        description='Show depth statistics overlay'
    )
    enable_head_arg = DeclareLaunchArgument(
        'enable_head', default_value='true',
        description='Enable head camera display'
    )
    enable_waist_arg = DeclareLaunchArgument(
        'enable_waist', default_value='true',
        description='Enable waist camera display'
    )

    camera_display_node = Node(
        package='camera_display_cpp',
        executable='camera_display_node',
        name='camera_display_node',
        output='screen',
        parameters=[{
            'colormap': LaunchConfiguration('colormap'),
            'max_depth': LaunchConfiguration('max_depth'),
            'min_depth': LaunchConfiguration('min_depth'),
            'display_scale': LaunchConfiguration('display_scale'),
            'show_histogram': LaunchConfiguration('show_histogram'),
            'show_statistics': LaunchConfiguration('show_statistics'),
            'enable_head': LaunchConfiguration('enable_head'),
            'enable_waist': LaunchConfiguration('enable_waist'),
        }]
    )

    return LaunchDescription([
        colormap_arg,
        max_depth_arg,
        min_depth_arg,
        display_scale_arg,
        show_histogram_arg,
        show_statistics_arg,
        enable_head_arg,
        enable_waist_arg,
        camera_display_node,
    ])
