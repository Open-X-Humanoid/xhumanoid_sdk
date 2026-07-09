/**
 * @file gps_data_display_node.cpp
 * @brief ROS2 node for receiving and parsing GPS data from GPS driver
 *
 * This node subscribes to GPS data from the gps_ros2 driver and provides:
 * - Real-time GPS data display
 * - GPS status parsing and visualization
 * - Data logging to file
 * - Statistics calculation
 */

#include <memory>
#include <string>
#include <vector>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <chrono>
#include <cmath>

#include "rclcpp/rclcpp.hpp"
#include "navigation_msgs/msg/gps_fix.hpp"

class GPSDataDisplayNode : public rclcpp::Node {
 public:
  GPSDataDisplayNode()
      : Node("gps_data_display_node"),
        total_messages_(0),
        valid_messages_(0),
        save_to_file_(false),
        log_interval_(1.0) {

    // Declare parameters
    this->declare_parameter("gps_topic", "gps/fix");
    this->declare_parameter("save_to_file", false);
    this->declare_parameter("log_file", "/tmp/gps_data.txt");
    this->declare_parameter("log_interval", 1.0);
    this->declare_parameter("show_raw_data", true);
    this->declare_parameter("show_status", true);

    // Get parameters
    gps_topic_ = this->get_parameter("gps_topic").as_string();
    save_to_file_ = this->get_parameter("save_to_file").as_bool();
    log_file_ = this->get_parameter("log_file").as_string();
    log_interval_ = this->get_parameter("log_interval").as_double();
    show_raw_data_ = this->get_parameter("show_raw_data").as_bool();
    show_status_ = this->get_parameter("show_status").as_bool();

    // Create subscriber
    subscription_ = this->create_subscription<navigation_msgs::msg::GpsFix>(
        gps_topic_, rclcpp::QoS(10),
        std::bind(&GPSDataDisplayNode::gps_callback, this, std::placeholders::_1));

    // Create statistics timer
    stats_timer_ = this->create_wall_timer(
        std::chrono::duration<double>(log_interval_),
        std::bind(&GPSDataDisplayNode::log_statistics, this));

    // Initialize statistics
    last_valid_time_ = this->now();
    min_lat_ = 90.0;
    max_lat_ = -90.0;
    min_lon_ = 180.0;
    max_lon_ = -180.0;
    max_speed_ = 0.0;
    max_sats_ = 0;

    // Open log file if enabled
    if (save_to_file_) {
      log_file_stream_.open(log_file_, std::ios::app);
      if (log_file_stream_.is_open()) {
        log_file_stream_ << "# GPS Data Log - Started at " << get_current_time_string() << std::endl;
        log_file_stream_ << "# timestamp,lat,lon,alt,status,sats,hdop,speed,heading,tx_ms" << std::endl;
        RCLCPP_INFO(this->get_logger(), "Log file opened: %s", log_file_.c_str());
      } else {
        RCLCPP_ERROR(this->get_logger(), "Failed to open log file: %s", log_file_.c_str());
        save_to_file_ = false;
      }
    }

    RCLCPP_INFO(this->get_logger(), "GPS Data Display Node initialized");
    RCLCPP_INFO(this->get_logger(), "  GPS topic: %s", gps_topic_.c_str());
    RCLCPP_INFO(this->get_logger(), "  Save to file: %s", save_to_file_ ? "true" : "false");
    if (save_to_file_) {
      RCLCPP_INFO(this->get_logger(), "  Log file: %s", log_file_.c_str());
    }
  }

  ~GPSDataDisplayNode() {
    if (log_file_stream_.is_open()) {
      log_file_stream_.close();
    }
  }

