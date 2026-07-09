# GPS数据获取节点（选配） (GPS Data Display Node)

> **适用平台**: 具身天工3.0 (Thor) | **选配功能** - 需要搭配GPS模块使用
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

基于 ROS2 的GPS数据获取与解析显示节点。

提供两个版本：
- **Python版本**: `gps_data_display_py`
- **C++版本**: `gps_data_display_cpp`

## 功能特性

- 订阅GPS驱动发布的定位数据
- 实时解析并显示GPS信息（经纬度、高度、速度、航向等）
- GPS定位状态解析与彩色显示
  - INVALID (红色) - 定位无效
  - SINGLE (黄色) - 单点定位
  - DGPS/SBAS (青色) - 差分定位
  - RTK_FIXED (绿色) - RTK固定解
  - RTK_FLOAT (蓝色) - RTK浮点解
- GPS数据统计（消息总数、有效率、位置范围等）
- 支持数据保存到文件

## 依赖

- ROS2 (Humble/Jazzy)
- navigation_msgs (自定义GPS消息)
- rclcpp

## 目录结构

```
gps_data_display/
├── README.md
├── python/                              # Python版本 (gps_data_display_py)
│   ├── package.xml
│   ├── setup.py
│   ├── setup.cfg
│   ├── resource/
│   │   └── gps_data_display_py
│   ├── gps_data_display/
│   │   ├── __init__.py
│   │   └── gps_data_display_node.py
│   └── launch/
│       └── gps_data_display.launch.py
└── cpp/                                 # C++版本 (gps_data_display_cpp)
    └── gps_data_display/
        ├── CMakeLists.txt
        ├── package.xml
        ├── src/
        │   └── gps_data_display_node.cpp
        └── launch/
            └── gps_data_display.launch.py
```

## 编译

### Python版本

```bash
cd ~/xos
colcon build --packages-select gps_data_display_py
source setup.bash
```

### C++版本

```bash
cd ~/xos
colcon build --packages-select gps_data_display_cpp
source setup.bash
```

## 使用方法

### 1. 基本使用

#### Python版本

```bash
ros2 launch gps_data_display_py gps_data_display.launch.py
```

#### C++版本

```bash
ros2 launch gps_data_display_cpp gps_data_display.launch.py
```

### 2. 保存数据到文件

#### Python版本

```bash
ros2 launch gps_data_display_py gps_data_display.launch.py \
    save_to_file:=true \
    log_file:=/tmp/gps_log.txt
```

#### C++版本

```bash
ros2 launch gps_data_display_cpp gps_data_display.launch.py \
    save_to_file:=true \
    log_file:=/tmp/gps_log.txt
```

### 3. 自定义话题和显示选项

#### Python版本

```bash
ros2 launch gps_data_display_py gps_data_display.launch.py \
    gps_topic:=gps/fix \
    show_raw_data:=true \
    show_status:=true \
    log_interval:=2.0
```

#### C++版本

```bash
ros2 launch gps_data_display_cpp gps_data_display.launch.py \
    gps_topic:=gps/fix \
    show_raw_data:=true \
    show_status:=true \
    log_interval:=2.0
```

## 参数说明

| 参数名 | 默认值 | 说明 |
|--------|--------|------|
| `gps_topic` | `gps/fix` | GPS数据话题 |
| `save_to_file` | `false` | 是否保存数据到文件 |
| `log_file` | `/tmp/gps_data.txt` | 日志文件路径 |
| `log_interval` | `1.0` | 统计信息打印间隔（秒） |
| `show_raw_data` | `true` | 显示原始GPS数据 |
| `show_status` | `true` | 显示状态摘要 |

## 话题

### 订阅话题

| 话题名 | 类型 | 说明 |
|--------|------|------|
| `gps/fix` | `navigation_msgs/msg/GpsFix` | GPS定位数据 |

### 消息字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| latitude | float64 | 纬度（度） |
| longitude | float64 | 经度（度） |
| altitude | float64 | 高度（米） |
| status | int32 | 定位状态（0=无效，1=单点，2=差分，4=RTK固定，5=RTK浮点） |
| num_sats | int32 | 卫星数量 |
| hdop | float64 | 定位精度因子 |
| speed | float64 | 速度（m/s） |
| heading | float64 | 航向角（度） |
| tx | float64 | GPS-PPS时间差（ms） |

## 输出示例

### 实时数据显示

```
========== GPS Data ==========
  Timestamp: 2025-03-19 14:30:15.123
  Status: RTK_FIXED
  Position:
    Latitude:  31.123456° N
    Longitude: 121.654321° E
    Altitude:  15.234 m
  Quality:
    Satellites: 12
    HDOP: 0.85
  Motion:
    Speed:   2.500 m/s (9.0 km/h)
    Heading: 45.00°
  Timing:
    GPS-PPS diff: 0.500 ms
==============================
```

### 状态摘要（单行）

```
[GPS] RTK_FIXED | Sats:12 | HDOP:0.8 | 31.123456,121.654321 | Alt:15.2m | Spd:9.0km/h | Head:45.0°
```

### 统计信息

```
======= GPS Statistics =======
  Total messages: 300
  Valid messages: 295 (98.3%)
  Position bounds:
    Latitude:  [31.123000, 31.124000]
    Longitude: [121.654000, 121.655000]
  Max speed: 5.500 m/s (19.8 km/h)
  Max satellites: 14
==============================
```

## 日志文件格式

启用 `save_to_file:=true` 后，数据以CSV格式保存：

```
# GPS Data Log - Started at 2025-03-19 14:30:00
# timestamp,lat,lon,alt,status,sats,hdop,speed,heading,tx_ms
1742377815.123,31.123456,121.654321,15.234,4,12,0.85,2.5,45.0,0.5
```

## 配合GPS驱动使用

首先启动GPS驱动节点，然后启动数据获取节点：

#### Python版本

```bash
# 终端 1: 启动GPS驱动
ros2 launch gps_ros2 gps.launch.py

# 终端 2: 启动GPS数据获取
ros2 launch gps_data_display_py gps_data_display.launch.py
```

#### C++版本

```bash
# 终端 1: 启动GPS驱动
ros2 launch gps_ros2 gps.launch.py

# 终端 2: 启动GPS数据获取
ros2 launch gps_data_display_cpp gps_data_display.launch.py
```

## 定位状态说明

| 状态值 | 名称 | 说明 | 颜色 |
|--------|------|------|------|
| 0 | INVALID | 定位不可用或无效 | 红色 |
| 1 | SINGLE | 单点定位 | 黄色 |
| 2 | DGPS/SBAS | 伪距差分或SBAS定位 | 青色 |
| 4 | RTK_FIXED | RTK固定解 | 绿色 |
| 5 | RTK_FLOAT | RTK浮点解 | 蓝色 |

## 注意事项

1. 确保GPS驱动节点已正确启动并发布数据
2. GPS天线需要有良好的天空视野以获得有效定位
3. RTK定位需要基站支持
4. 日志文件会追加写入，不会覆盖已有数据

## 相关链接

- GPS驱动包：`hardware/fusion/src/gps_ros2`
- GPS消息定义：`interface/navigation_msgs/msg/GpsFix.msg`