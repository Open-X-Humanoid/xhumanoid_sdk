#!/usr/bin/env bash
# Run the simulator image with the SDK source mounted at /ws/src/xhumanoid_sdk.
# Usage: mujoco_sim/docker/run.sh [command ...]   (default: interactive bash)
set -euo pipefail

IMAGE="${IMAGE:-xhumanoid-mujoco-sim:jazzy}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${HERE}/../.." && pwd)"
"${HERE}/../scripts/fetch_model.sh" > /dev/null
MODEL_IN_CONTAINER="/ws/src/xhumanoid_sdk/mujoco_sim/models/xSIM_MUJOCO/resources/tiangong3/urdf/tiangong3.xml"

tty_flags=()
[[ -t 0 && -t 1 ]] && tty_flags=(-it)

exec docker run --rm ${tty_flags[@]+"${tty_flags[@]}"} \
  -v "${REPO}:/ws/src/xhumanoid_sdk:ro" \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e "XHUMANOID_SIM_MODEL=${MODEL_IN_CONTAINER}" \
  -e ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}" \
  "${IMAGE}" "${@:-bash}"
