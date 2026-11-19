# mujoco_sim

基于 MuJoCo 的无头（headless）仿真节点，对外暴露与真机一致的 ROS 2 话题，
让 SDK 示例（目前为 `single_joint_control`）可以在没有机器人的情况下运行。

> **仿真结果不等同于真机验证。** 模型动力学未经标定，只用于检查接口、流程和逻辑。
> 请勿将仿真中的增益、速度、时间直接用于真机。

## 功能范围

| 项目 | 状态 |
| --- | --- |
| 订阅 `/arm/cmd` (`ros2_bridge_msgs/ArmCtrl`) | mode 0（位置）、mode 1（力位混合） |
| 发布 `/robot_state` (`ros2_bridge_msgs/RobotState`) | 手臂关节状态（电机 ID 11–27）、IMU，100 Hz |
| 机体 | 骨盆固定在世界系（`fix_base:=true`），无平衡控制器 |
| 机器人模型 | 具身天工 3.0（tiangong3），来自官方 [xSIM_MUJOCO](https://github.com/Open-X-Humanoid/xSIM_MUJOCO) |
| 其他示例（点云、图像、GPS、TTS、灵巧手等） | **未实现** |
| C++ 版本、可视化窗口 | 未提供 |

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

## 消息包说明（重要）

真机上的 `ros2_bridge_msgs` 不是公开包。`msgs/ros2_bridge_msgs` 是一个**仅用于仿真的同名替身**，只声明 SDK 示例用到的字段：

- `ArmCtrl`、`MotorCtrl` 字段取自 `single_joint_control` 的使用方式。
- `RobotState.arm.status[].name/.pos` 和 `RobotState.imu` 的字段名取自 SDK 示例。`MotorStatus` 的 `speed/current/temperature` 以及各字段单位是推断值。

**不要在机器人上构建这个包**，它会覆盖 `~/xos` 中的正式定义。

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

# 2. 一键冒烟测试：下载模型、构建、启动仿真、运行 single_joint_control
mujoco_sim/docker/run.sh bash -c 'cd /ws/src/xhumanoid_sdk && bash mujoco_sim/scripts/smoke_test.sh'
```

通过时最后输出 `SMOKE TEST PASSED`，示例日志包含 `All motion stages completed!`。

手动运行：

```bash
mujoco_sim/docker/run.sh bash        # 进入容器，仓库以只读方式挂载到 /ws/src/xhumanoid_sdk
# 容器内
source /opt/ros/jazzy/setup.bash
cd /ws
colcon build --base-paths src/xhumanoid_sdk/mujoco_sim src/xhumanoid_sdk/single_joint_control/python \
  --packages-select ros2_bridge_msgs xhumanoid_mujoco_sim single_joint_control_py
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

## 目录

```
mujoco_sim/
├── docker/        # Dockerfile 与 run.sh
├── msgs/          # 仅用于仿真的 ros2_bridge_msgs 替身
├── python/        # xhumanoid_mujoco_sim (ament_python)，入口 sim_node
├── scripts/       # fetch_model.sh、smoke_test.sh
└── models/        # 下载的模型（已 gitignore）
```