 private:
  void gps_callback(const navigation_msgs::msg::GpsFix::SharedPtr msg) {
    total_messages_++;

    // Parse GPS status
    std::string status_str = get_status_string(msg->status);
    bool is_valid = (msg->status > 0);

    if (is_valid) {
      valid_messages_++;
      last_valid_time_ = this->now();

      // Update statistics
      update_statistics(msg);

      // Update position bounds
      if (msg->latitude >= -90.0 && msg->latitude <= 90.0) {
        min_lat_ = std::min(min_lat_, msg->latitude);
        max_lat_ = std::max(max_lat_, msg->latitude);
      }
      if (msg->longitude >= -180.0 && msg->longitude <= 180.0) {
        min_lon_ = std::min(min_lon_, msg->longitude);
        max_lon_ = std::max(max_lon_, msg->longitude);
      }
    }

    // Display raw data
    if (show_raw_data_) {
      display_gps_data(msg, status_str);
    }

    // Show status summary
    if (show_status_) {
      display_status_summary(msg, status_str);
    }

    // Save to file if enabled
    if (save_to_file_ && log_file_stream_.is_open()) {
      save_to_log(msg);
    }
  }

  std::string get_status_string(int32_t status) {
    switch (status) {
      case 0: return "INVALID";
      case 1: return "SINGLE";
      case 2: return "DGPS/SBAS";
      case 4: return "RTK_FIXED";
      case 5: return "RTK_FLOAT";
      default: return "UNKNOWN(" + std::to_string(status) + ")";
    }
  }

  std::string get_status_color(int32_t status) {
    // Return ANSI color code based on status
    switch (status) {
      case 0: return "\033[31m";  // Red - Invalid
      case 1: return "\033[33m";  // Yellow - Single point
      case 2: return "\033[36m";  // Cyan - DGPS
      case 4: return "\033[32m";  // Green - RTK Fixed
      case 5: return "\033[34m";  // Blue - RTK Float
      default: return "\033[0m";  // Reset
    }
  }

  void display_gps_data(const navigation_msgs::msg::GpsFix::SharedPtr msg, const std::string& status_str) {
    std::string color = get_status_color(msg->status);
    std::string reset = "\033[0m";

    RCLCPP_INFO(this->get_logger(), "");
    RCLCPP_INFO(this->get_logger(), "========== GPS Data ==========");
    RCLCPP_INFO(this->get_logger(), "  Timestamp: %s", get_current_time_string().c_str());
    RCLCPP_INFO(this->get_logger(), "  Status: %s%s%s", color.c_str(), status_str.c_str(), reset.c_str());
    RCLCPP_INFO(this->get_logger(), "  Position:");
    RCLCPP_INFO(this->get_logger(), "    Latitude:  %.6f° %s", msg->latitude, msg->latitude >= 0 ? "N" : "S");
    RCLCPP_INFO(this->get_logger(), "    Longitude: %.6f° %s", msg->longitude, msg->longitude >= 0 ? "E" : "W");
    RCLCPP_INFO(this->get_logger(), "    Altitude:  %.3f m", msg->altitude);
    RCLCPP_INFO(this->get_logger(), "  Quality:");
    RCLCPP_INFO(this->get_logger(), "    Satellites: %d", msg->num_sats);
    RCLCPP_INFO(this->get_logger(), "    HDOP: %.2f", msg->hdop);
    RCLCPP_INFO(this->get_logger(), "  Motion:");
    RCLCPP_INFO(this->get_logger(), "    Speed:   %.3f m/s (%.1f km/h)", msg->speed, msg->speed * 3.6);
    RCLCPP_INFO(this->get_logger(), "    Heading: %.2f°", msg->heading);
    RCLCPP_INFO(this->get_logger(), "  Timing:");
    RCLCPP_INFO(this->get_logger(), "    GPS-PPS diff: %.3f ms", msg->tx);
    RCLCPP_INFO(this->get_logger(), "==============================");
  }

