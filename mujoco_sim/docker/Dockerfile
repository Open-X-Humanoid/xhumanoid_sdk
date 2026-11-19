# ROS 2 Jazzy + MuJoCo runtime for the xhumanoid_sdk simulator.
# The SDK source is NOT copied in: docker/run.sh bind-mounts it at /ws/src/xhumanoid_sdk.
#
# Build (defaults use the official upstream sources):
#   docker build -t xhumanoid-mujoco-sim:jazzy mujoco_sim/docker
# Behind a restricted network, override the mirrors, for example:
#   docker build --network host -t xhumanoid-mujoco-sim:jazzy \
#     --build-arg UBUNTU_MIRROR=http://mirrors.tuna.tsinghua.edu.cn/ubuntu \
#     --build-arg ROS_APT_URL=http://mirrors.tuna.tsinghua.edu.cn/ros2/ubuntu \
#     --build-arg ROS_KEY_URL=https://mirrors.tuna.tsinghua.edu.cn/rosdistro/ros.key \
#     --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
#     mujoco_sim/docker
ARG BASE_IMAGE=ubuntu:24.04
FROM ${BASE_IMAGE}

ARG UBUNTU_MIRROR=
ARG ROS_APT_URL=http://packages.ros.org/ros2/ubuntu
ARG ROS_KEY_URL=https://raw.githubusercontent.com/ros/rosdistro/master/ros.key
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG MUJOCO_VERSION=3.17.0

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    PIP_INDEX_URL=${PIP_INDEX_URL} \
    MUJOCO_GL=egl

RUN if [ -n "${UBUNTU_MIRROR}" ]; then \
      sed -i "s|http://archive.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g; s|http://security.ubuntu.com/ubuntu|${UBUNTU_MIRROR}|g" \
        /etc/apt/sources.list.d/ubuntu.sources; \
    fi \
 && apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
 && curl -fsSL --retry 5 "${ROS_KEY_URL}" -o /usr/share/keyrings/ros-archive-keyring.gpg.asc \
 && gpg --dearmor < /usr/share/keyrings/ros-archive-keyring.gpg.asc > /usr/share/keyrings/ros-archive-keyring.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] ${ROS_APT_URL} noble main" \
      > /etc/apt/sources.list.d/ros2.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential cmake python3-pip python3-numpy \
      python3-colcon-common-extensions \
      ros-jazzy-ros-base \
      libegl1 libgl1 libglx-mesa0 \
 && pip3 install --no-cache-dir "mujoco==${MUJOCO_VERSION}" \
 && rm -rf /var/lib/apt/lists/*

# Browser viewer (optional at run time, see README): rendering happens in the
# browser, so the container needs no display or GPU.
ARG VISER_VERSION=1.1.1
RUN pip3 install --no-cache-dir "viser==${VISER_VERSION}"

WORKDIR /ws
CMD ["bash"]
