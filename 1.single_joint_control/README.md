# Single Joint Control Example

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

这是一个 ROS2 示例包，演示如何通过 `/arm/cmd` 话题控制单个关节电机，包含 **位置模式** 和 **力位混合模式** 两种控制方式。

实现效果：通过控制21号关节（右肩关节俯仰）完成以下动作序列：
1. **位置模式**：右臂抬起（-1.588 rad） -> 放下（0.0 rad）
2. **力位混合模式**：右臂抬起（-1.588 rad） -> 放下（0.0 rad）

提供两个版本：
- **Python版本**: `single_joint_control_py`
- **C++版本**: `single_joint_control_cpp`

## 控制模式说明

### 位置模式（mode=0）

通过指定目标位置、速度和最大电流来控制关节运动，适用于需要精确到达目标位置的场景。

关键参数：
- `pos`: 目标位置（rad）
- `spd`: 期望速度（rad/s）
- `cur`: 最大电流（A）

### 力位混合模式（mode=1）

通过 PD 控制器结合前馈力矩来控制关节，适用于需要柔顺控制或力控制的场景。

关键参数：
- `kp`: 比例增益
- `kd`: 微分增益
- `pos`: 期望位置（rad）
- `spd`: 期望速度（rad/s）
- `tor`: 前馈力矩（Nm）

控制律：`τ = kp * (pos_target - pos_current) + kd * (spd_target - spd_current) + tor`

## 编译

### Python版本

```bash
source ~/xos/setup.bash
colcon build --packages-select single_joint_control_py
```

### C++版本

```bash
source ~/xos/setup.bash
colcon build --packages-select single_joint_control_cpp
```

## 运行

### 方式一：使用 launch 文件

#### Python版本

```bash
source ~/xos/setup.bash
ros2 launch single_joint_control_py run.launch.py
```

#### C++版本

```bash
source ~/xos/setup.bash
ros2 launch single_joint_control_cpp run.launch.py
```

### 方式二：直接运行可执行文件

#### Python版本

```bash
source ~/xos/setup.bash
ros2 run single_joint_control_py cmd_publisher
```

#### C++版本

```bash
source ~/xos/setup.bash
ros2 run single_joint_control_cpp cmd_publisher
```

## 验证

在另一个终端中，你可以验证消息是否正确发布：

```bash
source ~/xos/setup.bash
ros2 topic echo /arm/cmd
```

或者使用命令行发送单次命令：

```bash
# 位置模式 (mode=0)：右臂关节21移动到 -1.588 rad
ros2 topic pub --once /arm/cmd ros2_bridge_msgs/msg/ArmCtrl "{
  header: {stamp: {sec: 0, nanosec: 0}, frame_id: 'arm'},
  mode: 0,
  label: 0,
  ctrl: [
    {name: 21, pos: -1.588, spd: 0.3, cur: 10.0}
  ]
}"

# 力位混合模式 (mode=1)：右臂关节21移动到 0.5 rad
ros2 topic pub --once /arm/cmd ros2_bridge_msgs/msg/ArmCtrl "{
  header: {stamp: {sec: 0, nanosec: 0}, frame_id: 'arm'},
  mode: 1,
  label: 0,
  ctrl: [
    {name: 21, kp: 50.0, kd: 2.0, pos: 0.5, spd: 0, tor: 0}
  ]
}"
```

## 目录结构

```
1.single_joint_control/
├── README.md
├── python/                              # Python版本 (single_joint_control_py)
│   ├── package.xml
│   ├── setup.py
│   ├── setup.cfg
│   ├── resource/
│   │   └── single_joint_control_py
│   ├── single_joint_control/
│   │   ├── __init__.py
│   │   └── cmd_publisher.py
│   └── launch/
│       └── run.launch.py
└── cpp/                                 # C++版本 (single_joint_control_cpp)
    └── single_joint_control/
        ├── CMakeLists.txt
        ├── package.xml
        ├── src/
        │   └── cmd_publisher.cpp
        └── launch/
            └── run.launch.py
```

## 消息格式

### ArmCtrl 控制消息

```
std_msgs/Header header          # 消息头（时间戳和坐标系）
uint8 mode                      # 控制模式: 0=位置模式, 1=力位混合模式, 2=速度模式, 3=标零模式, 4=距离模式, 5=电流模式
uint8 label                     # 调用标签
uint8 reserved                  # 保留字段
ros2_bridge_msgs/MotorCtrl[] ctrl  # 电机控制命令数组
```

### MotorCtrl 电机控制消息

```
uint16 name                     # 电机名称/ID
float64 kp                      # 比例增益（力位混合模式使用）
float64 kd                      # 微分增益（力位混合模式使用）
float64 pos                     # 期望位置 (rad)（位置模式和力位混合模式使用）
float64 spd                     # 期望速度 (rad/s)（位置模式、速度模式和力位混合模式使用）
float64 tor                     # 前馈力矩（力位混合模式使用）
float64 cur                     # 最大电流 (A)（位置模式和速度模式使用）
```

### RobotState 状态反馈

通过订阅 `/robot_state` 话题获取关节状态，其中 `arm.status` 包含手臂各关节的位置、速度、电流、温度等信息。
