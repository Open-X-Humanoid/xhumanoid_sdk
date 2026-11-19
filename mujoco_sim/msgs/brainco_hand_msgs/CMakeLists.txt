cmake_minimum_required(VERSION 3.8)
project(brainco_hand_msgs)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/SetMotorMulti.msg"
  "msg/MotorStatus.msg"
  "msg/TouchStatusItem.msg"
  "msg/TouchStatus.msg"
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
