cmake_minimum_required(VERSION 3.8)
project(speaker_play_demo_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(interaction_msgs REQUIRED)

# Create the speaker play demo node executable
add_executable(speaker_play_demo_node src/speaker_play_demo_node.cpp)

ament_target_dependencies(speaker_play_demo_node
  rclcpp
  interaction_msgs
)

# Install the executable
install(TARGETS speaker_play_demo_node
  DESTINATION lib/${PROJECT_NAME})

# Install launch files
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME})

ament_package()