/**
 * @file point_cloud_display_node.cpp
 * @brief ROS2 node for displaying Livox LiDAR point cloud data
 *
 * This node subscribes to Livox point cloud data and provides:
 * - Point cloud statistics (point count, bounds)
 * - Basic filtering options
 * - Republishing for visualization
 */

#include <memory>
#include <string>
#include <algorithm>
#include <limits>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/point_cloud2.hpp"
#include "pcl_conversions/pcl_conversions.h"
#include "pcl/point_cloud.h"
#include "pcl/point_types.h"
#include "pcl/filters/voxel_grid.h"
#include "pcl/filters/statistical_outlier_removal.h"

class PointCloudDisplayNode : public rclcpp::Node {
 public:
  PointCloudDisplayNode()
      : Node("point_cloud_display_node"),
        total_frames_(0),
        total_points_(0),
        filter_enable_(false),
        voxel_leaf_size_(0.05f),
        sor_enable_(false),
        sor_mean_k_(50),
        sor_stddev_mul_thresh_(1.0) {
    // Declare parameters
    this->declare_parameter("input_topic", "/livox/lidar");
    this->declare_parameter("output_topic", "/point_cloud/filtered");
    this->declare_parameter("frame_id", "livox_frame");
    this->declare_parameter("filter_enable", false);
    this->declare_parameter("voxel_leaf_size", 0.05);
    this->declare_parameter("sor_enable", false);
    this->declare_parameter("sor_mean_k", 50);
    this->declare_parameter("sor_stddev_mul_thresh", 1.0);
    this->declare_parameter("publish_interval", 1.0);

    // Get parameters
    std::string input_topic = this->get_parameter("input_topic").as_string();
    std::string output_topic = this->get_parameter("output_topic").as_string();
    frame_id_ = this->get_parameter("frame_id").as_string();
    filter_enable_ = this->get_parameter("filter_enable").as_bool();
    voxel_leaf_size_ = static_cast<float>(this->get_parameter("voxel_leaf_size").as_double());
    sor_enable_ = this->get_parameter("sor_enable").as_bool();
    sor_mean_k_ = static_cast<int>(this->get_parameter("sor_mean_k").as_int());
    sor_stddev_mul_thresh_ = static_cast<float>(this->get_parameter("sor_stddev_mul_thresh").as_double());
    double publish_interval = this->get_parameter("publish_interval").as_double();

    // Create subscriber
    subscription_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
        input_topic, rclcpp::SensorDataQoS(),
        std::bind(&PointCloudDisplayNode::point_cloud_callback, this, std::placeholders::_1));

    // Create publisher
    publisher_ = this->create_publisher<sensor_msgs::msg::PointCloud2>(
        output_topic, rclcpp::SensorDataQoS());

    // Create statistics publisher
    stats_pub_ = this->create_publisher<sensor_msgs::msg::PointCloud2>(
        "/point_cloud/stats", rclcpp::QoS(10));

    // Create timer for periodic statistics logging
    stats_timer_ = this->create_wall_timer(
        std::chrono::duration<double>(publish_interval),
        std::bind(&PointCloudDisplayNode::log_statistics, this));

