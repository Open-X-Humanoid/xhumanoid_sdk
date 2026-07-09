cmake_minimum_required(VERSION 3.8)
project(single_joint_control_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(ros2_bridge_msgs REQUIRED)

# Create the executable
add_executable(cmd_publisher src/cmd_publisher.cpp)
ament_target_dependencies(cmd_publisher
  rclcpp
  ros2_bridge_msgs
)

# Install the executable
install(TARGETS cmd_publisher
  DESTINATION lib/${PROJECT_NAME})

# Install launch files
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME})

ament_package()
