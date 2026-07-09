/**
 * @file camera_6v_display_node.cpp
 * @brief ROS2 node for visualizing 6 camera streams
 *
 * This node subscribes to 6 camera image topics and displays them
 * in a grid layout using OpenCV.
 *
 * Camera indices: 0, 1, 2, 4, 5, 6 (skipping 3 and 7)
 */

#include <memory>
#include <string>
#include <vector>
#include <map>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "sensor_msgs/msg/compressed_image.hpp"
#include <opencv2/opencv.hpp>
#if __has_include(<cv_bridge/cv_bridge.hpp>)
#include <cv_bridge/cv_bridge.hpp>
#else
#include <cv_bridge/cv_bridge.h>
#endif

class Camera6vDisplayNode : public rclcpp::Node {
 public:
  Camera6vDisplayNode()
      : Node("camera_6v_display_node"),
        display_width_(320),
        display_height_(240),
        use_compressed_(false),
        total_frames_(0) {

    // Declare parameters
    this->declare_parameter("display_width", 320);
    this->declare_parameter("display_height", 240);
    this->declare_parameter("use_compressed", false);
    this->declare_parameter("show_fps", true);
    this->declare_parameter("window_name", "6V Camera Display");
    this->declare_parameter("topic_prefix", "camera");

    // Get parameters
    display_width_ = this->get_parameter("display_width").as_int();
    display_height_ = this->get_parameter("display_height").as_int();
    use_compressed_ = this->get_parameter("use_compressed").as_bool();
    show_fps_ = this->get_parameter("show_fps").as_bool();
    window_name_ = this->get_parameter("window_name").as_string();
    topic_prefix_ = this->get_parameter("topic_prefix").as_string();

    // Camera indices (skipping 3 and 7)
    camera_indices_ = {0, 1, 2, 4, 5, 6};

    // Initialize subscribers and frame storage
    for (int idx : camera_indices_) {
      std::string topic = topic_prefix_ + std::to_string(idx) + "/image_raw";
      std::string compressed_topic = topic_prefix_ + std::to_string(idx) + "/image/compressed";

      if (use_compressed_) {
        auto sub = this->create_subscription<sensor_msgs::msg::CompressedImage>(
            compressed_topic, rclcpp::QoS(10),
            [this, idx](const sensor_msgs::msg::CompressedImage::SharedPtr msg) {
              compressed_image_callback(msg, idx);
            });
        compressed_subscribers_[idx] = sub;
      } else {
        auto sub = this->create_subscription<sensor_msgs::msg::Image>(
            topic, rclcpp::QoS(10),
            [this, idx](const sensor_msgs::msg::Image::SharedPtr msg) {
              image_callback(msg, idx);
            });
        subscribers_[idx] = sub;
      }

      // Initialize frame statistics
      frame_counts_[idx] = 0;
      last_frame_times_[idx] = this->now();
      fps_values_[idx] = 0.0;

      // Initialize placeholder image
      cv::Mat placeholder(display_height_, display_width_, CV_8UC3, cv::Scalar(50, 50, 50));
      cv::putText(placeholder, "CAM " + std::to_string(idx), cv::Point(10, 30),
                  cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(200, 200, 200), 2);
      cv::putText(placeholder, "Waiting...", cv::Point(10, 60),
                  cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(150, 150, 150), 1);
      latest_frames_[idx] = placeholder.clone();
    }

    // Create display timer (30 Hz)
    display_timer_ = this->create_wall_timer(
        std::chrono::milliseconds(33),
        std::bind(&Camera6vDisplayNode::update_display, this));

    // Create FPS calculation timer (1 Hz)
    fps_timer_ = this->create_wall_timer(
        std::chrono::seconds(1),
        std::bind(&Camera6vDisplayNode::calculate_fps, this));

    // Create OpenCV window
    cv::namedWindow(window_name_, cv::WINDOW_NORMAL);
    cv::resizeWindow(window_name_, display_width_ * 3, display_height_ * 2);

    RCLCPP_INFO(this->get_logger(), "Camera 6V Display Node initialized");
    RCLCPP_INFO(this->get_logger(), "  Display size: %dx%d per camera", display_width_, display_height_);
    RCLCPP_INFO(this->get_logger(), "  Use compressed: %s", use_compressed_ ? "true" : "false");
    for (int idx : camera_indices_) {
      std::string topic = use_compressed_ ?
          topic_prefix_ + std::to_string(idx) + "/image/compressed" :
          topic_prefix_ + std::to_string(idx) + "/image_raw";
      RCLCPP_INFO(this->get_logger(), "  Subscribed to: %s", topic.c_str());
    }
  }

  ~Camera6vDisplayNode() {
    cv::destroyAllWindows();
  }

