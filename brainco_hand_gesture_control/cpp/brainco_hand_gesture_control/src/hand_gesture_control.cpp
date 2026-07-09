/**
 * @file hand_gesture_control.cpp
 * @brief 灵巧手手势控制节点 - 实现OK手势和剪刀石头布功能
 *
 * 该节点通过位置模式控制灵巧手实现预设手势:
 * - OK手势: 大拇指和食指捏合,其他手指伸直
 * - 石头: 所有手指弯曲握拳
 * - 剪刀: 食指和中指伸直,其他手指弯曲
 * - 布: 所有手指伸直张开
 *
 * 手指索引 (6个电机):
 * - 0: 拇指弯曲
 * - 1: 拇指旋转
 * - 2: 食指
 * - 3: 中指
 * - 4: 无名指
 * - 5: 小指
 *
 * 通过ROS2服务触发手势:
 * - 服务名: /gesture_command
 * - 请求: gesture (ok/rock/scissors/paper)
 */

#include <rclcpp/rclcpp.hpp>
#include <brainco_hand_msgs/msg/set_motor_multi.hpp>
#include <brainco_hand_msgs/msg/motor_status.hpp>
#include <brainco_hand_gesture_interfaces/srv/gesture_command.hpp>
#include <map>
#include <string>
#include <vector>
#include <algorithm>
#include <array>

using GestureCommand = brainco_hand_gesture_interfaces::srv::GestureCommand;

class HandGestureControl : public rclcpp::Node
{
public:
    HandGestureControl() : Node("brainco_hand_gesture_control")
    {
        // 声明参数
        this->declare_parameter("hand_prefix", "right_hand");  // right_hand 或 left_hand
        this->declare_parameter("control_mode", 1);  // 1: 位置模式

        // 获取参数
        hand_prefix_ = this->get_parameter("hand_prefix").as_string();
        control_mode_ = this->get_parameter("control_mode").as_int();

        // 构建话题名称
        std::string motor_cmd_topic = hand_prefix_ + "/set_motor_multi";
        std::string motor_status_topic = hand_prefix_ + "/motor_status";

        // 创建电机控制发布者
        motor_pub_ = this->create_publisher<brainco_hand_msgs::msg::SetMotorMulti>(
            motor_cmd_topic, 10);

        // 创建电机状态订阅者
        status_sub_ = this->create_subscription<brainco_hand_msgs::msg::MotorStatus>(
            motor_status_topic, 10,
            std::bind(&HandGestureControl::statusCallback, this, std::placeholders::_1));

        // 创建手势控制服务
        gesture_service_ = this->create_service<GestureCommand>(
            "gesture_command",
            std::bind(&HandGestureControl::gestureCommandCallback,
                      this, std::placeholders::_1, std::placeholders::_2));

        // 初始化手势位置映射
        initGesturePositions();

        RCLCPP_INFO(this->get_logger(), "灵巧手手势控制节点已启动");
        RCLCPP_INFO(this->get_logger(), "手: %s", hand_prefix_.c_str());
        RCLCPP_INFO(this->get_logger(), "控制话题: %s", motor_cmd_topic.c_str());
        RCLCPP_INFO(this->get_logger(), "状态话题: %s", motor_status_topic.c_str());
        RCLCPP_INFO(this->get_logger(), "服务: /gesture_command");
        RCLCPP_INFO(this->get_logger(), "支持的手势: ok, rock(石头), scissors(剪刀), paper(布)");
    }

private:
    // 手指索引定义 (6个电机: 拇指弯曲, 拇指旋转, 食指-小指)
    enum FingerIndex
    {
        THUMB_FLEX = 0,   // 拇指弯曲
        THUMB_ROTATE = 1, // 拇指旋转
        INDEX = 2,        // 食指
        MIDDLE = 3,       // 中指
        RING = 4,         // 无名指
        PINKY = 5         // 小指
    };

    // 电机数量
    static constexpr int MOTOR_COUNT = 6;

    // 位置范围: 1 (完全伸直) ~ 1000 (完全弯曲)
    static constexpr uint16_t POS_MIN = 1;      // 完全伸直
    static constexpr uint16_t POS_MAX = 1000;   // 完全弯曲

    // 手势位置数组 (6个电机的位置值)
    using GesturePositions = std::array<uint16_t, MOTOR_COUNT>;

    // 发布者
    rclcpp::Publisher<brainco_hand_msgs::msg::SetMotorMulti>::SharedPtr motor_pub_;

    // 订阅者
    rclcpp::Subscription<brainco_hand_msgs::msg::MotorStatus>::SharedPtr status_sub_;

    // 服务
    rclcpp::Service<GestureCommand>::SharedPtr gesture_service_;

    // 手势位置映射
    std::map<std::string, GesturePositions> gesture_positions_;

    // 当前电机状态
    brainco_hand_msgs::msg::MotorStatus::SharedPtr current_status_;

    // 参数
    std::string hand_prefix_;
    int control_mode_;

