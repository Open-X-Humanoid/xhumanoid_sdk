/**
 * @file speaker_play_demo_node.cpp
 * @brief 通过 /intelligent_interaction/tts/play 服务实现音频播放控制
 *
 * 支持文本/文件/URL三种播报方式和停止/查询控制
 */

#include <memory>
#include <string>
#include <fstream>
#include <iostream>
#include <sstream>
#include <thread>
#include <chrono>

#include "rclcpp/rclcpp.hpp"
#include "interaction_msgs/srv/tts_service.hpp"

class SpeakerPlayDemoNode : public rclcpp::Node {
 public:
  SpeakerPlayDemoNode() : Node("speaker_play_demo_node") {
    this->declare_parameter("default_text", "你好，我是天工机器人。");
    this->declare_parameter("default_audio_path", "/tmp/test.wav");
    this->declare_parameter("auto_play_on_start", false);

    default_text_ = this->get_parameter("default_text").as_string();
    default_audio_path_ = this->get_parameter("default_audio_path").as_string();
    auto_play_on_start_ = this->get_parameter("auto_play_on_start").as_bool();

    tts_client_ = this->create_client<interaction_msgs::srv::TtsService>(
        "/intelligent_interaction/tts/play");

    RCLCPP_INFO(this->get_logger(), "Speaker Play Demo Node initialized");
    RCLCPP_INFO(this->get_logger(), "  Default text: %s", default_text_.c_str());
    RCLCPP_INFO(this->get_logger(), "  Default audio path: %s", default_audio_path_.c_str());

    RCLCPP_INFO(this->get_logger(), "Waiting for TTS service...");
    if (!tts_client_->wait_for_service(std::chrono::seconds(5))) {
      RCLCPP_WARN(this->get_logger(), "TTS service not available, will retry when needed");
    } else {
      RCLCPP_INFO(this->get_logger(), "TTS service is ready");
    }

    if (auto_play_on_start_) {
      std::thread([this]() {
        std::this_thread::sleep_for(std::chrono::seconds(1));
        play_text(default_text_);
      }).detach();
    }
  }

  void call_tts(const std::string& text, const std::string& res_type, const std::string& cmd) {
    if (!tts_client_->service_is_ready()) {
      RCLCPP_ERROR(this->get_logger(), "TTS service is not ready");
      return;
    }

    auto request = std::make_shared<interaction_msgs::srv::TtsService::Request>();
    request->text = text;
    request->type = res_type;
    request->cmd = cmd;

    RCLCPP_INFO(this->get_logger(), "TTS call: text=\"%.50s\", type=%s, cmd=%s",
                text.c_str(), res_type.c_str(), cmd.c_str());

    tts_client_->async_send_request(
        request,
        [this](rclcpp::Client<interaction_msgs::srv::TtsService>::SharedFuture future) {
          auto response = future.get();
          if (response->success) {
            RCLCPP_INFO(this->get_logger(), "TTS success. Status: %s",
                        response->status.c_str());
          } else {
            RCLCPP_ERROR(this->get_logger(), "TTS failed. Status: %s",
                         response->status.c_str());
          }
        });
  }

  void play_text(const std::string& text) {
    call_tts(text, "text", "append");
  }

  void play_file(const std::string& path) {
    std::ifstream f(path);
    if (!f.good()) {
      RCLCPP_ERROR(this->get_logger(), "Audio file does not exist: %s", path.c_str());
      return;
    }
    call_tts(path, "file", "append");
  }

  void play_url(const std::string& url) {
    call_tts(url, "url", "append");
  }

  void stop() {
    call_tts("", "text", "stop");
  }

  void query_status() {
    call_tts("", "text", "query");
  }

 private:
  rclcpp::Client<interaction_msgs::srv::TtsService>::SharedPtr tts_client_;
  std::string default_text_;
  std::string default_audio_path_;
  bool auto_play_on_start_;
};

void print_help() {
  std::cout << "\n========================================" << std::endl;
  std::cout << "Speaker Play Demo - Commands:" << std::endl;
  std::cout << "  text <content>  - Play text via TTS" << std::endl;
  std::cout << "  play <path>     - Play audio file" << std::endl;
  std::cout << "  url <url>       - Play audio from URL" << std::endl;
  std::cout << "  stop            - Stop playback" << std::endl;
  std::cout << "  status          - Query playback status" << std::endl;
  std::cout << "  help            - Show this help" << std::endl;
  std::cout << "  quit            - Exit program" << std::endl;
  std::cout << "========================================" << std::endl;
}

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<SpeakerPlayDemoNode>();

  std::thread spin_thread([&node]() {
    rclcpp::spin(node);
  });

  if (argc > 1) {
    std::string cmd = argv[1];
    if (cmd == "text" && argc > 2) {
      node->play_text(argv[2]);
    } else if (cmd == "play" && argc > 2) {
      node->play_file(argv[2]);
    } else if (cmd == "url" && argc > 2) {
      node->play_url(argv[2]);
    } else if (cmd == "stop") {
      node->stop();
    } else if (cmd == "status") {
      node->query_status();
    }
    std::this_thread::sleep_for(std::chrono::seconds(1));
  } else {
    print_help();

    std::string line;
    while (rclcpp::ok() && std::getline(std::cin, line)) {
      if (line.empty()) continue;

      std::istringstream iss(line);
      std::string cmd;
      iss >> cmd;

      if (cmd == "text") {
        std::string rest;
        std::getline(iss >> std::ws, rest);
        if (!rest.empty()) {
          node->play_text(rest);
        } else {
          std::cout << "Usage: text <content>" << std::endl;
        }
      } else if (cmd == "play") {
        std::string path;
        if (iss >> path) {
          node->play_file(path);
        } else {
          std::cout << "Usage: play <path>" << std::endl;
        }
      } else if (cmd == "url") {
        std::string url;
        if (iss >> url) {
          node->play_url(url);
        } else {
          std::cout << "Usage: url <url>" << std::endl;
        }
      } else if (cmd == "stop") {
        node->stop();
      } else if (cmd == "status") {
        node->query_status();
      } else if (cmd == "help") {
        print_help();
      } else if (cmd == "quit" || cmd == "exit") {
        break;
      } else {
        std::cout << "Unknown command: " << cmd << std::endl;
        print_help();
      }
    }
  }

  rclcpp::shutdown();
  if (spin_thread.joinable()) spin_thread.join();
  return 0;
}
