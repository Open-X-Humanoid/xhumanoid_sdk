# 喇叭播放示例 (Speaker Play Demo)

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

基于 ROS2 的喇叭播放示例节点，通过调用 `/intelligent_interaction/tts/play` 服务实现文本/文件/URL播报。

提供两个版本：
- **Python版本**: `speaker_play_demo_py`
- **C++版本**: `speaker_play_demo_cpp`

## 功能特性

- 通过 TtsService 播放文本（TTS合成）
- 播放本地音频文件
- 播放远端音频URL
- 停止当前播报
- 查询播报状态（idle / playing）
- 提供命令行交互界面

## 依赖

- ROS2 (Jazzy)
- interaction_msgs（智能交互服务消息定义）
- rclcpp / rclpy

## 目录结构

```
speaker_play_demo/
├── README.md
├── python/                              # Python版本 (包名: speaker_play_demo_py)
│   ├── package.xml
│   ├── setup.py
│   ├── setup.cfg
│   ├── resource/
│   │   └── speaker_play_demo_py
│   ├── launch/
│   │   └── speaker_play_demo.launch.py
│   └── speaker_play_demo/
│       ├── __init__.py
│       └── speaker_play_demo_node.py
└── cpp/                                 # C++版本 (包名: speaker_play_demo_cpp)
    └── speaker_play_demo/
        ├── CMakeLists.txt
        ├── package.xml
        ├── launch/
        │   └── speaker_play_demo.launch.py
        └── src/
            └── speaker_play_demo_node.cpp
```

## 编译

### Python版本

```bash
cd ~/xos
colcon build --packages-select speaker_play_demo_py
source setup.bash
```

### C++版本

```bash
cd ~/xos
colcon build --packages-select speaker_play_demo_cpp
source setup.bash
```

## 使用方法

### 1. 交互模式

```bash
# Python版本
ros2 launch speaker_play_demo_py speaker_play_demo.launch.py

# C++版本
ros2 launch speaker_play_demo_cpp speaker_play_demo.launch.py
```

交互命令：
```
========================================
Speaker Play Demo - Commands:
  text <content>  - Play text via TTS
  play <path>     - Play audio file
  url <url>       - Play audio from URL
  stop            - Stop playback
  status          - Query playback status
  help            - Show this help
  quit            - Exit program
========================================
```

### 2. 自动播放模式

```bash
ros2 launch speaker_play_demo_py speaker_play_demo.launch.py \
    auto_play_on_start:=true \
    default_text:="你好，我是天工"
```

## 参数说明

| 参数名 | 默认值 | 说明 |
|--------|--------|------|
| `default_text` | `你好，我是天工机器人。` | 默认播放文本 |
| `default_audio_path` | `/tmp/test.wav` | 默认音频文件路径 |
| `auto_play_on_start` | `false` | 启动时自动播放 |

## 服务接口

### 调用的服务

| 服务名 | 类型 | 说明 |
|--------|------|------|
| `/intelligent_interaction/tts/play` | `interaction_msgs/srv/TtsService` | TTS播报服务 |

### TtsService 请求/响应

```
# Request
string text     # 文本 / 文件绝对路径 / URL；cmd=query 时无效
string type     # 资源类型：text / file / url
string cmd      # 指令：append（排队播报）/ stop（停止）/ query（查询）
---
# Response
bool   success  # 是否成功
string status   # query 时返回 "idle" / "playing" / "none"
```

## 验证

可直接使用命令行调用服务：

```bash
# 播报文本
ros2 service call /intelligent_interaction/tts/play \
    interaction_msgs/srv/TtsService \
    "{text: '你好我是天工', type: 'text', cmd: 'append'}"

# 停止播报
ros2 service call /intelligent_interaction/tts/play \
    interaction_msgs/srv/TtsService \
    "{text: '', type: 'text', cmd: 'stop'}"

# 查询状态
ros2 service call /intelligent_interaction/tts/play \
    interaction_msgs/srv/TtsService \
    "{text: '', type: 'text', cmd: 'query'}"
```

## 输出示例

```
[INFO] [speaker_play_demo_node]: Speaker Play Demo Node initialized
[INFO] [speaker_play_demo_node]:   Default text: 你好，我是天工机器人。
[INFO] [speaker_play_demo_node]: TTS service is ready
[INFO] [speaker_play_demo_node]: TTS call: text="你好世界", type=text, cmd=append
[INFO] [speaker_play_demo_node]: TTS success. Status: none
```

## 相关链接

- 消息定义：`interaction_msgs`
- 流式音频播放：通过 `/intelligent_interaction/audio/stream` 话题
- 音色切换：通过 `/intelligent_interaction/tts/update_voice_id` 服务