    /**
     * @brief 初始化手势位置映射
     *
     * 位置范围: 1 (完全伸直) ~ 1000 (完全弯曲)
     * 手指顺序: [拇指弯曲, 拇指旋转, 食指, 中指, 无名指, 小指]
     */
    void initGesturePositions()
    {
        // OK手势: 大拇指和食指捏合,其他手指伸直
        gesture_positions_["ok"] = {{
            450,     // 拇指弯曲: 中等弯曲
            800,     // 拇指旋转: 适当旋转角度
            450,     // 食指: 弯曲与拇指捏合
            POS_MIN, // 中指: 伸直
            POS_MIN, // 无名指: 伸直
            POS_MIN  // 小指: 伸直
        }};

        // 石头: 所有手指弯曲握拳
        gesture_positions_["rock"] = {{
            800,     // 拇指弯曲: 完全弯曲
            500,     // 拇指旋转: 中间位置
            900,     // 食指: 完全弯曲
            900,     // 中指: 完全弯曲
            900,     // 无名指: 完全弯曲
            900      // 小指: 完全弯曲
        }};

        // 剪刀: 食指和中指伸直,其他手指弯曲
        gesture_positions_["scissors"] = {{
            800,     // 拇指弯曲: 弯曲
            500,     // 拇指旋转: 中间位置
            POS_MIN, // 食指: 伸直
            POS_MIN, // 中指: 伸直
            900,     // 无名指: 弯曲
            900      // 小指: 弯曲
        }};

        // 布: 所有手指伸直张开
        gesture_positions_["paper"] = {{
            POS_MIN, // 拇指弯曲: 伸直
            200,     // 拇指旋转: 张开角度
            POS_MIN, // 食指: 伸直
            POS_MIN, // 中指: 伸直
            POS_MIN, // 无名指: 伸直
            POS_MIN  // 小指: 伸直
        }};

        RCLCPP_INFO(this->get_logger(), "手势位置已初始化 (位置范围: 1-1000)");
    }

    /**
     * @brief 手势控制服务回调函数
     */
    void gestureCommandCallback(
        const std::shared_ptr<GestureCommand::Request> request,
        std::shared_ptr<GestureCommand::Response> response)
    {
        std::string gesture = request->gesture;

        // 转换为小写
        std::transform(gesture.begin(), gesture.end(), gesture.begin(),
                       [](unsigned char c) { return std::tolower(c); });

        RCLCPP_INFO(this->get_logger(), "接收到手势命令: %s", gesture.c_str());

        // 检查手势是否存在
        if (gesture_positions_.find(gesture) == gesture_positions_.end())
        {
            response->success = false;
            response->message = "未知手势: '" + gesture + "'. 支持的手势: ok, rock, scissors, paper";
            RCLCPP_WARN(this->get_logger(), "%s", response->message.c_str());
            return;
        }

        // 执行手势
        bool result = executeGesture(gesture);

        response->success = result;
        response->message = result ? "手势 '" + gesture + "' 执行成功" : "手势 '" + gesture + "' 执行失败";

        if (result)
        {
            RCLCPP_INFO(this->get_logger(), "%s", response->message.c_str());
        }
        else
        {
            RCLCPP_ERROR(this->get_logger(), "%s", response->message.c_str());
        }
    }

    /**
     * @brief 电机状态回调函数
     */
    void statusCallback(const brainco_hand_msgs::msg::MotorStatus::SharedPtr msg)
    {
        current_status_ = msg;
    }

    /**
     * @brief 执行手势 - 通过Topic发布控制命令
     */
    bool executeGesture(const std::string &gesture)
    {
        // 创建消息
        auto msg = brainco_hand_msgs::msg::SetMotorMulti();
        msg.mode = static_cast<uint8_t>(control_mode_);  // 位置模式 = 1

        // 获取手势位置
        const GesturePositions &pos = gesture_positions_[gesture];

        // 设置各手指位置
        for (int i = 0; i < MOTOR_COUNT; i++)
        {
            msg.positions[i] = pos[i];
            msg.speeds[i] = 0;      // 速度 0 表示使用默认速度
            msg.currents[i] = 0;
            msg.pwms[i] = 0;
            msg.durations[i] = 0;
        }

        RCLCPP_INFO(this->get_logger(), "正在执行手势: %s", gesture.c_str());
        RCLCPP_DEBUG(this->get_logger(),
                     "位置: 拇指弯曲=%u, 拇指旋转=%u, 食指=%u, 中指=%u, 无名指=%u, 小指=%u",
                     pos[THUMB_FLEX], pos[THUMB_ROTATE], pos[INDEX],
                     pos[MIDDLE], pos[RING], pos[PINKY]);

        // 发布控制命令
        motor_pub_->publish(msg);

        return true;
    }

    /**
     * @brief 打印当前电机状态
     */
    void printCurrentStatus()
    {
        if (current_status_)
        {
            RCLCPP_INFO(this->get_logger(), "当前电机状态:");
            const char* finger_names[] = {"拇指弯曲", "拇指旋转", "食指", "中指", "无名指", "小指"};
            for (int i = 0; i < MOTOR_COUNT; i++)
            {
                RCLCPP_INFO(this->get_logger(),
                            "  %s: 位置=%u, 速度=%d, 电流=%d, 状态=%u",
                            finger_names[i],
                            current_status_->positions[i],
                            current_status_->speeds[i],
                            current_status_->currents[i],
                            current_status_->states[i]);
            }
        }
    }
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<HandGestureControl>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}