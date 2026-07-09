/**
 * @file mic_record_demo_node.cpp
 * @brief 通过 /lyre/audio_control 服务开启拾音器原始音频流，
 *        订阅 /lyre/audio_stream 接收音频数据并保存为 WAV 文件。
 */

#include <memory>
#include <string>
#include <vector>
#include <fstream>
#include <iostream>
#include <sstream>
#include <thread>
#include <chrono>
#include <ctime>
#include <atomic>
#include <mutex>
#include <iomanip>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include "std_msgs/msg/bool.hpp"
#include "std_srvs/srv/empty.hpp"
#include "lyre_msgs/srv/audio_control.hpp"
#include "lyre_msgs/msg/audio_frame.hpp"

#pragma pack(push, 1)
struct WavHeader {
  char riff[4] = {'R', 'I', 'F', 'F'};
  uint32_t overall_size = 0;
  char wave[4] = {'W', 'A', 'V', 'E'};
  char fmt_marker[4] = {'f', 'm', 't', ' '};
  uint32_t fmt_length = 16;
  uint16_t format = 1;
  uint16_t channels = 1;
  uint32_t sample_rate = 16000;
  uint32_t byte_rate = 32000;
  uint16_t block_align = 2;
  uint16_t bits_per_sample = 16;
  char data_marker[4] = {'d', 'a', 't', 'a'};
  uint32_t data_size = 0;
};
#pragma pack(pop)

class MicRecordDemoNode : public rclcpp::Node {
 public:
  MicRecordDemoNode()
      : Node("mic_record_demo_node"),
        is_recording_(false),
        frame_count_(0) {

    this->declare_parameter("output_dir", "/tmp");
    this->declare_parameter("max_duration", 60);

    output_dir_ = this->get_parameter("output_dir").as_string();
    max_duration_ = this->get_parameter("max_duration").as_int();

    audio_control_client_ = this->create_client<lyre_msgs::srv::AudioControl>(
        "/lyre/audio_control");

    audio_stream_sub_ = this->create_subscription<lyre_msgs::msg::AudioFrame>(
        "/lyre/audio_stream", 10,
        std::bind(&MicRecordDemoNode::audio_stream_callback, this,
                  std::placeholders::_1));

    status_pub_ = this->create_publisher<std_msgs::msg::String>("mic_record/status", 10);
    recording_pub_ = this->create_publisher<std_msgs::msg::Bool>("mic_record/is_recording", 10);

    status_timer_ = this->create_wall_timer(
        std::chrono::milliseconds(500),
        std::bind(&MicRecordDemoNode::publish_status, this));

    RCLCPP_INFO(this->get_logger(), "Mic Record Demo Node initialized");
    RCLCPP_INFO(this->get_logger(), "  Output directory: %s", output_dir_.c_str());
    RCLCPP_INFO(this->get_logger(), "  Max duration: %ds", max_duration_);
    RCLCPP_INFO(this->get_logger(), "");
    RCLCPP_INFO(this->get_logger(), "Audio source: /lyre/audio_stream");
    RCLCPP_INFO(this->get_logger(), "Audio control: /lyre/audio_control");
    RCLCPP_INFO(this->get_logger(), "");
    RCLCPP_INFO(this->get_logger(), "Commands:");
    RCLCPP_INFO(this->get_logger(), "  ros2 service call /mic_record/start std_srvs/srv/Empty");
    RCLCPP_INFO(this->get_logger(), "  ros2 service call /mic_record/stop std_srvs/srv/Empty");
  }

  ~MicRecordDemoNode() {
    if (is_recording_.load()) stop_recording();
  }

  void start_recording() {
    if (is_recording_.load()) {
      RCLCPP_WARN(this->get_logger(), "Already recording");
      return;
    }

    if (!audio_control_client_->wait_for_service(std::chrono::seconds(3))) {
      RCLCPP_ERROR(this->get_logger(), "AudioControl service not available");
      return;
    }

    auto req = std::make_shared<lyre_msgs::srv::AudioControl::Request>();
    req->enable = true;

    audio_control_client_->async_send_request(
        req, [this](rclcpp::Client<lyre_msgs::srv::AudioControl>::SharedFuture future) {
          auto resp = future.get();
          if (resp->success) {
            std::string ts = get_timestamp_string();
            current_file_ = output_dir_ + "/recording_" + ts + ".wav";
            {
              std::lock_guard<std::mutex> lock(data_mutex_);
              audio_data_.clear();
              frame_count_ = 0;
              sample_rate_ = 0;
              channels_ = 0;
              bits_per_sample_ = 0;
            }
            is_recording_ = true;
            publish_status_update("recording_started");
            RCLCPP_INFO(this->get_logger(), "Recording started: %s", current_file_.c_str());

            if (max_duration_ > 0) {
              max_timer_ = this->create_wall_timer(
                  std::chrono::seconds(max_duration_),
                  [this]() {
                    max_timer_->cancel();
                    RCLCPP_INFO(this->get_logger(), "Max recording duration reached");
                    stop_recording();
                  });
            }
          } else {
            RCLCPP_ERROR(this->get_logger(), "Failed to enable audio stream: %s",
                         resp->message.c_str());
          }
        });
  }

