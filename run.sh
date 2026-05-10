#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$PROJECT_DIR/venv"
WS="$PROJECT_DIR/ros2_ws"

# Source ROS 2 and workspace
source /opt/ros/jazzy/setup.bash
source "$WS/install/setup.bash"

# Add venv site-packages so ROS nodes find ultralytics/torch
export PYTHONPATH="$VENV/lib/python3.12/site-packages:$PYTHONPATH"

# Let Gazebo find textures via model://drone_yolo_detection/...
export GZ_SIM_RESOURCE_PATH="$WS/install/drone_yolo_detection/share:$GZ_SIM_RESOURCE_PATH"

# Use custom-trained model (falls back to base if not found)
if [ -f "$PROJECT_DIR/models/yolov8l_custom.pt" ]; then
    export YOLO_MODEL="$PROJECT_DIR/models/yolov8l_custom.pt"
    MODEL_LABEL="yolov8l_custom (cube/cylinder)"
else
    export YOLO_MODEL="$PROJECT_DIR/models/yolov8l.pt"
    MODEL_LABEL="yolov8l (COCO 80 classes)"
fi

echo "Starting Drone YOLOv8l Detection Simulation..."
echo "  Gazebo world  : drone_detection.sdf"
echo "  Model         : $MODEL_LABEL"
echo "  GPU           : $(python3 -c 'import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")')"
echo ""
echo "Controls: close the OpenCV window or press Ctrl+C to stop."
echo ""

ros2 launch drone_yolo_detection drone_detection.launch.py
