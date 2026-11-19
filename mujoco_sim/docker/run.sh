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

# Browser viewer: VIEWER_PORT=8080 publishes the viewer on 127.0.0.1:8080 (use
# an SSH tunnel from a remote machine). Set VIEWER_BIND=0.0.0.0 to expose it
# on all interfaces; the viewer has no authentication.
port_flags=()
if [[ -n "${VIEWER_PORT:-}" ]]; then
  port_flags=(-p "${VIEWER_BIND:-127.0.0.1}:${VIEWER_PORT}:${VIEWER_PORT}"
              -e "XHUMANOID_SIM_VIEWER_PORT=${VIEWER_PORT}")
fi

exec docker run --rm ${tty_flags[@]+"${tty_flags[@]}"} \
  ${port_flags[@]+"${port_flags[@]}"} \
  -v "${REPO}:/ws/src/xhumanoid_sdk:ro" \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e "XHUMANOID_SIM_MODEL=${MODEL_IN_CONTAINER}" \
  -e ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}" \
  "${IMAGE}" "${@:-bash}"
