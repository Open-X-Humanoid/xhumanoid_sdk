#!/usr/bin/env bash
# Run INSIDE the container (docker/run.sh mujoco_sim/scripts/smoke_test.sh).
# Builds the packages, starts the simulator and runs single_joint_control_py
# against it. Passes when the example reports that all motion stages completed.
set -eo pipefail

SRC=/ws/src/xhumanoid_sdk
LOG_DIR="${LOG_DIR:-/tmp/xhumanoid_smoke}"
mkdir -p "${LOG_DIR}"

set +u
source /opt/ros/jazzy/setup.bash
cd /ws
colcon build --base-paths "${SRC}/mujoco_sim" "${SRC}/single_joint_control/python" \
  --packages-select ros2_bridge_msgs xhumanoid_mujoco_sim single_joint_control_py \
  > "${LOG_DIR}/build.log" 2>&1 || { tail -40 "${LOG_DIR}/build.log"; exit 1; }
source /ws/install/setup.bash

ros2 launch xhumanoid_mujoco_sim sim.launch.py > "${LOG_DIR}/sim.log" 2>&1 &
SIM_PID=$!
trap 'kill ${SIM_PID} 2>/dev/null || true; wait ${SIM_PID} 2>/dev/null || true' EXIT

# Wait for /robot_state before starting the example.
timeout 60 ros2 topic echo --once /robot_state ros2_bridge_msgs/msg/RobotState > "${LOG_DIR}/robot_state_sample.txt"

timeout "${EXAMPLE_TIMEOUT:-120}" ros2 run single_joint_control_py cmd_publisher \
  > "${LOG_DIR}/example.log" 2>&1 &
EX_PID=$!
for _ in $(seq 1 $(( ${EXAMPLE_TIMEOUT:-120} * 2 ))); do
  grep -q "All motion stages completed" "${LOG_DIR}/example.log" && break
  kill -0 ${EX_PID} 2>/dev/null || break
  sleep 0.5
done
kill ${EX_PID} 2>/dev/null || true

grep -E "Stage .* completed|All motion stages" "${LOG_DIR}/example.log" || true
if grep -q "All motion stages completed" "${LOG_DIR}/example.log"; then
  echo "SMOKE TEST PASSED"
else
  echo "SMOKE TEST FAILED, last example output:"; tail -15 "${LOG_DIR}/example.log"
  echo "--- sim.log"; tail -15 "${LOG_DIR}/sim.log"
  exit 1
fi
