import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_dir = get_package_share_directory('imu_display_py')

    imu_source_arg = DeclareLaunchArgument(
        'imu_source',
        default_value='livox',
        description='IMU source: livox, xsens'
    )

    imu_topic_arg = DeclareLaunchArgument(
        'imu_topic',
        default_value='',
        description='Override IMU topic (leave empty to use default for selected source)'
    )

    frame_id_arg = DeclareLaunchArgument(
        'frame_id',
        default_value='base_link',
        description='Frame ID for IMU data'
    )

    history_size_arg = DeclareLaunchArgument(
        'history_size',
        default_value='500',
        description='Number of samples to keep in history'
    )

    plot_interval_arg = DeclareLaunchArgument(
        'plot_interval',
        default_value='2.0',
        description='Interval between plot updates in seconds'
    )

    save_format_arg = DeclareLaunchArgument(
        'save_format',
        default_value='png',
        description='Image format for saving plots (png, pdf, svg)'
    )

    dpi_arg = DeclareLaunchArgument(
        'dpi',
        default_value='150',
        description='DPI for saved images'
    )

    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value=os.path.join(pkg_dir, 'rviz', 'imu_display.rviz'),
        description='Path to RViz config file'
    )

    imu_display_node = Node(
        package='imu_display_py',
        executable='imu_display_node',
        name='imu_display_node',
        output='screen',
        parameters=[{
            'imu_source': LaunchConfiguration('imu_source'),
            'imu_topic': LaunchConfiguration('imu_topic'),
            'frame_id': LaunchConfiguration('frame_id'),
            'history_size': LaunchConfiguration('history_size'),
            'plot_interval': LaunchConfiguration('plot_interval'),
            'save_format': LaunchConfiguration('save_format'),
            'dpi': LaunchConfiguration('dpi'),
        }],
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', LaunchConfiguration('rviz_config')],
        output='screen',
    )

    return LaunchDescription([
        imu_source_arg,
        imu_topic_arg,
        frame_id_arg,
        history_size_arg,
        plot_interval_arg,
        save_format_arg,
        dpi_arg,
        rviz_config_arg,
        imu_display_node,
        rviz_node,
    ])