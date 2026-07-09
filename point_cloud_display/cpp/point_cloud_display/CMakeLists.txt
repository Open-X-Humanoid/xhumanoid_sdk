cmake_minimum_required(VERSION 3.8)
project(point_cloud_display_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(PCL REQUIRED)

# Create the point cloud display node executable
add_executable(point_cloud_display_node src/point_cloud_display_node.cpp)
ament_target_dependencies(point_cloud_display_node
  rclcpp
  sensor_msgs
  pcl_conversions
)

# Include PCL directories
target_include_directories(point_cloud_display_node PUBLIC
  ${PCL_INCLUDE_DIRS}
)

# Link PCL libraries
target_link_libraries(point_cloud_display_node
  ${PCL_LIBRARIES}
)

# Install the executable
install(TARGETS point_cloud_display_node
  DESTINATION lib/${PROJECT_NAME})

# Install launch files
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME})

# Install rviz config files
install(DIRECTORY rviz
  DESTINATION share/${PROJECT_NAME})

ament_package()