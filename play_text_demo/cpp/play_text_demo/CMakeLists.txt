cmake_minimum_required(VERSION 3.8)
project(play_text_demo_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(interaction_msgs REQUIRED)

# Create the executable
add_executable(play_text_node src/play_text_node.cpp)
ament_target_dependencies(play_text_node
  rclcpp
  interaction_msgs
)

# Install the executable
install(TARGETS play_text_node
  DESTINATION lib/${PROJECT_NAME})

# Install launch files
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME})

ament_package()