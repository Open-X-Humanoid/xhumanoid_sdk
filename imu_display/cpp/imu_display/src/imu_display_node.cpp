/**
 * @file imu_display_node.cpp
 * @brief ROS2 node for displaying IMU data with multi-source support
 *
 * Supports two IMU sources on the Thor platform:
 * - livox:  /livox/imu, 200Hz
 * - xsens:  /robot_state (ImuStatus field), body IMU
 */

#include <memory>
#include <string>
#include <vector>
#include <deque>
#include <cmath>
#include <algorithm>
#include <iomanip>
#include <fstream>
#include <sstream>
#include <cstdlib>
#include <map>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "std_msgs/msg/string.hpp"
#include "visualization_msgs/msg/marker.hpp"
#include "visualization_msgs/msg/marker_array.hpp"
#include "ament_index_cpp/get_package_share_directory.hpp"
#include "ros2_bridge_msgs/msg/robot_state.hpp"

#define RAD_TO_DEG (57.2957795130823)
#define GRAVITY (9.8)

struct IMUDataPoint {
  double timestamp;
  double roll, pitch, yaw;
  double gyr_x, gyr_y, gyr_z;
  double acc_x, acc_y, acc_z;
};

struct IMUSourceConfig {
  std::string topic;
  std::string type;   // "sensor_msgs" or "robot_state"
  std::string desc;
};

static const std::map<std::string, IMUSourceConfig> IMU_SOURCE_MAP = {
    {"livox",  {"/livox/imu",   "sensor_msgs", "Livox雷达IMU"}},
    {"xsens",  {"/robot_state", "robot_state",  "Xsens体内IMU（通过/robot_state）"}},
};

void quaternionToEuler(double w, double x, double y, double z,
                       double& roll, double& pitch, double& yaw) {
  double sinr_cosp = 2.0 * (w * x + y * z);
  double cosr_cosp = 1.0 - 2.0 * (x * x + y * y);
  roll = std::atan2(sinr_cosp, cosr_cosp);

  double sinp = 2.0 * (w * y - z * x);
  if (std::abs(sinp) >= 1.0) {
    pitch = std::copysign(M_PI / 2.0, sinp);
  } else {
    pitch = std::asin(sinp);
  }

  double siny_cosp = 2.0 * (w * z + x * y);
  double cosy_cosp = 1.0 - 2.0 * (y * y + z * z);
  yaw = std::atan2(siny_cosp, cosy_cosp);
}

