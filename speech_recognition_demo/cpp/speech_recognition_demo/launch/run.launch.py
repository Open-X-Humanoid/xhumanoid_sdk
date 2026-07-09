from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='speech_recognition_demo_cpp',
            executable='speech_recognition_node',
            name='speech_recognition_demo',
            output='screen',
            parameters=[{
                'subscribe_iat': True,
                'subscribe_event': True,
                'subscribe_keyword': True,
            }],
            remappings=[],
        ),
    ])