cmake_minimum_required(VERSION 3.8)
project(camera_6v_display_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(OpenCV REQUIRED)

# Create the camera 6v display node executable
add_executable(camera_6v_display_node src/camera_6v_display_node.cpp)

ament_target_dependencies(camera_6v_display_node
  rclcpp
  sensor_msgs
  cv_bridge
)

# Include directories
target_include_directories(camera_6v_display_node PUBLIC
  ${OpenCV_INCLUDE_DIRS}
  ${cv_bridge_INCLUDE_DIRS}
)

# Link libraries
target_link_libraries(camera_6v_display_node
  ${OpenCV_LIBRARIES}
  ${cv_bridge_LIBRARIES}
)

# Install the executable
install(TARGETS camera_6v_display_node
  DESTINATION lib/${PROJECT_NAME})

# Install launch files
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME})

ament_package()