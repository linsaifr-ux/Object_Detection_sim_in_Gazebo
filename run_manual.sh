#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$PROJECT_DIR/venv"
WS="$PROJECT_DIR/ros2_ws"

source /opt/ros/jazzy/setup.bash
source "$WS/install/setup.bash"

export PYTHONPATH="$VENV/lib/python3.12/site-packages:$PYTHONPATH"
export GZ_SIM_RESOURCE_PATH="$WS/install/drone_yolo_detection/share:$GZ_SIM_RESOURCE_PATH"
export YOLO_MODEL="$PROJECT_DIR/models/yolov8l.pt"

echo "Starting Manual Drone Control + YOLOv8l Detection..."
echo ""
echo "Keyboard controls (in the teleop window):"
echo "  i        : fly forward"
echo "  ,        : fly backward"
echo "  j        : turn left (yaw)"
echo "  l        : turn right (yaw)"
echo "  u/o      : strafe left/right"
echo "  t        : ascend (increase z speed)"
echo "  b        : descend"
echo "  k        : stop / hover"
echo "  q/z      : increase/decrease max speed"
echo ""
echo "A teleop window will open in ~4 seconds."
echo ""

ros2 launch drone_yolo_detection drone_manual.launch.py
