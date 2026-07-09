import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Get package directory
    pkg_dir = get_package_share_directory('point_cloud_display_py')
    rviz_config_path = os.path.join(pkg_dir, 'rviz', 'point_cloud.rviz')

    # Declare launch arguments
    input_topic_arg = DeclareLaunchArgument(
        'input_topic',
        default_value='/livox/lidar',
        description='Input point cloud topic from Livox driver'
    )

    output_topic_arg = DeclareLaunchArgument(
        'output_topic',
        default_value='/point_cloud/filtered',
        description='Output point cloud topic for filtered data'
    )

    frame_id_arg = DeclareLaunchArgument(
        'frame_id',
        default_value='livox_frame',
        description='Frame ID for point cloud'
    )

    filter_enable_arg = DeclareLaunchArgument(
        'filter_enable',
        default_value='false',
        description='Enable voxel grid filtering'
    )

    voxel_leaf_size_arg = DeclareLaunchArgument(
        'voxel_leaf_size',
        default_value='0.05',
        description='Voxel grid leaf size in meters'
    )

    sor_enable_arg = DeclareLaunchArgument(
        'sor_enable',
        default_value='false',
        description='Enable statistical outlier removal'
    )

    sor_mean_k_arg = DeclareLaunchArgument(
        'sor_mean_k',
        default_value='50',
        description='Number of neighbors for statistical outlier removal'
    )

    sor_stddev_arg = DeclareLaunchArgument(
        'sor_stddev_mul_thresh',
        default_value='1.0',
        description='Standard deviation multiplier for SOR'
    )

    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value=rviz_config_path,
        description='Path to RViz config file'
    )

    # Point cloud display node
    point_cloud_display_node = Node(
        package='point_cloud_display_py',
        executable='point_cloud_display_node',
        name='point_cloud_display_node',
        output='screen',
        parameters=[{
            'input_topic': LaunchConfiguration('input_topic'),
            'output_topic': LaunchConfiguration('output_topic'),
            'frame_id': LaunchConfiguration('frame_id'),
            'filter_enable': LaunchConfiguration('filter_enable'),
            'voxel_leaf_size': LaunchConfiguration('voxel_leaf_size'),
            'sor_enable': LaunchConfiguration('sor_enable'),
            'sor_mean_k': LaunchConfiguration('sor_mean_k'),
            'sor_stddev_mul_thresh': LaunchConfiguration('sor_stddev_mul_thresh'),
        }]
    )

    # RViz node
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', LaunchConfiguration('rviz_config')],
    )

    return LaunchDescription([
        input_topic_arg,
        output_topic_arg,
        frame_id_arg,
        filter_enable_arg,
        voxel_leaf_size_arg,
        sor_enable_arg,
        sor_mean_k_arg,
        sor_stddev_arg,
        rviz_config_arg,
        point_cloud_display_node,
        rviz_node,
    ])