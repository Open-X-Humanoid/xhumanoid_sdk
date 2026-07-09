#!/bin/bash
# IMU Display Node - UV Environment Launcher
# This script activates the UV virtual environment before running the node

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/.venv"

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Install it with:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating UV virtual environment..."
    cd "$PROJECT_DIR"
    uv venv
    uv pip install -e .
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Source ROS2 workspace if available
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
elif [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
fi

# Source the workspace install if available
WORKSPACE_INSTALL="$PROJECT_DIR/../../../install/setup.bash"
if [ -f "$WORKSPACE_INSTALL" ]; then
    source "$WORKSPACE_INSTALL"
fi

# Run the node with all arguments
exec python3 "$SCRIPT_DIR/imu_display_node.py" "$@"