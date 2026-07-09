# 语音识别 Demo

> **适用平台**: 具身天工3.0 (Thor)
>
> 本示例需要在 **具身天工3.0 机器人本体** 上进行开发和运行，开发环境为 **Ubuntu 24.04**，当前不支持 Mac 和 Windows。
>
> ```bash
> # 登录算力主机（通过网线直连时需配置本机41网段网卡 MTU 为 9000）
> ssh nvidia@192.168.41.2
>
> # 注意：必须使用 nvidia 用户启动 ROS2 节点，否则消息无法通信
> source ~/xos/setup.bash
> ```

本示例演示如何通过订阅 `/lyre/voice_activity` 话题获取语音活动事件，包括 ASR 识别结果、关键词唤醒、人脸唤醒、VAD 事件等。

提供两个版本：
- **Python版本**: `speech_recognition_demo_py`
- **C++版本**: `speech_recognition_demo_cpp`

## 功能说明

订阅统一的语音活动话题：

| 话题名称 | 消息类型 | 说明 |
|---------|---------|------|
| `/lyre/voice_activity` | `lyre_msgs/msg/LyreVoiceActivity` | 语音活动事件（JSON格式） |

### 支持的事件类型

| eventType | 事件名称 | 说明 |
|-----------|----------|------|
| 1 | ASR结果 | 语音识别到的文本内容 |
| 4 | 关键词唤醒 | 检测到唤醒关键词，包含声源角度 |
| 5 | 退出对话 | 对话结束事件 |
| 6 | VAD事件 | 语音端点检测（arg1=0: 语音开始, arg1=2: 语音结束） |
| 20 | 人脸识别唤醒 | 通过人脸识别触发唤醒 |

## 前置条件

lyre 的启动通过 proc_manager 进程管理，正常启动约30s后 lyre 即可就绪。

使用遥控器操作：
- 上拨F键 → 长按A：开启语音对话
- 再次长按A：关闭对话

## 编译

### Python版本

```bash
cd ~/xos
colcon build --packages-select speech_recognition_demo_py
source setup.bash
```

### C++版本

```bash
cd ~/xos
colcon build --packages-select speech_recognition_demo_cpp
source setup.bash
```

## 运行

### Python版本

```bash
ros2 launch speech_recognition_demo_py run.launch.py
```

### C++版本

```bash
ros2 launch speech_recognition_demo_cpp run.launch.py
```

## 验证

可以直接使用命令行监听话题：

```bash
ros2 topic echo /lyre/voice_activity
```

## 目录结构

```
4.speech_recognition_demo/
├── README.md
├── python/                              # Python版本 (speech_recognition_demo_py)
│   ├── package.xml
│   ├── setup.py
│   ├── setup.cfg
│   ├── resource/
│   │   └── speech_recognition_demo_py
│   ├── speech_recognition_demo/
│   │   ├── __init__.py
│   │   └── speech_recognition_node.py
│   └── launch/
│       └── run.launch.py
└── cpp/                                 # C++版本 (speech_recognition_demo_cpp)
    └── speech_recognition_demo/
        ├── CMakeLists.txt
        ├── package.xml
        ├── src/
        │   └── speech_recognition_node.cpp
        └── launch/
            └── run.launch.py
```

## 消息格式

`LyreVoiceActivity` 消息内容为 JSON 字符串，示例：

### ASR识别结果 (eventType: 1)
```json
{
  "content": {
    "eventType": 1,
    "result": {"text": {"ws": [{"cw": [{"w": "今天的天气"}]}]}}
  },
  "timestamp": "1774592141.073",
  "traceId": "xxx",
  "type": "aiui_event"
}
```

### 关键词唤醒 (eventType: 4)
```json
{
  "content": {
    "eventType": 4,
    "result": {"ivw": {"angle": 93}}
  },
  "type": "aiui_event"
}
```

## 输出示例

```
[INFO] [speech_recognition_demo]: Subscribed to: /lyre/voice_activity
[INFO] [speech_recognition_demo]: [唤醒] 人脸识别唤醒 (traceId=a044418b-...)
[INFO] [speech_recognition_demo]: [唤醒] 关键词唤醒，角度: 93° (traceId=2f02cf62-...)
[INFO] [speech_recognition_demo]: [VAD] 检测到语音开始 (traceId=61332d9e-...)
[INFO] [speech_recognition_demo]: [ASR] 识别结果: "今天的天气" (traceId=53583960-...)
[INFO] [speech_recognition_demo]: [VAD] 检测到语音结束 (traceId=c622a4f3-...)
[INFO] [speech_recognition_demo]: [对话] 退出对话 (traceId=6710113f-...)
```

## 依赖

- `rclcpp` / `rclpy`: ROS2 客户端库
- `lyre_msgs`: lyre 语音消息定义
