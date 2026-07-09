cmake_minimum_required(VERSION 3.8)
project(imu_display_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(ament_index_cpp REQUIRED)
find_package(ros2_bridge_msgs REQUIRED)

# C++ Node
add_executable(imu_display_node_cpp src/imu_display_node.cpp)
ament_target_dependencies(imu_display_node_cpp
  rclcpp
  sensor_msgs
  std_msgs
  visualization_msgs
  ament_index_cpp
  ros2_bridge_msgs
)

# Install the C++ executable
install(TARGETS imu_display_node_cpp
  DESTINATION lib/${PROJECT_NAME})

# Install launch files
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME})

# Install rviz config files
install(DIRECTORY rviz
  DESTINATION share/${PROJECT_NAME})

# Install scripts
install(DIRECTORY scripts
  DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()