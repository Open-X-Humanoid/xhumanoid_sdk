# 强脑手触觉反馈显示（选配） (BrainCo Hand Touch Display)

> **适用平台**: 具身天工3.0 (Thor) | **选配功能** - 需要搭配强脑灵巧手使用
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

基于 ROS2 的强脑灵巧手触觉反馈状态实时打印节点，支持同时显示左右手五指的法向力、切向力、切向力方向、接近值和传感器状态。

提供两个版本：
- **Python版本**: `brainco_hand_touch_display_py`
- **C++版本**: `brainco_hand_touch_display_cpp`

## 功能特性

- 实时打印左右手触觉传感器数据
- 支持独立启用/禁用左手或右手
- 可调节打印间隔
- 格式化表格输出，包含以下数据：
  - **法向力** (Normal Force)：单位 N，精度 0.01N
  - **切向力** (Tangential Force)：单位 N，精度 0.01N
  - **切向力方向** (Direction)：单位 度（0~359°），无接触时显示 N/A
  - **接近值** (Proximity)：接近觉感应值
  - **传感器状态** (Status)：OK / ERR / COMM

## 依赖

- ROS2 (Humble/Jazzy)
- brainco_hand_msgs

## 前提条件

确保强脑灵巧手已在诊断界面中配置并启用，且机器人系统已启动。

## 目录结构

```
12.brainco_hand_touch_display/
├── README.md
├── python/                                      # Python版本
│   ├── package.xml
│   ├── setup.py
│   ├── setup.cfg
│   ├── resource/
│   │   └── brainco_hand_touch_display_py
│   ├── launch/
│   │   └── touch_display.launch.py
│   └── brainco_hand_touch_display/
│       ├── __init__.py
│       └── touch_display_node.py
└── cpp/                                         # C++版本
    └── brainco_hand_touch_display/
        ├── CMakeLists.txt
        ├── package.xml
        ├── launch/
        │   └── touch_display.launch.py
        └── src/
            └── touch_display_node.cpp
```

## 编译

### Python版本

```bash
source ~/xos/setup.bash
colcon build --packages-select brainco_hand_touch_display_py
```

### C++版本

```bash
source ~/xos/setup.bash
colcon build --packages-select brainco_hand_touch_display_cpp
```

## 使用方法

### 1. 同时显示左右手（默认）

#### Python版本

```bash
source ~/xos/setup.bash
ros2 launch brainco_hand_touch_display_py touch_display.launch.py
```

#### C++版本

```bash
source ~/xos/setup.bash
ros2 launch brainco_hand_touch_display_cpp touch_display.launch.py
```

### 2. 仅显示右手

```bash
ros2 launch brainco_hand_touch_display_py touch_display.launch.py enable_left:=false
```

### 3. 仅显示左手

```bash
ros2 launch brainco_hand_touch_display_py touch_display.launch.py enable_right:=false
```

### 4. 调整打印间隔（0.5秒）

```bash
ros2 launch brainco_hand_touch_display_py touch_display.launch.py print_interval:=0.5
```

### 5. 直接运行节点

```bash
source ~/xos/setup.bash
ros2 run brainco_hand_touch_display_py touch_display_node
ros2 run brainco_hand_touch_display_cpp touch_display_node
```

## 参数说明

| 参数名 | 默认值 | 说明 |
|--------|--------|------|
| `enable_left` | `true` | 启用左手触觉显示 |
| `enable_right` | `true` | 启用右手触觉显示 |
| `print_interval` | `1.0` | 打印间隔（秒） |

## 订阅话题

| 话题名 | 类型 | 说明 |
|--------|------|------|
| `/left_hand/touch_status` | `brainco_hand_msgs/msg/TouchStatus` | 左手触觉反馈 |
| `/right_hand/touch_status` | `brainco_hand_msgs/msg/TouchStatus` | 右手触觉反馈 |

## 消息格式

### TouchStatus

```
TouchStatusItem[5] data    # 5个手指的触觉数据（拇指、食指、中指、无名指、小指）
```

### TouchStatusItem

```
uint16 normal_force1          # 法向力，单位 0.01N
uint16 tangential_force1      # 切向力，单位 0.01N
uint16 tangential_direction1  # 切向力方向，0~359°，65535表示无效
uint32 self_proximity1        # 接近值
uint16 status                 # 状态：低8位 0=正常，1=数据异常，2=通信异常
```

## 输出示例

```
======================================================================
  [Left Hand]
  Finger   | Normal(N)  | Tangential(N)  | Direction(°)  | Proximity  | Status
  --------------------------------------------------------------------
  Thumb    |       0.52 |           0.13 |           120 |       1500 |     OK
  Index    |       1.20 |           0.45 |            85 |       2300 |     OK
  Middle   |       0.00 |           0.00 |           N/A |        100 |     OK
  Ring     |       0.00 |           0.00 |           N/A |         50 |     OK
  Little   |       0.00 |           0.00 |           N/A |         30 |     OK
  [Right Hand]
  Finger   | Normal(N)  | Tangential(N)  | Direction(°)  | Proximity  | Status
  --------------------------------------------------------------------
  Thumb    |       0.80 |           0.20 |            90 |       1800 |     OK
  Index    |       0.00 |           0.00 |           N/A |        200 |     OK
  Middle   |       0.00 |           0.00 |           N/A |        150 |     OK
  Ring     |       0.00 |           0.00 |           N/A |         80 |     OK
  Little   |       0.00 |           0.00 |           N/A |         40 |     OK
======================================================================
```

## 传感器状态说明

| 状态 | 说明 |
|------|------|
| OK | 数据正常 |
| ERR | 数据异常（高8位包含详细错误标志） |
| COMM | 与触觉传感器通信异常 |

### 错误标志位（高8位）

| Bit | 说明 |
|-----|------|
| Bit0 | 原始值错误 |
| Bit1 | 原始值长时间未更新 |
| Bit2 | 触发超时 |

## 验证

在另一个终端中验证话题数据：

```bash
source ~/xos/setup.bash
ros2 topic echo /left_hand/touch_status
ros2 topic echo /right_hand/touch_status
```
