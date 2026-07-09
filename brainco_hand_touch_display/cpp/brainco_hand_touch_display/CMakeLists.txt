cmake_minimum_required(VERSION 3.8)
project(brainco_hand_touch_display_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(brainco_hand_msgs REQUIRED)

add_executable(touch_display_node src/touch_display_node.cpp)

ament_target_dependencies(touch_display_node
  rclcpp
  brainco_hand_msgs
)

install(TARGETS touch_display_node
  DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}/)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
