cmake_minimum_required(VERSION 3.8)
project(camera_display_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(OpenCV REQUIRED)

add_executable(camera_display_node src/camera_display_node.cpp)

ament_target_dependencies(camera_display_node
  rclcpp
  sensor_msgs
)

target_include_directories(camera_display_node PUBLIC
  ${OpenCV_INCLUDE_DIRS}
)

target_link_libraries(camera_display_node
  ${OpenCV_LIBRARIES}
)

install(TARGETS camera_display_node
  DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME})

ament_package()