class IMUDisplayNode : public rclcpp::Node {
 public:
  IMUDisplayNode()
      : Node("imu_display_node"),
        total_messages_(0),
        history_size_(200),
        last_print_time_(0),
        plot_interval_(2.0),
        save_plot_(false),
        dpi_(150) {
    this->declare_parameter("imu_source", "livox");
    this->declare_parameter("imu_topic", "");
    this->declare_parameter("frame_id", "base_link");
    this->declare_parameter("history_size", 200);
    this->declare_parameter("print_interval", 1.0);
    this->declare_parameter("plot_interval", 2.0);
    this->declare_parameter("save_plot", true);
    this->declare_parameter("save_dir", "/tmp/imu_plots");
    this->declare_parameter("save_format", "png");
    this->declare_parameter("dpi", 150);

    imu_source_ = this->get_parameter("imu_source").as_string();
    std::string imu_topic_override = this->get_parameter("imu_topic").as_string();
    frame_id_ = this->get_parameter("frame_id").as_string();
    history_size_ = static_cast<size_t>(this->get_parameter("history_size").as_int());
    double print_interval = this->get_parameter("print_interval").as_double();
    plot_interval_ = this->get_parameter("plot_interval").as_double();
    save_plot_ = this->get_parameter("save_plot").as_bool();
    save_dir_ = this->get_parameter("save_dir").as_string();
    save_format_ = this->get_parameter("save_format").as_string();
    dpi_ = this->get_parameter("dpi").as_int();

    auto it = IMU_SOURCE_MAP.find(imu_source_);
    if (it == IMU_SOURCE_MAP.end()) {
      RCLCPP_ERROR(this->get_logger(),
                   "Unknown imu_source: '%s'. Supported: livox, xsens. Defaulting to livox.",
                   imu_source_.c_str());
      imu_source_ = "livox";
      it = IMU_SOURCE_MAP.find(imu_source_);
    }
    const auto& src_cfg = it->second;
    imu_topic_ = imu_topic_override.empty() ? src_cfg.topic : imu_topic_override;

    if (save_plot_) {
      std::string mkdir_cmd = "mkdir -p " + save_dir_;
      system(mkdir_cmd.c_str());
    }

    if (src_cfg.type == "sensor_msgs") {
      imu_subscription_ = this->create_subscription<sensor_msgs::msg::Imu>(
          imu_topic_, rclcpp::SensorDataQoS(),
          std::bind(&IMUDisplayNode::imu_callback, this, std::placeholders::_1));
    } else {
      robot_state_subscription_ = this->create_subscription<ros2_bridge_msgs::msg::RobotState>(
          imu_topic_, 10,
          std::bind(&IMUDisplayNode::robot_state_callback, this, std::placeholders::_1));
    }

    orientation_marker_pub_ = this->create_publisher<visualization_msgs::msg::MarkerArray>(
        "/imu/orientation_marker", rclcpp::QoS(10));

    stats_timer_ = this->create_wall_timer(
        std::chrono::duration<double>(print_interval),
        std::bind(&IMUDisplayNode::log_statistics, this));

    if (save_plot_) {
      plot_timer_ = this->create_wall_timer(
          std::chrono::duration<double>(plot_interval_),
          std::bind(&IMUDisplayNode::generate_plot, this));
    }

    RCLCPP_INFO(this->get_logger(), "IMU Display Node initialized");
    RCLCPP_INFO(this->get_logger(), "  IMU source: %s - %s", imu_source_.c_str(), src_cfg.desc.c_str());
    RCLCPP_INFO(this->get_logger(), "  Subscribing to: %s", imu_topic_.c_str());
    RCLCPP_INFO(this->get_logger(), "  Frame ID: %s", frame_id_.c_str());
    RCLCPP_INFO(this->get_logger(), "  History size: %zu", history_size_);
    RCLCPP_INFO(this->get_logger(), "  Save plot: %s", save_plot_ ? "true" : "false");
    if (save_plot_) {
      RCLCPP_INFO(this->get_logger(), "  Save directory: %s", save_dir_.c_str());
    }
  }

 private:
  void store_data(double timestamp, double roll_deg, double pitch_deg, double yaw_deg,
                  double gyr_x, double gyr_y, double gyr_z,
                  double acc_x, double acc_y, double acc_z) {
    IMUDataPoint point;
    point.timestamp = timestamp;
    point.roll = roll_deg;
    point.pitch = pitch_deg;
    point.yaw = yaw_deg;
    point.gyr_x = gyr_x;
    point.gyr_y = gyr_y;
    point.gyr_z = gyr_z;
    point.acc_x = acc_x;
    point.acc_y = acc_y;
    point.acc_z = acc_z;

    history_.push_back(point);
    if (history_.size() > history_size_) {
      history_.pop_front();
    }

    print_curve_data(point);
  }

  void imu_callback(const sensor_msgs::msg::Imu::SharedPtr msg) {
    total_messages_++;

    double roll, pitch, yaw;
    quaternionToEuler(msg->orientation.w, msg->orientation.x,
                      msg->orientation.y, msg->orientation.z,
                      roll, pitch, yaw);

    double roll_deg = roll * RAD_TO_DEG;
    double pitch_deg = pitch * RAD_TO_DEG;
    double yaw_deg = yaw * RAD_TO_DEG;

    double timestamp = msg->header.stamp.sec + msg->header.stamp.nanosec * 1e-9;

    store_data(timestamp, roll_deg, pitch_deg, yaw_deg,
               msg->angular_velocity.x, msg->angular_velocity.y, msg->angular_velocity.z,
               msg->linear_acceleration.x, msg->linear_acceleration.y, msg->linear_acceleration.z);

    publish_orientation_marker_with_quat(msg->orientation, roll_deg, pitch_deg, yaw_deg);
  }

  void robot_state_callback(const ros2_bridge_msgs::msg::RobotState::SharedPtr msg) {
    total_messages_++;

    const auto& imu = msg->imu;
    double timestamp = this->now().seconds();

    store_data(timestamp, imu.roll, imu.pitch, imu.yaw,
               imu.wx, imu.wy, imu.wz,
               imu.ax, imu.ay, imu.az);

    publish_orientation_marker_euler(imu.roll, imu.pitch, imu.yaw);
  }

