cmake_minimum_required(VERSION 3.8)
project(gps_data_display_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(navigation_msgs REQUIRED)

# Create the GPS data display node executable
add_executable(gps_data_display_node src/gps_data_display_node.cpp)

ament_target_dependencies(gps_data_display_node
  rclcpp
  navigation_msgs
)

# Install the executable
install(TARGETS gps_data_display_node
  DESTINATION lib/${PROJECT_NAME})

# Install launch files
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME})

ament_package()