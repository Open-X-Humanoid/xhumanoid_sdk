/**
 * @file speech_recognition_node.cpp
 * @brief 订阅 /lyre/voice_activity 话题获取ASR语音活动事件
 *
 * 统一接收人脸唤醒、关键词唤醒、VAD事件、ASR识别结果等
 */

#include <memory>
#include <string>
#include <sstream>

#include "lyre_msgs/msg/lyre_voice_activity.hpp"
#include "rclcpp/rclcpp.hpp"

// Minimal JSON value extraction helpers (avoid external JSON lib dependency)
static std::string extract_string(const std::string& json, const std::string& key) {
  std::string search = "\"" + key + "\":\"";
  auto pos = json.find(search);
  if (pos == std::string::npos) return "";
  pos += search.size();
  auto end = json.find('"', pos);
  if (end == std::string::npos) return "";
  return json.substr(pos, end - pos);
}

static int extract_int(const std::string& json, const std::string& key, int def = -1) {
  std::string search = "\"" + key + "\":";
  auto pos = json.find(search);
  if (pos == std::string::npos) return def;
  pos += search.size();
  try { return std::stoi(json.substr(pos)); } catch (...) { return def; }
}

static std::string extract_asr_text(const std::string& json) {
  std::string result;
  std::string search = "\"w\":\"";
  size_t pos = 0;
  while ((pos = json.find(search, pos)) != std::string::npos) {
    pos += search.size();
    auto end = json.find('"', pos);
    if (end != std::string::npos) {
      result += json.substr(pos, end - pos);
      pos = end + 1;
    }
  }
  return result;
}

class SpeechRecognitionNode : public rclcpp::Node {
 public:
  SpeechRecognitionNode() : Node("speech_recognition_demo") {
    voice_activity_sub_ = this->create_subscription<lyre_msgs::msg::LyreVoiceActivity>(
        "/lyre/voice_activity", 10,
        std::bind(&SpeechRecognitionNode::voice_activity_callback, this,
                  std::placeholders::_1));

    RCLCPP_INFO(this->get_logger(), "SpeechRecognitionNode initialized");
    RCLCPP_INFO(this->get_logger(), "Subscribed to: /lyre/voice_activity");
  }

 private:
  void voice_activity_callback(const lyre_msgs::msg::LyreVoiceActivity::SharedPtr msg) {
    const auto& content = msg->content;
    std::string type = extract_string(content, "type");
    std::string trace_id = extract_string(content, "traceId");

    if (type != "aiui_event") {
      RCLCPP_INFO(this->get_logger(), "[VoiceActivity] type=%s", type.c_str());
      return;
    }

    int event_type = extract_int(content, "eventType");

    switch (event_type) {
      case 1: {
        std::string text = extract_asr_text(content);
        RCLCPP_INFO(this->get_logger(), "[ASR] 识别结果: \"%s\" (traceId=%s)",
                    text.c_str(), trace_id.c_str());
        break;
      }
      case 4: {
        int angle = extract_int(content, "angle");
        RCLCPP_INFO(this->get_logger(), "[唤醒] 关键词唤醒，角度: %d° (traceId=%s)",
                    angle, trace_id.c_str());
        break;
      }
      case 5:
        RCLCPP_INFO(this->get_logger(), "[对话] 退出对话 (traceId=%s)",
                    trace_id.c_str());
        break;
      case 6: {
        int arg1 = extract_int(content, "arg1");
        if (arg1 == 0) {
          RCLCPP_INFO(this->get_logger(), "[VAD] 检测到语音开始 (traceId=%s)",
                      trace_id.c_str());
        } else if (arg1 == 2) {
          RCLCPP_INFO(this->get_logger(), "[VAD] 检测到语音结束 (traceId=%s)",
                      trace_id.c_str());
        } else {
          RCLCPP_INFO(this->get_logger(), "[VAD] VAD事件 arg1=%d (traceId=%s)",
                      arg1, trace_id.c_str());
        }
        break;
      }
      case 20:
        RCLCPP_INFO(this->get_logger(), "[唤醒] 人脸识别唤醒 (traceId=%s)",
                    trace_id.c_str());
        break;
      default:
        RCLCPP_INFO(this->get_logger(), "[事件] eventType=%d (traceId=%s)",
                    event_type, trace_id.c_str());
        break;
    }
  }

  rclcpp::Subscription<lyre_msgs::msg::LyreVoiceActivity>::SharedPtr voice_activity_sub_;
};

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<SpeechRecognitionNode>());
  rclcpp::shutdown();
  return 0;
}
