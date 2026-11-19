#!/usr/bin/env bash
# Download the tiangong3 MuJoCo model from Open-X-Humanoid/xSIM_MUJOCO (Apache-2.0)
# at a pinned commit into mujoco_sim/models/xSIM_MUJOCO/.
#
# Environment overrides:
#   XSIM_COMMIT   commit to fetch (default: pinned below)
#   XSIM_TARBALL  path of an already downloaded tar.gz of that commit (skips the download)
set -euo pipefail

XSIM_COMMIT="${XSIM_COMMIT:-942469c660ec93e6d7ae9e78026db81cfa623591}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${HERE}/../models/xSIM_MUJOCO"
MODEL="${DEST}/resources/tiangong3/urdf/tiangong3.xml"

if [[ -f "${MODEL}" ]]; then
  echo "${MODEL}"
  exit 0
fi

tarball="${XSIM_TARBALL:-}"
if [[ -z "${tarball}" ]]; then
  tarball="$(mktemp --suffix=.tar.gz)"
  trap 'rm -f "${tarball}"' EXIT
  curl -fL --retry 5 --retry-delay 3 -o "${tarball}" \
    "https://codeload.github.com/Open-X-Humanoid/xSIM_MUJOCO/tar.gz/${XSIM_COMMIT}"
fi

mkdir -p "${DEST}"
tar -xzf "${tarball}" -C "${DEST}" --strip-components=1 \
  --wildcards '*/LICENSE' '*/resources/tiangong3/*'
echo "${XSIM_COMMIT}" > "${DEST}/COMMIT"
echo "${MODEL}"