  void publish_orientation_marker_with_quat(
      const geometry_msgs::msg::Quaternion& orientation,
      double roll_deg, double pitch_deg, double yaw_deg) {
    publish_markers(orientation, roll_deg, pitch_deg, yaw_deg);
  }

  void publish_orientation_marker_euler(double roll_deg, double pitch_deg, double yaw_deg) {
    double r = roll_deg / RAD_TO_DEG;
    double p = pitch_deg / RAD_TO_DEG;
    double y = yaw_deg / RAD_TO_DEG;

    geometry_msgs::msg::Quaternion q;
    q.w = cos(r/2)*cos(p/2)*cos(y/2) + sin(r/2)*sin(p/2)*sin(y/2);
    q.x = sin(r/2)*cos(p/2)*cos(y/2) - cos(r/2)*sin(p/2)*sin(y/2);
    q.y = cos(r/2)*sin(p/2)*cos(y/2) + sin(r/2)*cos(p/2)*sin(y/2);
    q.z = cos(r/2)*cos(p/2)*sin(y/2) - sin(r/2)*sin(p/2)*cos(y/2);

    publish_markers(q, roll_deg, pitch_deg, yaw_deg);
  }

  void publish_markers(const geometry_msgs::msg::Quaternion& orientation,
                       double roll_deg, double pitch_deg, double yaw_deg) {
    visualization_msgs::msg::MarkerArray marker_array;
    double axis_length = 0.1;
    double axis_width = 0.01;
    auto stamp = this->now();

    struct AxisColor { float r, g, b; };
    AxisColor colors[] = {{1,0,0}, {0,1,0}, {0,0,1}};

    for (int i = 0; i < 3; ++i) {
      visualization_msgs::msg::Marker m;
      m.header.frame_id = frame_id_;
      m.header.stamp = stamp;
      m.ns = "imu_orientation";
      m.id = i;
      m.type = visualization_msgs::msg::Marker::ARROW;
      m.action = visualization_msgs::msg::Marker::ADD;
      m.pose.orientation = orientation;
      m.scale.x = axis_length;
      m.scale.y = axis_width;
      m.scale.z = axis_width;
      m.color.r = colors[i].r;
      m.color.g = colors[i].g;
      m.color.b = colors[i].b;
      m.color.a = 1.0f;
      marker_array.markers.push_back(m);
    }

    visualization_msgs::msg::Marker text_marker;
    text_marker.header.frame_id = frame_id_;
    text_marker.header.stamp = stamp;
    text_marker.ns = "imu_text";
    text_marker.id = 0;
    text_marker.type = visualization_msgs::msg::Marker::TEXT_VIEW_FACING;
    text_marker.action = visualization_msgs::msg::Marker::ADD;
    text_marker.pose.position.z = 0.15;
    text_marker.pose.orientation.w = 1.0;
    text_marker.scale.z = 0.05;
    text_marker.color.r = text_marker.color.g = text_marker.color.b = text_marker.color.a = 1.0f;

    char text_buf[256];
    snprintf(text_buf, sizeof(text_buf),
             "[%s] R:%.1f° P:%.1f° Y:%.1f°",
             imu_source_.c_str(), roll_deg, pitch_deg, yaw_deg);
    text_marker.text = text_buf;
    marker_array.markers.push_back(text_marker);

    orientation_marker_pub_->publish(marker_array);
  }

  void print_curve_data(const IMUDataPoint& point) {
    std::cout << "IMU_DATA,"
              << std::fixed << std::setprecision(6) << point.timestamp << ","
              << std::setprecision(3) << point.roll << ","
              << point.pitch << ","
              << point.yaw << ","
              << point.gyr_x << ","
              << point.gyr_y << ","
              << point.gyr_z << ","
              << point.acc_x << ","
              << point.acc_y << ","
              << point.acc_z
              << std::endl;
  }

