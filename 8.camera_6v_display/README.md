# 6V相机可视化节点（选配） (Camera 6V Display Node)

> **适用平台**: 具身天工3.0 (Thor) | **选配功能** - 需要搭配6V相机模块使用
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

基于 ROS2 的6路相机实时可视化显示节点。

提供两个版本：
- **Python版本**: `camera_6v_display_py`
- **C++版本**: `camera_6v_display_cpp`

## 功能特性

- 订阅6个相机的图像数据（相机索引：0, 1, 2, 4, 5, 6，跳过3和7）
- 使用OpenCV在2x3网格布局中实时显示所有相机画面
- 支持原始图像和压缩图像话题
- 实时显示每个相机的FPS
- 自动添加相机标签和时间戳
- 支持自定义显示尺寸

## 依赖

- ROS2 (Humble/Jazzy)
- OpenCV
- cv_bridge
- sensor_msgs

## 目录结构

```
8.camera_6v_display/
├── README.md
├── python/                              # Python版本 (包名: camera_6v_display_py)
│   ├── package.xml
│   ├── setup.py
│   ├── setup.cfg
│   ├── resource/
│   │   └── camera_6v_display_py
│   ├── launch/
│   │   └── camera_6v_display.launch.py
│   └── camera_6v_display/
│       ├── __init__.py
│       └── camera_6v_display_node.py
└── cpp/                                 # C++版本 (包名: camera_6v_display_cpp)
    └── camera_6v_display/
        ├── CMakeLists.txt
        ├── package.xml
        ├── launch/
        │   └── camera_6v_display.launch.py
        └── src/
            └── camera_6v_display_node.cpp
```

## 编译

### Python版本

```bash
cd ~/xos
colcon build --packages-select camera_6v_display_py
source setup.bash
```

### C++版本

```bash
cd ~/xos
colcon build --packages-select camera_6v_display_cpp
source setup.bash
```

## 使用方法

### 1. 基本使用

#### Python版本

```bash
ros2 launch camera_6v_display_py camera_6v_display.launch.py
```

#### C++版本

```bash
ros2 launch camera_6v_display_cpp camera_6v_display.launch.py
```

### 2. 使用压缩图像话题

#### Python版本

```bash
ros2 launch camera_6v_display_py camera_6v_display.launch.py use_compressed:=true
```

#### C++版本

```bash
ros2 launch camera_6v_display_cpp camera_6v_display.launch.py use_compressed:=true
```

### 3. 自定义显示尺寸

#### Python版本

```bash
ros2 launch camera_6v_display_py camera_6v_display.launch.py \
    display_width:=640 \
    display_height:=480
```

#### C++版本

```bash
ros2 launch camera_6v_display_cpp camera_6v_display.launch.py \
    display_width:=640 \
    display_height:=480
```

### 4. 完整参数配置

#### Python版本

```bash
ros2 launch camera_6v_display_py camera_6v_display.launch.py \
    display_width:=480 \
    display_height:=360 \
    use_compressed:=false \
    show_fps:=true \
    window_name:="6V Camera Monitor" \
    topic_prefix:=camera
```

#### C++版本

```bash
ros2 launch camera_6v_display_cpp camera_6v_display.launch.py \
    display_width:=480 \
    display_height:=360 \
    use_compressed:=false \
    show_fps:=true \
    window_name:="6V Camera Monitor" \
    topic_prefix:=camera
```

## 参数说明

| 参数名 | 默认值 | 说明 |
|--------|--------|------|
| `display_width` | `320` | 每个相机显示区域的宽度（像素） |
| `display_height` | `240` | 每个相机显示区域的高度（像素） |
| `use_compressed` | `false` | 是否使用压缩图像话题 |
| `show_fps` | `true` | 是否显示FPS |
| `window_name` | `6V Camera Display` | OpenCV窗口名称 |
| `topic_prefix` | `camera` | 话题前缀 |

## 话题

### 订阅话题

| 话题名 | 类型 | 说明 |
|--------|------|------|
| `camera{i}/image_raw` | `sensor_msgs/msg/Image` | 相机原始图像（i = 0,1,2,4,5,6） |
| `camera{i}/image/compressed` | `sensor_msgs/msg/CompressedImage` | 相机压缩图像（use_compressed:=true时） |

## 显示布局

```
+-------------------+-------------------+-------------------+
|      CAM 0        |      CAM 1        |      CAM 2        |
|     [FPS]         |     [FPS]         |     [FPS]         |
+-------------------+-------------------+-------------------+
|      CAM 4        |      CAM 5        |      CAM 6        |
|     [FPS]         |     [FPS]         |     [FPS]         |
+-------------------+-------------------+-------------------+
```

## 配合相机驱动使用

首先启动相机驱动节点，然后启动可视化节点：

#### Python版本

```bash
# 终端 1: 启动相机驱动
ros2 run camera_v4l2_opencv_ros camera_v4l2_opencv_node

# 终端 2: 启动可视化
ros2 launch camera_6v_display_py camera_6v_display.launch.py
```

#### C++版本

```bash
# 终端 1: 启动相机驱动
ros2 run camera_v4l2_opencv_ros camera_v4l2_opencv_node

# 终端 2: 启动可视化
ros2 launch camera_6v_display_cpp camera_6v_display.launch.py
```

## 输出示例

节点启动后会显示：

```
[camera_6v_display_node]: Camera 6V Display Node initialized
[camera_6v_display_node]:   Display size: 320x240 per camera
[camera_6v_display_node]:   Use compressed: false
[camera_6v_display_node]:   Subscribed to: camera0/image_raw
[camera_6v_display_node]:   Subscribed to: camera1/image_raw
[camera_6v_display_node]:   Subscribed to: camera2/image_raw
[camera_6v_display_node]:   Subscribed to: camera4/image_raw
[camera_6v_display_node]:   Subscribed to: camera5/image_raw
[camera_6v_display_node]:   Subscribed to: camera6/image_raw
```

## 快捷键

- `ESC` 或 `q` - 退出程序

## 注意事项

1. 确保相机驱动节点已正确启动并发布图像数据
2. 如果相机未启动，会显示"Waiting..."占位图像
3. 需要图形界面支持（SSH连接需使用 `-X` 转发或使用VNC）
4. 显示尺寸建议与相机分辨率保持相同宽高比

## 相关链接

- 相机驱动包：`hardware/fusion/src/camera`
- 相机驱动节点：`camera_v4l2_opencv_ros`