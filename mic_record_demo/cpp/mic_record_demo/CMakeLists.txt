cmake_minimum_required(VERSION 3.8)
project(mic_record_demo_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(lyre_msgs REQUIRED)

# Create the mic record demo node executable
add_executable(mic_record_demo_node src/mic_record_demo_node.cpp)

ament_target_dependencies(mic_record_demo_node
  rclcpp
  std_msgs
  std_srvs
  lyre_msgs
)

# Install the executable
install(TARGETS mic_record_demo_node
  DESTINATION lib/${PROJECT_NAME})

# Install launch files
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME})

ament_package()