 private:
  void image_callback(const sensor_msgs::msg::Image::SharedPtr msg, int camera_idx) {
    try {
      // Convert ROS image to OpenCV
      cv_bridge::CvImagePtr cv_ptr;
      cv_ptr = cv_bridge::toCvCopy(msg, sensor_msgs::image_encodings::RGB8);

      // Store the frame
      process_frame(cv_ptr->image, camera_idx);

    } catch (const cv_bridge::Exception& e) {
      RCLCPP_ERROR(this->get_logger(), "cv_bridge exception for camera %d: %s", camera_idx, e.what());
    }
  }

  void compressed_image_callback(const sensor_msgs::msg::CompressedImage::SharedPtr msg, int camera_idx) {
    try {
      // Decode compressed image
      cv::Mat image = cv::imdecode(cv::Mat(msg->data), cv::IMREAD_COLOR);

      if (!image.empty()) {
        // Convert BGR to RGB for consistent display
        cv::cvtColor(image, image, cv::COLOR_BGR2RGB);
        process_frame(image, camera_idx);
      }
    } catch (const std::exception& e) {
      RCLCPP_ERROR(this->get_logger(), "Exception decoding compressed image for camera %d: %s", camera_idx, e.what());
    }
  }

  void process_frame(cv::Mat& frame, int camera_idx) {
    // Resize frame to display size
    cv::Mat resized;
    cv::resize(frame, resized, cv::Size(display_width_, display_height_));

    // Add camera label
    std::string label = "CAM " + std::to_string(camera_idx);
    cv::putText(resized, label, cv::Point(5, 20),
                cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(0, 255, 0), 1);

    // Add FPS if enabled
    if (show_fps_ && fps_values_[camera_idx] > 0) {
      std::string fps_text = std::to_string(static_cast<int>(fps_values_[camera_idx])) + " FPS";
      cv::putText(resized, fps_text, cv::Point(display_width_ - 70, 20),
                  cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(0, 255, 0), 1);
    }

    // Update frame counter and store
    frame_counts_[camera_idx]++;
    total_frames_++;
    latest_frames_[camera_idx] = resized.clone();
  }

  void calculate_fps() {
    auto now = this->now();
    for (int idx : camera_indices_) {
      double elapsed = (now - last_frame_times_[idx]).seconds();
      if (elapsed > 0) {
        fps_values_[idx] = frame_counts_[idx] / elapsed;
      }
      // Reset counters
      frame_counts_[idx] = 0;
      last_frame_times_[idx] = now;
    }
  }

  void update_display() {
    // Create a 2x3 grid layout
    // Row 0: CAM0, CAM1, CAM2
    // Row 1: CAM4, CAM5, CAM6

    cv::Mat row0, row1;

    // Get frames for row 0 (cameras 0, 1, 2)
    cv::hconcat(std::vector<cv::Mat>{
        latest_frames_[0], latest_frames_[1], latest_frames_[2]
    }, row0);

    // Get frames for row 1 (cameras 4, 5, 6)
    cv::hconcat(std::vector<cv::Mat>{
        latest_frames_[4], latest_frames_[5], latest_frames_[6]
    }, row1);

    // Combine rows
    cv::Mat grid;
    cv::vconcat(std::vector<cv::Mat>{row0, row1}, grid);

    // Add timestamp
    std::string timestamp = get_current_time_string();
    cv::putText(grid, timestamp, cv::Point(10, grid.rows - 10),
                cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(255, 255, 255), 1);

    // Convert RGB to BGR for display
    cv::Mat display;
    cv::cvtColor(grid, display, cv::COLOR_RGB2BGR);

    // Show the image
    cv::imshow(window_name_, display);
    cv::waitKey(1);
  }

  std::string get_current_time_string() {
    auto now = std::chrono::system_clock::now();
    auto time = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time), "%Y-%m-%d %H:%M:%S");
    return ss.str();
  }

  // ROS2 interfaces
  std::map<int, rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr> subscribers_;
  std::map<int, rclcpp::Subscription<sensor_msgs::msg::CompressedImage>::SharedPtr> compressed_subscribers_;
  rclcpp::TimerBase::SharedPtr display_timer_;
  rclcpp::TimerBase::SharedPtr fps_timer_;

  // Camera indices
  std::vector<int> camera_indices_;

  // Frame storage
  std::map<int, cv::Mat> latest_frames_;
  std::map<int, int> frame_counts_;
  std::map<int, rclcpp::Time> last_frame_times_;
  std::map<int, double> fps_values_;

  // Parameters
  int display_width_;
  int display_height_;
  bool use_compressed_;
  bool show_fps_;
  std::string window_name_;
  std::string topic_prefix_;

  // Statistics
  size_t total_frames_;
};

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);

  auto node = std::make_shared<Camera6vDisplayNode>();

  // Handle window close
  while (rclcpp::ok()) {
    rclcpp::spin_some(node);

    // Check for window close
    char key = cv::waitKey(10);
    if (key == 27 || key == 'q') {  // ESC or 'q' to quit
      RCLCPP_INFO(node->get_logger(), "User requested shutdown");
      break;
    }
  }

  rclcpp::shutdown();
  return 0;
}