    RCLCPP_INFO(this->get_logger(), "Point Cloud Display Node initialized");
    RCLCPP_INFO(this->get_logger(), "  Input topic: %s", input_topic.c_str());
    RCLCPP_INFO(this->get_logger(), "  Output topic: %s", output_topic.c_str());
    RCLCPP_INFO(this->get_logger(), "  Frame ID: %s", frame_id_.c_str());
    RCLCPP_INFO(this->get_logger(), "  Filter enable: %s", filter_enable_ ? "true" : "false");
    if (filter_enable_) {
      RCLCPP_INFO(this->get_logger(), "  Voxel leaf size: %.3f", voxel_leaf_size_);
    }
    RCLCPP_INFO(this->get_logger(), "  Statistical Outlier Removal: %s", sor_enable_ ? "true" : "false");
    if (sor_enable_) {
      RCLCPP_INFO(this->get_logger(), "  SOR Mean K: %d, Stddev Mult: %.2f", sor_mean_k_, sor_stddev_mul_thresh_);
    }
  }

 private:
  void point_cloud_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg) {
    auto start_time = std::chrono::high_resolution_clock::now();

    // Update frame count
    total_frames_++;
    size_t input_points = msg->width * msg->height;
    total_points_ += input_points;

    // Convert to PCL format
    pcl::PointCloud<pcl::PointXYZI>::Ptr pcl_cloud(new pcl::PointCloud<pcl::PointXYZI>);
    pcl::fromROSMsg(*msg, *pcl_cloud);

    // Calculate bounds
    update_bounds(*pcl_cloud);

    // Apply filtering if enabled
    pcl::PointCloud<pcl::PointXYZI>::Ptr filtered_cloud = pcl_cloud;
    if (filter_enable_ || sor_enable_) {
      filtered_cloud = apply_filters(pcl_cloud);
    }

    // Convert back to ROS message
    sensor_msgs::msg::PointCloud2 output_msg;
    pcl::toROSMsg(*filtered_cloud, output_msg);
    output_msg.header.stamp = msg->header.stamp;
    output_msg.header.frame_id = frame_id_;

    // Publish filtered point cloud
    publisher_->publish(output_msg);

    // Calculate processing time
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    last_processing_time_ms_ = duration.count();
  }

  void update_bounds(const pcl::PointCloud<pcl::PointXYZI>& cloud) {
    if (cloud.empty()) {
      return;
    }

    min_x_ = std::numeric_limits<float>::max();
    max_x_ = std::numeric_limits<float>::lowest();
    min_y_ = std::numeric_limits<float>::max();
    max_y_ = std::numeric_limits<float>::lowest();
    min_z_ = std::numeric_limits<float>::max();
    max_z_ = std::numeric_limits<float>::lowest();

    for (const auto& point : cloud.points) {
      if (std::isfinite(point.x) && std::isfinite(point.y) && std::isfinite(point.z)) {
        min_x_ = std::min(min_x_, point.x);
        max_x_ = std::max(max_x_, point.x);
        min_y_ = std::min(min_y_, point.y);
        max_y_ = std::max(max_y_, point.y);
        min_z_ = std::min(min_z_, point.z);
        max_z_ = std::max(max_z_, point.z);
      }
    }
  }

  pcl::PointCloud<pcl::PointXYZI>::Ptr apply_filters(const pcl::PointCloud<pcl::PointXYZI>::Ptr& input) {
    pcl::PointCloud<pcl::PointXYZI>::Ptr cloud = input;

    // Apply Voxel Grid filter
    if (filter_enable_) {
      pcl::PointCloud<pcl::PointXYZI>::Ptr voxel_filtered(new pcl::PointCloud<pcl::PointXYZI>);
      pcl::VoxelGrid<pcl::PointXYZI> voxel_filter;
      voxel_filter.setInputCloud(cloud);
      voxel_filter.setLeafSize(voxel_leaf_size_, voxel_leaf_size_, voxel_leaf_size_);
      voxel_filter.filter(*voxel_filtered);
      cloud = voxel_filtered;
    }

    // Apply Statistical Outlier Removal filter
    if (sor_enable_) {
      pcl::PointCloud<pcl::PointXYZI>::Ptr sor_filtered(new pcl::PointCloud<pcl::PointXYZI>);
      pcl::StatisticalOutlierRemoval<pcl::PointXYZI> sor_filter;
      sor_filter.setInputCloud(cloud);
      sor_filter.setMeanK(sor_mean_k_);
      sor_filter.setStddevMulThresh(sor_stddev_mul_thresh_);
      sor_filter.filter(*sor_filtered);
      cloud = sor_filtered;
    }

    return cloud;
  }

  void log_statistics() {
    if (total_frames_ == 0) {
      RCLCPP_INFO(this->get_logger(), "No point cloud data received yet...");
      return;
    }

    RCLCPP_INFO(this->get_logger(),
                "Statistics - Frames: %lu, Total Points: %lu, Avg Points/Frame: %.0f",
                total_frames_, total_points_,
                static_cast<double>(total_points_) / total_frames_);

    RCLCPP_INFO(this->get_logger(),
                "Bounds - X: [%.2f, %.2f], Y: [%.2f, %.2f], Z: [%.2f, %.2f]",
                min_x_, max_x_, min_y_, max_y_, min_z_, max_z_);

    RCLCPP_INFO(this->get_logger(),
                "Last Processing Time: %ld ms", last_processing_time_ms_);
  }

  // ROS2 interfaces
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr subscription_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr publisher_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr stats_pub_;
  rclcpp::TimerBase::SharedPtr stats_timer_;

  // Parameters
  std::string frame_id_;
  bool filter_enable_;
  float voxel_leaf_size_;
  bool sor_enable_;
  int sor_mean_k_;
  float sor_stddev_mul_thresh_;

  // Statistics
  size_t total_frames_;
  size_t total_points_;
  float min_x_, max_x_, min_y_, max_y_, min_z_, max_z_;
  long last_processing_time_ms_;
};

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<PointCloudDisplayNode>());
  rclcpp::shutdown();
  return 0;
}