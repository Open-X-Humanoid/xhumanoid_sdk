#include <cmath>

#include "rclcpp/rclcpp.hpp"
#include "ros2_bridge_msgs/msg/arm_ctrl.hpp"
#include "ros2_bridge_msgs/msg/motor_ctrl.hpp"
#include "ros2_bridge_msgs/msg/robot_state.hpp"

class CmdPublisher : public rclcpp::Node {
 public:
  CmdPublisher()
      : Node("cmd_publisher"), current_pos_(0.0), target_pos_(0.0), stage_(0) {
    publisher_ =
        this->create_publisher<ros2_bridge_msgs::msg::ArmCtrl>("/arm/cmd", 10);

    status_sub_ =
        this->create_subscription<ros2_bridge_msgs::msg::RobotState>(
            "/robot_state", 10,
            std::bind(&CmdPublisher::status_callback, this,
                      std::placeholders::_1));

    timer_ = this->create_wall_timer(
        std::chrono::milliseconds(20),
        std::bind(&CmdPublisher::control_callback, this));

    RCLCPP_INFO(this->get_logger(), "CmdPublisher initialized");
  }

 private:
  static constexpr uint16_t kJointId = 21;
  static constexpr double kPosTarget = -1.588;
  static constexpr double kPosThresholdDeg = 5.0;

  // Position mode parameters
  static constexpr uint8_t kPosMode = 0;
  static constexpr double kPosSpd = 0.3;
  static constexpr double kPosCur = 10.0;

  // Force-position hybrid mode parameters
  static constexpr uint8_t kHybridMode = 1;
  static constexpr double kHybridKp = 50.0;
  static constexpr double kHybridKd = 2.0;
  static constexpr double kHybridSpd = 0.0;
  static constexpr double kHybridTor = 0.0;

  void status_callback(
      const ros2_bridge_msgs::msg::RobotState::SharedPtr msg) {
    for (const auto& motor_status : msg->arm.status) {
      if (motor_status.name == kJointId) {
        current_pos_ = motor_status.pos;
      }
    }
  }

  double pos_diff_deg(double target) const {
    return std::abs(current_pos_ - target) * 180.0 / M_PI;
  }

  void control_callback() {
    switch (stage_) {
      case 0:
        run_position_stage(kPosTarget, 1, "Position mode: raise arm");
        break;
      case 1:
        run_position_stage(0.0, 2, "Position mode: lower arm");
        break;
      case 2:
        run_hybrid_stage(kPosTarget, 3, "Hybrid mode: raise arm");
        break;
      case 3:
        run_hybrid_stage(0.0, 4, "Hybrid mode: lower arm");
        break;
      default:
        break;
    }
  }

  void run_position_stage(double target, int next_stage, const char* label) {
    target_pos_ = target;
    double diff = pos_diff_deg(target);
    RCLCPP_INFO(this->get_logger(),
                "[Stage %d] %s: current=%.4f, target=%.4f, diff=%.2f deg",
                stage_, label, current_pos_, target, diff);

    if (diff < kPosThresholdDeg) {
      RCLCPP_INFO(this->get_logger(), "Stage %d completed", stage_);
      stage_ = next_stage;
      if (next_stage == 2) {
        RCLCPP_INFO(this->get_logger(),
                    "--- Switching to force-position hybrid mode ---");
      }
    }
    publish_position_cmd(target);
  }

  void run_hybrid_stage(double target, int next_stage, const char* label) {
    target_pos_ = target;
    double diff = pos_diff_deg(target);
    RCLCPP_INFO(this->get_logger(),
                "[Stage %d] %s: current=%.4f, target=%.4f, diff=%.2f deg",
                stage_, label, current_pos_, target, diff);

    if (diff < kPosThresholdDeg) {
      RCLCPP_INFO(this->get_logger(), "Stage %d completed", stage_);
      stage_ = next_stage;
      if (next_stage == 4) {
        RCLCPP_INFO(this->get_logger(), "All motion stages completed!");
        timer_->cancel();
      }
    }
    publish_hybrid_cmd(target);
  }

  void publish_position_cmd(double pos) {
    ros2_bridge_msgs::msg::ArmCtrl msg;
    msg.header.stamp = this->now();
    msg.header.frame_id = "arm";
    msg.mode = kPosMode;
    msg.label = 0;

    ros2_bridge_msgs::msg::MotorCtrl ctrl;
    ctrl.name = kJointId;
    ctrl.pos = pos;
    ctrl.spd = kPosSpd;
    ctrl.cur = kPosCur;
    msg.ctrl.push_back(ctrl);

    publisher_->publish(msg);
  }

  void publish_hybrid_cmd(double pos) {
    ros2_bridge_msgs::msg::ArmCtrl msg;
    msg.header.stamp = this->now();
    msg.header.frame_id = "arm";
    msg.mode = kHybridMode;
    msg.label = 0;

    ros2_bridge_msgs::msg::MotorCtrl ctrl;
    ctrl.name = kJointId;
    ctrl.kp = kHybridKp;
    ctrl.kd = kHybridKd;
    ctrl.pos = pos;
    ctrl.spd = kHybridSpd;
    ctrl.tor = kHybridTor;
    msg.ctrl.push_back(ctrl);

    publisher_->publish(msg);
  }

  rclcpp::Publisher<ros2_bridge_msgs::msg::ArmCtrl>::SharedPtr publisher_;
  rclcpp::Subscription<ros2_bridge_msgs::msg::RobotState>::SharedPtr
      status_sub_;
  rclcpp::TimerBase::SharedPtr timer_;

  double current_pos_;
  double target_pos_;
  int stage_;
};

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<CmdPublisher>());
  rclcpp::shutdown();
  return 0;
}
