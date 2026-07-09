/**
 * @file touch_display_node.cpp
 * @brief Real-time printing of tactile feedback status from BrainCo dexterous hands
 *
 * Subscribes to /left_hand/touch_status and /right_hand/touch_status topics,
 * printing formatted touch sensor data at a configurable interval.
 */

#include <cstdio>
#include <string>
#include <sstream>
#include <iomanip>

#include "rclcpp/rclcpp.hpp"
#include "brainco_hand_msgs/msg/touch_status.hpp"

static const char* FINGER_NAMES[] = {"Thumb", "Index", "Middle", "Ring", "Little"};

class TouchDisplayNode : public rclcpp::Node {
 public:
  TouchDisplayNode() : Node("touch_display_node") {
    this->declare_parameter("enable_left", true);
    this->declare_parameter("enable_right", true);
    this->declare_parameter("print_interval", 1.0);

    bool enable_left = this->get_parameter("enable_left").as_bool();
    bool enable_right = this->get_parameter("enable_right").as_bool();
    double print_interval = this->get_parameter("print_interval").as_double();

    if (enable_left) {
      left_sub_ = this->create_subscription<brainco_hand_msgs::msg::TouchStatus>(
          "/left_hand/touch_status", 10,
          [this](const brainco_hand_msgs::msg::TouchStatus::SharedPtr msg) {
            left_touch_ = msg;
          });
      enable_left_ = true;
    }

    if (enable_right) {
      right_sub_ = this->create_subscription<brainco_hand_msgs::msg::TouchStatus>(
          "/right_hand/touch_status", 10,
          [this](const brainco_hand_msgs::msg::TouchStatus::SharedPtr msg) {
            right_touch_ = msg;
          });
      enable_right_ = true;
    }

    timer_ = this->create_wall_timer(
        std::chrono::milliseconds(static_cast<int>(print_interval * 1000)),
        std::bind(&TouchDisplayNode::print_callback, this));

    RCLCPP_INFO(this->get_logger(), "Touch Display Node initialized");
    if (enable_left_)
      RCLCPP_INFO(this->get_logger(), "  Subscribed: /left_hand/touch_status");
    if (enable_right_)
      RCLCPP_INFO(this->get_logger(), "  Subscribed: /right_hand/touch_status");
    RCLCPP_INFO(this->get_logger(), "  Print interval: %.1fs", print_interval);
  }

 private:
  void print_callback() {
    std::ostringstream oss;
    oss << "\n" << std::string(70, '=') << "\n";

    if (enable_left_)
      format_hand(oss, "Left Hand", left_touch_);
    if (enable_right_)
      format_hand(oss, "Right Hand", right_touch_);

    oss << std::string(70, '=');
    RCLCPP_INFO(this->get_logger(), "%s", oss.str().c_str());
  }

  void format_hand(std::ostringstream& oss, const char* title,
                   const brainco_hand_msgs::msg::TouchStatus::SharedPtr& msg) {
    if (!msg) {
      oss << "  [" << title << "] No data received\n";
      return;
    }

    oss << "  [" << title << "]\n";
    oss << "  " << std::left << std::setw(8) << "Finger" << " | "
        << std::right << std::setw(10) << "Normal(N)" << " | "
        << std::setw(14) << "Tangential(N)" << " | "
        << std::setw(13) << "Direction(°)" << " | "
        << std::setw(10) << "Proximity" << " | "
        << std::setw(6) << "Status" << "\n";
    oss << "  " << std::string(68, '-') << "\n";

    for (int i = 0; i < 5 && i < static_cast<int>(msg->data.size()); i++) {
      const auto& item = msg->data[i];

      char normal_str[16], tangential_str[16], dir_str[16],
           prox_str[16], status_str[16];

      std::snprintf(normal_str, sizeof(normal_str), "%.2f",
                    item.normal_force1 / 100.0);
      std::snprintf(tangential_str, sizeof(tangential_str), "%.2f",
                    item.tangential_force1 / 100.0);

      if (item.tangential_direction1 == 65535)
        std::snprintf(dir_str, sizeof(dir_str), "N/A");
      else
        std::snprintf(dir_str, sizeof(dir_str), "%u",
                      item.tangential_direction1);

      std::snprintf(prox_str, sizeof(prox_str), "%u", item.self_proximity1);

      uint8_t status_low = item.status & 0xFF;
      if (status_low == 0)
        std::snprintf(status_str, sizeof(status_str), "OK");
      else if (status_low == 1)
        std::snprintf(status_str, sizeof(status_str), "ERR");
      else if (status_low == 2)
        std::snprintf(status_str, sizeof(status_str), "COMM");
      else
        std::snprintf(status_str, sizeof(status_str), "0x%04X", item.status);

      oss << "  " << std::left << std::setw(8) << FINGER_NAMES[i] << " | "
          << std::right << std::setw(10) << normal_str << " | "
          << std::setw(14) << tangential_str << " | "
          << std::setw(13) << dir_str << " | "
          << std::setw(10) << prox_str << " | "
          << std::setw(6) << status_str << "\n";
    }
  }

  rclcpp::Subscription<brainco_hand_msgs::msg::TouchStatus>::SharedPtr left_sub_;
  rclcpp::Subscription<brainco_hand_msgs::msg::TouchStatus>::SharedPtr right_sub_;
  rclcpp::TimerBase::SharedPtr timer_;

  brainco_hand_msgs::msg::TouchStatus::SharedPtr left_touch_;
  brainco_hand_msgs::msg::TouchStatus::SharedPtr right_touch_;

  bool enable_left_ = false;
  bool enable_right_ = false;
};

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<TouchDisplayNode>());
  rclcpp::shutdown();
  return 0;
}
