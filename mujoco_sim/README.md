# mujoco_sim

基于 MuJoCo 的无头（headless）仿真节点，对外暴露与真机一致的 ROS 2 话题，
让 SDK 示例可以在没有机器人的情况下运行。一个节点（`sim_node`）同时仿真机器人手臂和挂在两个手腕上的灵巧手，
并可以通过浏览器查看场景。目前支持：

- `single_joint_control`：机器人手臂
- `brainco_hand_gesture_control`、`brainco_hand_touch_display`：灵巧手

> **仿真结果不等同于真机验证。** 模型动力学未经标定，只用于检查接口、流程和逻辑。
> 请勿将仿真中的增益、速度、时间直接用于真机。

## 功能范围

| 项目 | 状态 |
| --- | --- |
| 订阅 `/arm/cmd` (`ros2_bridge_msgs/ArmCtrl`) | mode 0（位置）、mode 1（力位混合） |
| 发布 `/robot_state` (`ros2_bridge_msgs/RobotState`) | 手臂关节状态（电机 ID 11–27）、IMU，100 Hz |
| 机体 | 骨盆固定在世界系（`fix_base:=true`），无平衡控制器 |
| 机器人模型 | 具身天工 3.0（tiangong3），来自官方 [xSIM_MUJOCO](https://github.com/Open-X-Humanoid/xSIM_MUJOCO) |
| 灵巧手 | 见下文「灵巧手」 |
| 浏览器查看 | 见下文「浏览器查看」，默认关闭 |
| 其他示例（点云、图像、GPS、TTS 等） | **未实现** |
| 仿真器本身的 C++ 版本、本地可视化窗口 | 未提供（仿真器只有 Python 版；SDK 的 C++ 示例可以直接连接它） |

mode 2–5 收到后只告警一次并忽略。

### 控制近似

- **mode 1**：`torque = kp·(pos − q) + kd·(spd − dq) + tor`，通过模型的 `motor_*` 力矩执行器输出，受 `ctrlrange`（±90 Nm）限幅。
- **mode 0**：目标位置以 `spd` rad/s 的速度限幅逼近 `pos`（`spd <= 0` 时直接跳到 `pos`），再用模型 `pos_*` 执行器的 kp/kv 做 PD 跟踪。`cur` 被忽略，因为模型没有电机电流模型。
- 未收到指令的关节以模型 PD 增益保持在 0 位。
- 模型使用理想力矩执行器，没有速度/电流限制，所以 mode 1 的动作比真机快很多（`single_joint_control` 的混合阶段约 0.3 s 完成）。

### 固定基座下的 IMU

MuJoCo 对固定在世界上的 body 加速度计输出 0。节点在 `fix_base` 下按
`R_imu^T · (0, 0, 9.81)` 合成静止时的重力反作用，因此静止 IMU 读数为 `az ≈ 9.81`。
欧拉角单位为度，角速度为 rad/s，加速度为 m/s²。

## 灵巧手

`sim_node` 默认在机器人的左右手腕（`wrist_roll_l_link`、`wrist_roll_r_link`）上各挂一只手，
手随手臂运动。参数 `with_hands:=false` 可以关闭。话题前缀为 `left_hand`、`right_hand`：

| 话题 | 类型 | 方向 |
| --- | --- | --- |
| `/<hand>/set_motor_multi` | `brainco_hand_msgs/SetMotorMulti` | 订阅 |
| `/<hand>/motor_status` | `brainco_hand_msgs/MotorStatus` | 发布，与 `/robot_state` 同频（默认 100 Hz） |
| `/<hand>/touch_status` | `brainco_hand_msgs/TouchStatus` | 发布，同上 |

- 6 个电机顺序与 SDK 一致：拇指弯曲、拇指旋转、食指、中指、无名指、小指，位置范围 1（伸直）到 1000（弯曲）。
- 只模拟位置模式（`mode == 1`），其他模式告警一次并忽略。`speeds/currents/pwms/durations` 被忽略。
  默认速度下 1→1000 约需 `hand_full_stroke_s`（默认 0.8 s）。
- 手模型是程序生成的简化胶囊模型（`hand_model.py`），不是 BrainCo 手的真实几何或动力学。
  `scene.py` 用 `MjSpec.attach` 把它接到手腕上，关节名带 `left_hand/`、`right_hand/` 前缀。
- 安装位置（腕坐标系 z 向下 0.149 m，手指朝下，掌心朝向身体）是按 tcp 网格长度估计的近似值，不是机械尺寸。
- 手的几何只与自己和测试横杆碰撞，不与机器人碰撞（碰撞位 2，机器人使用位 1）。
- 每只手下方有一根固定在世界系的横杆（`<hand>_test_bar`），握拳（`rock`）时手指碰到它，从而产生触觉读数；
  因此弯曲幅度大的手势到不了目标位置。横杆**不随手臂运动**，手臂动了之后手就碰不到它。
- 触觉只有法向力（单位 0.01 N，来自 MuJoCo `touch` 传感器），切向力和接近值为 0，方向为 65535（无效），状态为 0（正常）。
  力的大小没有标定，握拳时拇指可达十几牛。
- tiangong3 的 MJCF 通过 `actuatorgroupdisable` 关闭了执行器组 0、1、3，手的执行器因此放在组 2。

```bash
ros2 launch brainco_hand_gesture_control_py hand_gesture_control.launch.py   # 或 _cpp
ros2 service call /gesture_command brainco_hand_gesture_interfaces/srv/GestureCommand "{gesture: 'rock'}"
ros2 topic echo /right_hand/motor_status
```

## 浏览器查看

宿主机可能没有显示器和 GPU，所以不用 MuJoCo 自带窗口，而是用 [viser](https://github.com/nerfstudio-project/viser)：
仿真节点只通过 websocket 推送各几何体的位姿，渲染由浏览器的 WebGL 完成。默认关闭，设置端口后开启：

```bash
VIEWER_PORT=8080 mujoco_sim/docker/run.sh bash     # 容器内按下文构建后：ros2 launch xhumanoid_mujoco_sim sim.launch.py
# 本机浏览器打开 http://127.0.0.1:8080
# 宿主机在远端时，在本机建立 SSH 隧道后再打开：  ssh -L 8080:127.0.0.1:8080 <宿主机>
```

- `run.sh` 只把端口发布到宿主机的 `127.0.0.1`。设置 `VIEWER_BIND=0.0.0.0` 会暴露到所有网卡。**viser 没有认证**，在共享主机上请使用 SSH 隧道。
- 直接运行节点时用参数 `viewer_port:=8080`（或环境变量 `XHUMANOID_SIM_VIEWER_PORT`）和 `viewer_host`。
- 画面只是几何的示意：机器人使用 MJCF 的可视网格，手使用胶囊，测试横杆是圆柱，地面是网格。没有光照细节、关节坐标轴或接触力显示。
- `scripts/check_viewer.py` 检查 HTTP 页面、websocket 初始场景和持续的位姿更新，但不检查渲染结果。

## 消息包说明（重要）

真机上的 `ros2_bridge_msgs` 和 `brainco_hand_msgs` 不是公开包。`msgs/` 下是**仅用于仿真的同名替身**，只声明 SDK 示例用到的字段：

- `ros2_bridge_msgs`：`ArmCtrl`、`MotorCtrl` 字段取自 `single_joint_control` 的使用方式。`RobotState.arm.status[].name/.pos` 和 `RobotState.imu` 的字段名取自 SDK 示例。`MotorStatus` 的 `speed/current/temperature` 以及各字段单位是推断值。
- `brainco_hand_msgs`：`TouchStatus/TouchStatusItem` 取自 `brainco_hand_touch_display/README.md`。`SetMotorMulti` 和 `MotorStatus` 的字段名取自手势示例的 Python 与 C++ 代码，数组长度 6 和整数位宽是推断值（Python 与 C++ 示例都能编译并运行）。

**不要在机器人上构建这些包**，它们会覆盖 `~/xos` 中的正式定义。

## 与官方 xSIM_MUJOCO 的关系

官方仿真器使用 `bodyctrl_msgs`（`arm/cmd_ctrl`、`arm/status`、`imu/status`），接口与本 SDK 不同，且依赖图形界面。
本目录只复用它的 tiangong3 MJCF 模型，通过 `scripts/fetch_model.sh` 按固定 commit
（`942469c660ec93e6d7ae9e78026db81cfa623591`）下载，不把模型文件提交到本仓库。

## 快速开始（Docker）

需要 Docker，镜像基于 Ubuntu 24.04 + ROS 2 Jazzy + MuJoCo 3.17.0。

```bash
cd xhumanoid_sdk

# 1. 构建镜像（网络受限时可覆盖镜像源，见 docker/Dockerfile 顶部的 ARG）
docker build -t xhumanoid-mujoco-sim:jazzy mujoco_sim/docker

# 2. 一键冒烟测试：下载模型、构建、启动仿真，依次运行 single_joint_control、灵巧手示例和浏览器查看检查
mujoco_sim/docker/run.sh bash -c 'cd /ws/src/xhumanoid_sdk && bash mujoco_sim/scripts/smoke_test.sh'
# 灵巧手示例改用 C++ 版本：HAND_IMPL=cpp bash mujoco_sim/scripts/smoke_test.sh
```

通过时最后输出 `SMOKE TEST PASSED`。`single_joint_control` 日志包含 `All motion stages completed!`，
灵巧手部分由 `scripts/check_hand.py` 依次触发 `paper/ok/rock/scissors/paper`，检查手指位置和触觉读数，
浏览器查看部分由 `scripts/check_viewer.py` 检查。

手动运行：

```bash
mujoco_sim/docker/run.sh bash        # 进入容器，仓库以只读方式挂载到 /ws/src/xhumanoid_sdk
# 容器内
source /opt/ros/jazzy/setup.bash
cd /ws
colcon build --base-paths src/xhumanoid_sdk/mujoco_sim src/xhumanoid_sdk/single_joint_control/python \
  --packages-select ros2_bridge_msgs brainco_hand_msgs xhumanoid_mujoco_sim single_joint_control_py
source install/setup.bash
ros2 launch xhumanoid_mujoco_sim sim.launch.py &
ros2 run single_joint_control_py cmd_publisher
```

`run.sh` 默认使用 `ROS_DOMAIN_ID=42`，且不使用 host 网络，避免 DDS 流量进入共享主机网络。

## 参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `model_path` | 环境变量 `XHUMANOID_SIM_MODEL` | tiangong3 MJCF 路径（`fetch_model.sh` 会打印） |
| `fix_base` | `true` | 固定骨盆。`false` 时机体会倒下，因为没有平衡控制 |
| `state_rate_hz` | `100.0` | 仿真步进与 `/robot_state` 发布频率 |
| `realtime_factor` | `1.0` | 相对实时的仿真倍率 |
| `with_hands` | `true` | 在两个手腕上挂灵巧手并提供 BrainCo 话题 |
| `hand_full_stroke_s` | `0.8` | 默认速度下 1→1000 的用时（未标定） |
| `viewer_port` | 环境变量 `XHUMANOID_SIM_VIEWER_PORT`，否则 `0` | 大于 0 时启动浏览器查看 |
| `viewer_host` | `0.0.0.0` | 查看服务的监听地址（容器内） |

## 目录

```
mujoco_sim/
├── docker/        # Dockerfile 与 run.sh
├── msgs/          # 仅用于仿真的 ros2_bridge_msgs、brainco_hand_msgs 替身
├── python/        # xhumanoid_mujoco_sim (ament_python)，入口 sim_node
├── scripts/       # fetch_model.sh、smoke_test.sh、check_hand.py、check_viewer.py
└── models/        # 下载的模型（已 gitignore）
```
