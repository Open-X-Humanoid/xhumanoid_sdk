from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """
    启动灵巧手手势控制节点

    使用方法:
        # 默认控制右手
        ros2 launch brainco_hand_gesture_control_cpp hand_gesture_control.launch.py

        # 控制左手
        ros2 launch brainco_hand_gesture_control_cpp hand_gesture_control.launch.py hand_prefix:=left_hand
    """

    # 声明启动参数
    hand_prefix_arg = DeclareLaunchArgument(
        'hand_prefix',
        default_value='right_hand',
        description='手的前缀: right_hand 或 left_hand'
    )

    control_mode_arg = DeclareLaunchArgument(
        'control_mode',
        default_value='1',
        description='控制模式: 1=位置, 2=速度, 3=电流, 4=PWM, 5=位置+时间, 6=位置+速度'
    )

    # 创建节点
    hand_gesture_control_node = Node(
        package='brainco_hand_gesture_control_cpp',
        executable='hand_gesture_control_node',
        name='brainco_hand_gesture_control',
        output='screen',
        parameters=[{
            'hand_prefix': LaunchConfiguration('hand_prefix'),
            'control_mode': LaunchConfiguration('control_mode'),
        }],
    )

    return LaunchDescription([
        hand_prefix_arg,
        control_mode_arg,
        hand_gesture_control_node,
    ])