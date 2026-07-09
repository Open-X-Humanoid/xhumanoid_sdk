# MIC录音示例 (Microphone Record Demo)

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

基于 ROS2 的麦克风录音示例节点，通过 lyre 音频流接口获取拾音器原始音频并保存为 WAV 文件。

提供两个版本：
- **Python版本**: `mic_record_demo_py`
- **C++版本**: `mic_record_demo_cpp`

## 功能特性

- 通过 `/lyre/audio_control` 服务开启/关闭拾音器音频流
- 订阅 `/lyre/audio_stream` 话题接收原始音频数据
- 自动检测音频格式（采样率、声道数、位深度）
- 保存为标准 WAV 格式文件
- 提供开始/停止录音服务接口
- 发布录音状态话题
- 支持最大录音时长限制

## 依赖

- ROS2 (Jazzy)
- lyre_msgs（音频消息和服务定义）
- rclcpp, std_msgs, std_srvs

## 目录结构

```
10.mic_record_demo/
├── README.md
├── python/                              # Python版本 (包名: mic_record_demo_py)
│   ├── package.xml
│   ├── setup.py
│   ├── setup.cfg
│   ├── resource/
│   │   └── mic_record_demo_py
│   ├── launch/
│   │   └── mic_record_demo.launch.py
│   └── mic_record_demo/
│       ├── __init__.py
│       └── mic_record_demo_node.py
└── cpp/                                 # C++版本 (包名: mic_record_demo_cpp)
    └── mic_record_demo/
        ├── CMakeLists.txt
        ├── package.xml
        ├── launch/
        │   └── mic_record_demo.launch.py
        └── src/
            └── mic_record_demo_node.cpp
```

## 编译

### Python版本

```bash
cd ~/xos
colcon build --packages-select mic_record_demo_py
source setup.bash
```

### C++版本

```bash
cd ~/xos
colcon build --packages-select mic_record_demo_cpp
source setup.bash
```

## 使用方法

### 1. 启动节点

```bash
# Python版本
ros2 launch mic_record_demo_py mic_record_demo.launch.py

# C++版本
ros2 launch mic_record_demo_cpp mic_record_demo.launch.py
```

#### 自定义参数

```bash
ros2 launch mic_record_demo_py mic_record_demo.launch.py \
    output_dir:=/tmp/recordings \
    max_duration:=30
```

### 2. 开始录音

```bash
ros2 service call /mic_record/start std_srvs/srv/Empty
```

节点会自动调用 `/lyre/audio_control` 开启音频流，并开始接收 `/lyre/audio_stream` 数据。

### 3. 停止录音

```bash
ros2 service call /mic_record/stop std_srvs/srv/Empty
```

停止后自动保存 WAV 文件并关闭音频流。

### 4. 查看录音状态

```bash
ros2 topic echo /mic_record/is_recording
ros2 topic echo /mic_record/status
```

## 参数说明

| 参数名 | 默认值 | 说明 |
|--------|--------|------|
| `output_dir` | `/tmp` | 录音文件输出目录 |
| `max_duration` | `60` | 最大录音时长(秒)，0=无限制 |

## 音频接口

### 使用的服务

| 服务名 | 类型 | 说明 |
|--------|------|------|
| `/lyre/audio_control` | `lyre_msgs/srv/AudioControl` | 开启/关闭拾音器音频流 |

```
# AudioControl.srv
bool enable     # true: 启动, false: 停止
---
bool success    # true: 成功, false: 失败
string message  # 返回信息
```

### 订阅的话题

| 话题名 | 类型 | 说明 |
|--------|------|------|
| `/lyre/audio_stream` | `lyre_msgs/msg/AudioFrame` | 原始音频数据流 |

```
# AudioFrame.msg
uint32 sample_rate      # 采样率 (Hz)
uint8 channels          # 声道数 (1=单声道, 2=立体声)
uint8 bits_per_sample   # 位深度 (8/16/24/32)
uint32 sequence         # 帧序号
uint32 timestamp_sec    # 时间戳（秒）
uint32 timestamp_nsec   # 时间戳（纳秒）
uint8[] data            # 音频数据
```

### 提供的服务

| 服务名 | 类型 | 说明 |
|--------|------|------|
| `/mic_record/start` | `std_srvs/srv/Empty` | 开始录音 |
| `/mic_record/stop` | `std_srvs/srv/Empty` | 停止录音 |

### 发布的话题

| 话题名 | 类型 | 说明 |
|--------|------|------|
| `/mic_record/status` | `std_msgs/msg/String` | 录音状态事件 |
| `/mic_record/is_recording` | `std_msgs/msg/Bool` | 是否正在录音 |

## 输出文件

录音文件以 WAV 格式保存，文件名格式：
```
recording_YYYYMMDD_HHMMSS.wav
```

## 验证

可直接通过命令行控制音频流：

```bash
# 手动开启音频流
ros2 service call /lyre/audio_control lyre_msgs/srv/AudioControl "{enable: true}"

# 监听音频数据
ros2 topic echo /lyre/audio_stream

# 关闭音频流
ros2 service call /lyre/audio_control lyre_msgs/srv/AudioControl "{enable: false}"
```

## 输出示例

```
[INFO] [mic_record_demo_node]: Mic Record Demo Node initialized
[INFO] [mic_record_demo_node]:   Output directory: /tmp
[INFO] [mic_record_demo_node]:   Max duration: 60s
[INFO] [mic_record_demo_node]: Audio source: /lyre/audio_stream
[INFO] [mic_record_demo_node]: Audio control: /lyre/audio_control
[INFO] [mic_record_demo_node]: Recording started: /tmp/recording_20250319_143015.wav
[INFO] [mic_record_demo_node]: Audio format: 16000Hz, 1ch, 16bit
[INFO] [mic_record_demo_node]: Recording saved: /tmp/recording_20250319_143015.wav (960000 bytes, 600 frames)
```

## 相关链接

- 音频播放示例：`9.speaker_play_demo`
- 语音识别示例：`4.speech_recognition_demo`
- 音频消息定义：`lyre_msgs`
