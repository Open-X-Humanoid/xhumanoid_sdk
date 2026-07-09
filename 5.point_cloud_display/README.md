# 点云显示节点 (Point Cloud Display Node)

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

基于 ROS2 的 Livox 激光雷达点云显示节点。

提供两个版本：
- **Python版本**: `point_cloud_display_py`
- **C++版本**: `point_cloud_display_cpp`

## 功能特性

- 订阅 Livox 雷达点云数据
- 点云统计信息显示（点数、边界范围、处理时间）
- 可选的点云滤波功能：
  - Voxel Grid 下采样
  - Statistical Outlier Removal 离群点去除
- 自动启动 RViz2 进行可视化

## 依赖

- ROS2 (Humble/Jazzy)
- PCL (Point Cloud Library)
- pcl_conversions
- sensor_msgs

## 目录结构

```
5.point_cloud_display/
├── README.md
├── python/                              # Python版本 (point_cloud_display_py)
│   ├── package.xml
│   ├── setup.py
│   ├── setup.cfg
│   ├── resource/
│   │   └── point_cloud_display_py
│   ├── point_cloud_display/
│   │   ├── __init__.py
│   │   └── point_cloud_display_node.py
│   ├── launch/
│   │   └── point_cloud_display.launch.py
│   └── rviz/
│       └── point_cloud.rviz
└── cpp/                                 # C++版本 (point_cloud_display_cpp)
    └── point_cloud_display/
        ├── CMakeLists.txt
        ├── package.xml
        ├── src/
        │   └── point_cloud_display_node.cpp
        ├── launch/
        │   └── point_cloud_display.launch.py
        └── rviz/
            └── point_cloud.rviz
```

## 编译

### Python版本

```bash
cd ~/xos
colcon build --packages-select point_cloud_display_py
source setup.bash
```

### C++版本

```bash
cd ~/xos
colcon build --packages-select point_cloud_display_cpp
source setup.bash
```

## 使用方法

### 1. 基本使用（无滤波）

#### Python版本

```bash
ros2 launch point_cloud_display_py point_cloud_display.launch.py
```

#### C++版本

```bash
ros2 launch point_cloud_display_cpp point_cloud_display.launch.py
```

### 2. 启用 Voxel Grid 滤波

#### Python版本

```bash
ros2 launch point_cloud_display_py point_cloud_display.launch.py \
    filter_enable:=true \
    voxel_leaf_size:=0.1
```

#### C++版本

```bash
ros2 launch point_cloud_display_cpp point_cloud_display.launch.py \
    filter_enable:=true \
    voxel_leaf_size:=0.1
```

### 3. 启用 Statistical Outlier Removal

#### Python版本

```bash
ros2 launch point_cloud_display_py point_cloud_display.launch.py \
    sor_enable:=true \
    sor_mean_k:=50 \
    sor_stddev_mul_thresh:=1.0
```

#### C++版本

```bash
ros2 launch point_cloud_display_cpp point_cloud_display.launch.py \
    sor_enable:=true \
    sor_mean_k:=50 \
    sor_stddev_mul_thresh:=1.0
```

### 4. 同时启用两种滤波

#### Python版本

```bash
ros2 launch point_cloud_display_py point_cloud_display.launch.py \
    filter_enable:=true \
    voxel_leaf_size:=0.05 \
    sor_enable:=true
```

#### C++版本

```bash
ros2 launch point_cloud_display_cpp point_cloud_display.launch.py \
    filter_enable:=true \
    voxel_leaf_size:=0.05 \
    sor_enable:=true
```

## 参数说明

| 参数名 | 默认值 | 说明 |
|--------|--------|------|
| `input_topic` | `/livox/lidar` | 输入点云话题 |
| `output_topic` | `/point_cloud/filtered` | 输出滤波后点云话题 |
| `frame_id` | `livox_frame` | 点云坐标系 |
| `filter_enable` | `false` | 是否启用 Voxel Grid 滤波 |
| `voxel_leaf_size` | `0.05` | Voxel Grid 体素大小（米） |
| `sor_enable` | `false` | 是否启用 Statistical Outlier Removal |
| `sor_mean_k` | `50` | SOR 邻近点数量 |
| `sor_stddev_mul_thresh` | `1.0` | SOR 标准差倍数阈值 |
| `rviz_config` | `$(pkg)/rviz/point_cloud.rviz` | RViz 配置文件路径 |

## 话题

| 话题名 | 类型 | 方向 | 说明 |
|--------|------|------|------|
| `/livox/lidar` | `sensor_msgs/PointCloud2` | 订阅 | Livox 原始点云 |
| `/point_cloud/filtered` | `sensor_msgs/PointCloud2` | 发布 | 滤波后点云 |

## 配合 Livox 驱动使用

首先启动 Livox 驱动节点，然后启动点云显示节点：

#### Python版本

```bash
# 终端 1: 启动 Livox 驱动
ros2 launch livox_ros_driver2 msg_MID360_launch.py

# 终端 2: 启动点云显示
ros2 launch point_cloud_display_py point_cloud_display.launch.py
```

#### C++版本

```bash
# 终端 1: 启动 Livox 驱动
ros2 launch livox_ros_driver2 msg_MID360_launch.py

# 终端 2: 启动点云显示
ros2 launch point_cloud_display_cpp point_cloud_display.launch.py
```

## 输出示例

节点会定期输出点云统计信息：

```
[point_cloud_display_node]: Statistics - Frames: 100, Total Points: 2560000, Avg Points/Frame: 25600
[point_cloud_display_node]: Bounds - X: [-15.23, 18.45], Y: [-12.67, 14.32], Z: [-2.15, 5.67]
[point_cloud_display_node]: Last Processing Time: 5 ms
```

## 注意事项

1. 确保 Livox 雷达已正确连接并配置
2. 确保 `livox_frame` 坐标系已定义或使用正确的 frame_id
3. 滤波参数需要根据实际场景调整