  void stop_recording() {
    if (!is_recording_.load()) {
      RCLCPP_WARN(this->get_logger(), "Not recording");
      return;
    }

    is_recording_ = false;
    if (max_timer_) max_timer_->cancel();

    auto req = std::make_shared<lyre_msgs::srv::AudioControl::Request>();
    req->enable = false;
    if (audio_control_client_->service_is_ready()) {
      audio_control_client_->async_send_request(req);
    }

    save_wav();
    publish_status_update("recording_stopped");
  }

 private:
  void audio_stream_callback(const lyre_msgs::msg::AudioFrame::SharedPtr msg) {
    if (!is_recording_.load()) return;

    std::lock_guard<std::mutex> lock(data_mutex_);
    if (frame_count_ == 0) {
      sample_rate_ = msg->sample_rate;
      channels_ = msg->channels;
      bits_per_sample_ = msg->bits_per_sample;
      RCLCPP_INFO(this->get_logger(), "Audio format: %uHz, %uch, %ubit",
                  sample_rate_, channels_, bits_per_sample_);
    }
    audio_data_.insert(audio_data_.end(), msg->data.begin(), msg->data.end());
    frame_count_++;
  }

  void save_wav() {
    std::vector<uint8_t> data;
    uint32_t sr, ch, bps;
    {
      std::lock_guard<std::mutex> lock(data_mutex_);
      data = audio_data_;
      sr = sample_rate_ > 0 ? sample_rate_ : 16000;
      ch = channels_ > 0 ? channels_ : 1;
      bps = bits_per_sample_ > 0 ? bits_per_sample_ : 16;
    }

    if (data.empty()) {
      RCLCPP_WARN(this->get_logger(), "No audio data captured");
      return;
    }

    WavHeader hdr;
    hdr.channels = ch;
    hdr.sample_rate = sr;
    hdr.bits_per_sample = bps;
    hdr.byte_rate = sr * ch * (bps / 8);
    hdr.block_align = ch * (bps / 8);
    hdr.data_size = data.size();
    hdr.overall_size = 36 + data.size();

    std::ofstream file(current_file_, std::ios::binary);
    if (!file.is_open()) {
      RCLCPP_ERROR(this->get_logger(), "Cannot create file: %s", current_file_.c_str());
      return;
    }
    file.write(reinterpret_cast<const char*>(&hdr), sizeof(hdr));
    file.write(reinterpret_cast<const char*>(data.data()), data.size());
    file.close();

    RCLCPP_INFO(this->get_logger(), "Recording saved: %s (%zu bytes, %u frames)",
                current_file_.c_str(), data.size(), frame_count_);
  }

  std::string get_timestamp_string() {
    auto now = std::chrono::system_clock::now();
    auto time = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time), "%Y%m%d_%H%M%S");
    return ss.str();
  }

  void publish_status() {
    auto msg = std_msgs::msg::Bool();
    msg.data = is_recording_.load();
    recording_pub_->publish(msg);
  }

  void publish_status_update(const std::string& status) {
    auto msg = std_msgs::msg::String();
    msg.data = status;
    status_pub_->publish(msg);
  }

  rclcpp::Client<lyre_msgs::srv::AudioControl>::SharedPtr audio_control_client_;
  rclcpp::Subscription<lyre_msgs::msg::AudioFrame>::SharedPtr audio_stream_sub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr status_pub_;
  rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr recording_pub_;
  rclcpp::TimerBase::SharedPtr status_timer_;
  rclcpp::TimerBase::SharedPtr max_timer_;

  std::string output_dir_;
  int max_duration_;

  std::atomic<bool> is_recording_;
  std::string current_file_;
  std::vector<uint8_t> audio_data_;
  uint32_t frame_count_;
  uint32_t sample_rate_ = 0;
  uint32_t channels_ = 0;
  uint32_t bits_per_sample_ = 0;
  std::mutex data_mutex_;
};

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<MicRecordDemoNode>();

  auto start_srv = node->create_service<std_srvs::srv::Empty>(
      "/mic_record/start",
      [&node](const std::shared_ptr<std_srvs::srv::Empty::Request>,
              std::shared_ptr<std_srvs::srv::Empty::Response>) {
        node->start_recording();
      });

  auto stop_srv = node->create_service<std_srvs::srv::Empty>(
      "/mic_record/stop",
      [&node](const std::shared_ptr<std_srvs::srv::Empty::Request>,
              std::shared_ptr<std_srvs::srv::Empty::Response>) {
        node->stop_recording();
      });

  RCLCPP_INFO(node->get_logger(), "Services: /mic_record/start, /mic_record/stop");

  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
