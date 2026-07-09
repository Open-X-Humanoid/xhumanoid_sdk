# 播放文字示例

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

这是一个 ROS2 示例包，演示如何调用 `/intelligent_interaction/tts/play` 服务实现文字转语音播放。

提供两个版本：
- **Python版本**: `play_text_demo_py`
- **C++版本**: `play_text_demo_cpp`

## 功能

通过调用 `/intelligent_interaction/tts/play` 服务（`interaction_msgs/srv/TtsService`），支持三种播报方式：
- **文本播报**：将文字合成语音播放（`type: text`）
- **本地音频播放**：播放本地音频文件（`type: file`）
- **远端URL播放**：播放远端音频URL（`type: url`）

支持的控制指令（`cmd`参数）：
- `append`：排队播报（默认）
- `stop`：打断当前播报
- `query`：查询当前播报状态

### 参数

| 参数 | 默认值 | 描述 |
|------|--------|------|
| `text` | `你好，我是天工机器人，很高兴认识你。` | 要播放的文本内容 / 文件路径 / URL |
| `type` | `text` | 资源类型：`text` / `file` / `url` |
| `cmd` | `append` | 指令：`append` / `stop` / `query` |

## 编译

### Python版本

```bash
source ~/xos/setup.bash
colcon build --packages-select play_text_demo_py
```

### C++版本

```bash
source ~/xos/setup.bash
colcon build --packages-select play_text_demo_cpp
```

## 运行

### 方式一：使用 launch 文件

#### Python版本

```bash
source ~/xos/setup.bash
ros2 launch play_text_demo_py run.launch.py
```

#### C++版本

```bash
source ~/xos/setup.bash
ros2 launch play_text_demo_cpp run.launch.py
```

### 方式二：直接运行可执行文件

```bash
# Python版本
ros2 run play_text_demo_py play_text_node

# C++版本
ros2 run play_text_demo_cpp play_text_node
```

### 自定义播放

```bash
# 播放自定义文本
ros2 run play_text_demo_py play_text_node --ros-args \
    -p text:="欢迎使用语音播放功能" -p type:=text -p cmd:=append

# 播放本地音频文件
ros2 run play_text_demo_py play_text_node --ros-args \
    -p text:="/path/to/audio.wav" -p type:=file -p cmd:=append

# 查询播报状态
ros2 run play_text_demo_py play_text_node --ros-args \
    -p cmd:=query
```

## 验证

可以直接使用命令行调用服务：

```bash
# 排队播报文本
ros2 service call /intelligent_interaction/tts/play \
    interaction_msgs/srv/TtsService \
    "{text: '你好我是天工', type: 'text', cmd: 'append'}"

# 停止当前播报
ros2 service call /intelligent_interaction/tts/play \
    interaction_msgs/srv/TtsService \
    "{text: '', type: 'text', cmd: 'stop'}"

# 查询播报状态
ros2 service call /intelligent_interaction/tts/play \
    interaction_msgs/srv/TtsService \
    "{text: '', type: 'text', cmd: 'query'}"
```

## 服务接口

`TtsService` 服务消息格式（`interaction_msgs/srv/TtsService`）：

```
# Request
string text     # 文本 / 本地音频文件绝对路径 / URL；cmd=query 时本字段无效
string type     # 资源类型：text / file / url；cmd=query 时本字段无效
string cmd      # 指令：append / stop / query
---
# Response
bool   success  # 指令是否成功执行
string status   # cmd=query 时返回："idle" / "playing" / "none"
```

## 目录结构

```
3.play_text_demo/
├── README.md
├── python/                              # Python版本 (play_text_demo_py)
│   ├── package.xml
│   ├── setup.py
│   ├── setup.cfg
│   ├── resource/
│   │   └── play_text_demo_py
│   ├── play_text_demo/
│   │   ├── __init__.py
│   │   └── play_text_node.py
│   └── launch/
│       └── run.launch.py
└── cpp/                                 # C++版本 (play_text_demo_cpp)
    └── play_text_demo/
        ├── CMakeLists.txt
        ├── package.xml
        ├── src/
        │   └── play_text_node.cpp
        └── launch/
            └── run.launch.py
```

## 依赖

- `rclcpp` / `rclpy`: ROS2 客户端库
- `interaction_msgs`: 智能交互服务消息定义