  void log_statistics() {
    if (total_messages_ == 0) {
      RCLCPP_INFO(this->get_logger(), "No IMU data received yet...");
      return;
    }
    if (history_.empty()) return;

    double avg_roll = 0, avg_pitch = 0, avg_yaw = 0;
    double avg_gyr_x = 0, avg_gyr_y = 0, avg_gyr_z = 0;
    double avg_acc_x = 0, avg_acc_y = 0, avg_acc_z = 0;

    for (const auto& p : history_) {
      avg_roll += p.roll;   avg_pitch += p.pitch;   avg_yaw += p.yaw;
      avg_gyr_x += p.gyr_x; avg_gyr_y += p.gyr_y;   avg_gyr_z += p.gyr_z;
      avg_acc_x += p.acc_x; avg_acc_y += p.acc_y;   avg_acc_z += p.acc_z;
    }

    size_t n = history_.size();
    avg_roll /= n; avg_pitch /= n; avg_yaw /= n;
    avg_gyr_x /= n; avg_gyr_y /= n; avg_gyr_z /= n;
    avg_acc_x /= n; avg_acc_y /= n; avg_acc_z /= n;

    RCLCPP_INFO(this->get_logger(),
                "[%s] Messages: %zu, History: %zu",
                imu_source_.c_str(), total_messages_, history_.size());
    RCLCPP_INFO(this->get_logger(),
                "Orientation (deg) - Roll: %.2f, Pitch: %.2f, Yaw: %.2f",
                avg_roll, avg_pitch, avg_yaw);
    RCLCPP_INFO(this->get_logger(),
                "Angular Velocity (rad/s) - X: %.3f, Y: %.3f, Z: %.3f",
                avg_gyr_x, avg_gyr_y, avg_gyr_z);
    RCLCPP_INFO(this->get_logger(),
                "Linear Acceleration (m/s²) - X: %.3f, Y: %.3f, Z: %.3f",
                avg_acc_x, avg_acc_y, avg_acc_z);
  }

  void generate_plot() {
    if (history_.empty()) {
      RCLCPP_INFO(this->get_logger(), "No IMU data for plotting...");
      return;
    }

    std::string csv_file = save_dir_ + "/imu_data.csv";
    std::ofstream file(csv_file);
    if (!file.is_open()) {
      RCLCPP_ERROR(this->get_logger(), "Failed to open CSV file: %s", csv_file.c_str());
      return;
    }

    file << "timestamp,roll,pitch,yaw,gyr_x,gyr_y,gyr_z,acc_x,acc_y,acc_z\n";
    for (const auto& p : history_) {
      file << std::fixed << std::setprecision(6) << p.timestamp << ","
           << std::setprecision(3) << p.roll << "," << p.pitch << "," << p.yaw << ","
           << p.gyr_x << "," << p.gyr_y << "," << p.gyr_z << ","
           << p.acc_x << "," << p.acc_y << "," << p.acc_z << "\n";
    }
    file.close();

    std::string script_path = ament_index_cpp::get_package_share_directory("imu_display_cpp")
                              + "/scripts/imu_plot_generator.py";
    std::string cmd = "python3 " + script_path +
                      " --csv " + csv_file +
                      " --output " + save_dir_ +
                      " --format " + save_format_ +
                      " --dpi " + std::to_string(dpi_);

    int result = system(cmd.c_str());
    if (result == 0) {
      RCLCPP_INFO(this->get_logger(), "Plot generated: %s/imu_plot.%s",
                  save_dir_.c_str(), save_format_.c_str());
    } else {
      RCLCPP_WARN(this->get_logger(), "Failed to generate plot (exit code: %d)", result);
    }
  }

  rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_subscription_;
  rclcpp::Subscription<ros2_bridge_msgs::msg::RobotState>::SharedPtr robot_state_subscription_;
  rclcpp::Publisher<visualization_msgs::msg::MarkerArray>::SharedPtr orientation_marker_pub_;
  rclcpp::TimerBase::SharedPtr stats_timer_;
  rclcpp::TimerBase::SharedPtr plot_timer_;

  std::string imu_source_;
  std::string imu_topic_;
  std::string frame_id_;
  size_t history_size_;
  double plot_interval_;
  bool save_plot_;
  std::string save_dir_;
  std::string save_format_;
  int dpi_;

  std::deque<IMUDataPoint> history_;
  size_t total_messages_;
  double last_print_time_;
};

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<IMUDisplayNode>());
  rclcpp::shutdown();
  return 0;
}