  void display_status_summary(const navigation_msgs::msg::GpsFix::SharedPtr msg, const std::string& status_str) {
    std::string color = get_status_color(msg->status);
    std::string reset = "\033[0m";

    // Single line summary for quick monitoring
    RCLCPP_INFO(this->get_logger(), "%s[GPS]%s %s | Sats:%d | HDOP:%.1f | %.6f,%.6f | Alt:%.1fm | Spd:%.1fkm/h | Head:%.1f°",
        color.c_str(), reset.c_str(),
        status_str.c_str(),
        msg->num_sats,
        msg->hdop,
        msg->latitude,
        msg->longitude,
        msg->altitude,
        msg->speed * 3.6,
        msg->heading);
  }

  void update_statistics(const navigation_msgs::msg::GpsFix::SharedPtr msg) {
    if (msg->speed > max_speed_) {
      max_speed_ = msg->speed;
    }
    if (msg->num_sats > max_sats_) {
      max_sats_ = msg->num_sats;
    }
  }

  void save_to_log(const navigation_msgs::msg::GpsFix::SharedPtr msg) {
    auto now = std::chrono::system_clock::now();
    auto now_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(now.time_since_epoch()).count();

    log_file_stream_ << std::fixed << std::setprecision(6)
                     << now_ns / 1e9 << ","
                     << msg->latitude << ","
                     << msg->longitude << ","
                     << msg->altitude << ","
                     << msg->status << ","
                     << msg->num_sats << ","
                     << msg->hdop << ","
                     << msg->speed << ","
                     << msg->heading << ","
                     << msg->tx
                     << std::endl;
  }

  void log_statistics() {
    if (total_messages_ == 0) {
      RCLCPP_INFO(this->get_logger(), "No GPS data received yet...");
      return;
    }

    double valid_rate = (total_messages_ > 0) ? (100.0 * valid_messages_ / total_messages_) : 0.0;

    RCLCPP_INFO(this->get_logger(), "");
    RCLCPP_INFO(this->get_logger(), "======= GPS Statistics =======");
    RCLCPP_INFO(this->get_logger(), "  Total messages: %lu", total_messages_);
    RCLCPP_INFO(this->get_logger(), "  Valid messages: %lu (%.1f%%)", valid_messages_, valid_rate);
    RCLCPP_INFO(this->get_logger(), "  Position bounds:");
    RCLCPP_INFO(this->get_logger(), "    Latitude:  [%.6f, %.6f]", min_lat_, max_lat_);
    RCLCPP_INFO(this->get_logger(), "    Longitude: [%.6f, %.6f]", min_lon_, max_lon_);
    RCLCPP_INFO(this->get_logger(), "  Max speed: %.3f m/s (%.1f km/h)", max_speed_, max_speed_ * 3.6);
    RCLCPP_INFO(this->get_logger(), "  Max satellites: %d", max_sats_);
    RCLCPP_INFO(this->get_logger(), "==============================");
  }

  std::string get_current_time_string() {
    auto now = std::chrono::system_clock::now();
    auto time = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()) % 1000;
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time), "%Y-%m-%d %H:%M:%S");
    ss << '.' << std::setfill('0') << std::setw(3) << ms.count();
    return ss.str();
  }

  // ROS2 interfaces
  rclcpp::Subscription<navigation_msgs::msg::GpsFix>::SharedPtr subscription_;
  rclcpp::TimerBase::SharedPtr stats_timer_;

  // Parameters
  std::string gps_topic_;
  bool save_to_file_;
  std::string log_file_;
  double log_interval_;
  bool show_raw_data_;
  bool show_status_;

  // Log file stream
  std::ofstream log_file_stream_;

  // Statistics
  size_t total_messages_;
  size_t valid_messages_;
  rclcpp::Time last_valid_time_;

  // Position bounds
  double min_lat_, max_lat_;
  double min_lon_, max_lon_;
  double max_speed_;
  int max_sats_;
};

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<GPSDataDisplayNode>());
  rclcpp::shutdown();
  return 0;
}