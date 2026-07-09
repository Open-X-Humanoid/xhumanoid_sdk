from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='play_text_demo_cpp',
            executable='play_text_node',
            name='play_text_demo',
            output='screen',
            parameters=[{
                'text': '你好，我是机器人，很高兴认识你。',
                'force': True,
            }],
            remappings=[],
        ),
    ])