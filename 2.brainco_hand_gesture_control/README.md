# 灵巧手手势控制节点（选配）

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

基于 `brainco_hand_msgs` 消息定义的ROS2节点,通过位置模式控制灵巧手实现预设手势。

提供两个版本：
- **Python版本**: `brainco_hand_gesture_control_py`
- **C++版本**: `brainco_hand_gesture_control_cpp`

## 功能

支持以下手势:
- **OK手势** (`ok`): 大拇指和食指捏合,其他手指伸直
- **石头** (`rock`): 所有手指弯曲握拳
- **剪刀** (`scissors`): 食指和中指伸直,其他手指弯曲
- **布** (`paper`): 所有手指伸直张开

## 目录结构

```
2.brainco_hand_gesture_control/
├── README.md
├── brainco_hand_gesture_interfaces/      # 服务消息定义包
│   ├── CMakeLists.txt
│   ├── package.xml
│   └── srv/
│       └── GestureCommand.srv
├── python/                              # Python版本 (brainco_hand_gesture_control_py)
│   ├── package.xml
│   ├── setup.py
│   ├── setup.cfg
│   ├── resource/
│   │   └── brainco_hand_gesture_control_py
│   ├── brainco_hand_gesture_control/
│   │   ├── __init__.py
│   │   └── hand_gesture_control.py
│   └── launch/
│       └── hand_gesture_control.launch.py
└── cpp/                                 # C++版本 (brainco_hand_gesture_control_cpp)
    └── brainco_hand_gesture_control/
        ├── CMakeLists.txt
        ├── package.xml
        ├── README.md
        ├── src/
        │   └── hand_gesture_control.cpp
        └── launch/
            └── hand_gesture_control.launch.py
```

## 依赖

- ROS2 (Jazzy)
- `brainco_hand_msgs` 包
- `brainco_hand_gesture_interfaces` 包 (服务消息定义)

## 编译

### 首先编译消息包

```bash
cd ~/xos
colcon build --packages-select brainco_hand_msgs brainco_hand_gesture_interfaces
source setup.bash
```

### Python版本

```bash
cd ~/xos
colcon build --packages-select brainco_hand_gesture_control_py
source setup.bash
```

### C++版本

```bash
cd ~/xos
colcon build --packages-select brainco_hand_gesture_control_cpp
source setup.bash
```

## 使用方法

### 1. 启动节点

#### Python版本

```bash
# 默认控制右手
ros2 launch brainco_hand_gesture_control_py hand_gesture_control.launch.py

# 控制左手
ros2 launch brainco_hand_gesture_control_py hand_gesture_control.launch.py hand_prefix:=left_hand
```

#### C++版本

```bash
# 默认控制右手
ros2 launch brainco_hand_gesture_control_cpp hand_gesture_control.launch.py

# 控制左手
ros2 launch brainco_hand_gesture_control_cpp hand_gesture_control.launch.py hand_prefix:=left_hand
```

### 2. 调用服务触发手势

```bash
# OK手势
ros2 service call /gesture_command brainco_hand_gesture_interfaces/srv/GestureCommand "{gesture: 'ok'}"

# 石头
ros2 service call /gesture_command brainco_hand_gesture_interfaces/srv/GestureCommand "{gesture: 'rock'}"

# 剪刀
ros2 service call /gesture_command brainco_hand_gesture_interfaces/srv/GestureCommand "{gesture: 'scissors'}"

# 布
ros2 service call /gesture_command brainco_hand_gesture_interfaces/srv/GestureCommand "{gesture: 'paper'}"
```

### 3. 查看状态

```bash
# 查看右手电机状态
ros2 topic echo /right_hand/motor_status

# 查看左手电机状态
ros2 topic echo /left_hand/motor_status
```

## 参数

| 参数 | 默认值 | 描述 |
|------|--------|------|
| `hand_prefix` | `right_hand` | 手的前缀: `right_hand` 或 `left_hand` |
| `control_mode` | `1` | 控制模式: 1=位置, 2=速度, 3=电流, 4=PWM, 5=位置+时间, 6=位置+速度 |

## 服务接口

### 手势控制服务

| 服务名 | 消息类型 | 描述 |
|--------|----------|------|
| `/gesture_command` | brainco_hand_gesture_interfaces/srv/GestureCommand | 触发指定手势 |

**请求字段:**
- `gesture` (string): 手势名称, 支持: `ok`, `rock`, `scissors`, `paper`

**响应字段:**
- `success` (bool): 执行结果
- `message` (string): 结果信息

## 话题接口

### 订阅话题

| 话题 | 消息类型 | 描述 |
|------|----------|------|
| `/{hand_prefix}/motor_status` | brainco_hand_msgs/MotorStatus | 电机状态反馈 |

### 发布话题

| 话题 | 消息类型 | 描述 |
|------|----------|------|
| `/{hand_prefix}/set_motor_multi` | brainco_hand_msgs/SetMotorMulti | 电机控制命令 |

## 手指索引

灵巧手有6个电机,对应以下手指:

| 索引 | 手指 | 描述 |
|------|------|------|
| 0 | 拇指弯曲 (Thumb Flex) | 控制拇指弯曲程度 |
| 1 | 拇指旋转 (Thumb Rotate) | 控制拇指旋转角度 |
| 2 | 食指 (Index) | |
| 3 | 中指 (Middle) | |
| 4 | 无名指 (Ring) | |
| 5 | 小指 (Pinky) | |

## 位置范围

位置值范围: **1 ~ 1000**
- `1`: 完全伸直
- `1000`: 完全弯曲

## 控制模式

| 模式 | 值 | 描述 |
|------|-----|------|
| 位置 | 1 | 按位置控制 |
| 速度 | 2 | 按速度控制 |
| 电流 | 3 | 按电流控制 |
| PWM | 4 | 按PWM控制 |
| 位置+时间 | 5 | 位置控制,带期望时间 |
| 位置+速度 | 6 | 位置控制,带期望速度 |

## 位置校准

**重要**: 代码中的位置值是示例值,需要根据实际灵巧手硬件进行校准。

请根据实际硬件调整源代码中的 `initGesturePositions()` 函数中的位置值。

## 许可证

Apache-2.0