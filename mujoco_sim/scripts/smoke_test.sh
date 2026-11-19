#!/usr/bin/env bash
# Run INSIDE the container (docker/run.sh mujoco_sim/scripts/smoke_test.sh).
# Builds the packages, then runs three checks against the simulator
# (sim.launch.py, robot with a hand on each wrist):
#   1. single_joint_control_py
#   2. brainco_hand_gesture_control and brainco_hand_touch_display
#   3. the browser viewer answers over HTTP and websocket
# Passes when all succeed. HAND_IMPL=cpp runs the C++ hand examples instead of
# the Python ones (default: py).
set -eo pipefail

HAND_IMPL="${HAND_IMPL:-py}"

SRC=/ws/src/xhumanoid_sdk
LOG_DIR="${LOG_DIR:-/tmp/xhumanoid_smoke}"
mkdir -p "${LOG_DIR}"

set +u
source /opt/ros/jazzy/setup.bash
cd /ws
colcon build \
  --base-paths "${SRC}/mujoco_sim" "${SRC}/single_joint_control/python" \
               "${SRC}/brainco_hand_gesture_control" \
               "${SRC}/brainco_hand_touch_display" \
  --packages-select ros2_bridge_msgs brainco_hand_msgs xhumanoid_mujoco_sim \
                    single_joint_control_py brainco_hand_gesture_interfaces \
                    "brainco_hand_gesture_control_${HAND_IMPL}" \
                    "brainco_hand_touch_display_${HAND_IMPL}" \
  > "${LOG_DIR}/build.log" 2>&1 || { tail -40 "${LOG_DIR}/build.log"; exit 1; }
source /ws/install/setup.bash

PIDS=()
cleanup() {
  for pid in "${PIDS[@]}"; do kill "${pid}" 2>/dev/null || true; done
  for pid in "${PIDS[@]}"; do wait "${pid}" 2>/dev/null || true; done
}
trap cleanup EXIT

# ---- 1. robot arm: single_joint_control_py -------------------------------
ros2 launch xhumanoid_mujoco_sim sim.launch.py > "${LOG_DIR}/sim.log" 2>&1 &
SIM_PID=$!
PIDS+=("${SIM_PID}")

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
kill "${SIM_PID}" 2>/dev/null || true

grep -E "Stage .* completed|All motion stages" "${LOG_DIR}/example.log" || true
if ! grep -q "All motion stages completed" "${LOG_DIR}/example.log"; then
  echo "SMOKE TEST FAILED (single_joint_control), last example output:"
  tail -15 "${LOG_DIR}/example.log"
  echo "--- sim.log"; tail -15 "${LOG_DIR}/sim.log"
  exit 1
fi
echo "single_joint_control: PASSED"

# ---- 2. dexterous hand: gesture control + touch display --------------------
ros2 launch xhumanoid_mujoco_sim sim.launch.py > "${LOG_DIR}/hand_sim.log" 2>&1 &
HAND_SIM_PID=$!
PIDS+=("${HAND_SIM_PID}")
ros2 launch "brainco_hand_gesture_control_${HAND_IMPL}" hand_gesture_control.launch.py \
  > "${LOG_DIR}/gesture.log" 2>&1 &
PIDS+=($!)
ros2 launch "brainco_hand_touch_display_${HAND_IMPL}" touch_display.launch.py print_interval:=1.0 \
  > "${LOG_DIR}/touch_display.log" 2>&1 &
PIDS+=($!)

if timeout 120 python3 "${SRC}/mujoco_sim/scripts/check_hand.py" > "${LOG_DIR}/hand_check.log" 2>&1; then
  cat "${LOG_DIR}/hand_check.log"
else
  cat "${LOG_DIR}/hand_check.log"
  echo "SMOKE TEST FAILED (hand), hand_sim.log:"; tail -15 "${LOG_DIR}/hand_sim.log"
  echo "--- gesture.log"; tail -15 "${LOG_DIR}/gesture.log"
  exit 1
fi
# The table header is only printed once /right_hand/touch_status has data.
if grep -q "Normal(N)" "${LOG_DIR}/touch_display.log"; then
  echo "touch_display: table printed"
else
  echo "SMOKE TEST FAILED (touch_display), last output:"; tail -20 "${LOG_DIR}/touch_display.log"
  exit 1
fi
kill "${HAND_SIM_PID}" 2>/dev/null || true

# ---- 3. browser viewer -----------------------------------------------------
ros2 launch xhumanoid_mujoco_sim sim.launch.py viewer_port:=8080 > "${LOG_DIR}/viewer_sim.log" 2>&1 &
PIDS+=($!)
if timeout 60 python3 "${SRC}/mujoco_sim/scripts/check_viewer.py" 8080 > "${LOG_DIR}/viewer_check.log" 2>&1; then
  cat "${LOG_DIR}/viewer_check.log"
else
  cat "${LOG_DIR}/viewer_check.log"
  echo "SMOKE TEST FAILED (viewer), viewer_sim.log:"; tail -15 "${LOG_DIR}/viewer_sim.log"
  exit 1
fi
echo "SMOKE TEST PASSED"
