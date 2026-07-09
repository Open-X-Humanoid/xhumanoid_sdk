cmake_minimum_required(VERSION 3.8)
project(speech_recognition_demo_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(lyre_msgs REQUIRED)

# Create the executable
add_executable(speech_recognition_node src/speech_recognition_node.cpp)
ament_target_dependencies(speech_recognition_node
  rclcpp
  lyre_msgs
)

# Install the executable
install(TARGETS speech_recognition_node
  DESTINATION lib/${PROJECT_NAME})

# Install launch files
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME})

ament_package()