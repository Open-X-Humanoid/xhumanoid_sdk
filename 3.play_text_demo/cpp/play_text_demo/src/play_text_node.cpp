/**
 * @file play_text_node.cpp
 * @brief 通过 /intelligent_interaction/tts/play 服务实现文字转语音播放
 *
 * 支持三种资源类型：文本(text)、本地音频文件(file)、远端URL(url)
 */

#include <chrono>
#include <memory>
#include <string>

#include "interaction_msgs/srv/tts_service.hpp"
#include "rclcpp/rclcpp.hpp"

class PlayTextNode : public rclcpp::Node {
 public:
  PlayTextNode() : Node("play_text_demo") {
    this->declare_parameter("text", "你好，我是天工机器人，很高兴认识你。");
    this->declare_parameter("type", "text");   // text / file / url
    this->declare_parameter("cmd", "append");  // append / stop / query

    client_ = this->create_client<interaction_msgs::srv::TtsService>(
        "/intelligent_interaction/tts/play");

    timer_ = this->create_wall_timer(
        std::chrono::milliseconds(500),
        std::bind(&PlayTextNode::call_tts_service, this));

    RCLCPP_INFO(this->get_logger(), "PlayTextNode initialized");
    RCLCPP_INFO(this->get_logger(), "Text: %s",
                this->get_parameter("text").as_string().c_str());
  }

 private:
  void call_tts_service() {
    timer_->cancel();

    while (!client_->wait_for_service(std::chrono::milliseconds(1000))) {
      if (!rclcpp::ok()) {
        RCLCPP_ERROR(this->get_logger(),
                     "Interrupted while waiting for TTS service. Exiting.");
        return;
      }
      RCLCPP_INFO(this->get_logger(), "TTS service not available, waiting...");
    }

    auto request = std::make_shared<interaction_msgs::srv::TtsService::Request>();
    request->text = this->get_parameter("text").as_string();
    request->type = this->get_parameter("type").as_string();
    request->cmd = this->get_parameter("cmd").as_string();

    RCLCPP_INFO(this->get_logger(),
                "Calling TTS service: text=\"%s\", type=%s, cmd=%s",
                request->text.c_str(), request->type.c_str(),
                request->cmd.c_str());

    auto future_result = client_->async_send_request(
        request, std::bind(&PlayTextNode::response_callback, this,
                           std::placeholders::_1));
  }

  void response_callback(
      rclcpp::Client<interaction_msgs::srv::TtsService>::SharedFuture future) {
    auto response = future.get();
    if (response->success) {
      RCLCPP_INFO(this->get_logger(), "TTS service success. Status: %s",
                  response->status.c_str());
    } else {
      RCLCPP_ERROR(this->get_logger(), "TTS service failed. Status: %s",
                   response->status.c_str());
    }
  }

  rclcpp::Client<interaction_msgs::srv::TtsService>::SharedPtr client_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<PlayTextNode>());
  rclcpp::shutdown();
  return 0;
}
