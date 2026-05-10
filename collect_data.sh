#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="$PROJECT_DIR/ros2_ws"

source /opt/ros/jazzy/setup.bash
source "$WS/install/setup.bash"
source "$PROJECT_DIR/venv/bin/activate"

export PYTHONPATH="$PROJECT_DIR/venv/lib/python3.12/site-packages:$PYTHONPATH"
export GZ_SIM_RESOURCE_PATH="$WS/install/drone_yolo_detection/share:$GZ_SIM_RESOURCE_PATH"

SPLIT=${1:-train}
IMAGES=${2:-3000}

echo "Collecting $IMAGES synthetic images → datasets/custom_shapes/$SPLIT/"
echo "Gazebo runs headless (no window)."
echo ""

ros2 launch drone_yolo_detection data_collection.launch.py \
    target_images:=$IMAGES \
    output_split:=$SPLIT
