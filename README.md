# Real-Time Drone Object Detection in Gazebo

Real-time object detection from a simulated drone camera feed using YOLOv8l and Gazebo Harmonic, built on ROS 2 Jazzy.

## System Requirements

| Component | Version |
|-----------|---------|
| OS | Ubuntu 24.04 LTS |
| ROS 2 | Jazzy Jalisco |
| Gazebo | Harmonic 8.x |
| Python | 3.12 |
| CUDA | 12.1+ |
| GPU | NVIDIA (GTX 1070 or better) |

## Stack

```
Gazebo Harmonic  ──camera feed──►  ros_gz_image bridge
                                         │
                                         ▼
                                   YOLOv8l detector  ──►  annotated image
                                         │
                                         ▼
                                   OpenCV display window
```

- **Simulation**: Gazebo Harmonic with a custom iris quadrotor SDF
- **Detection model**: YOLOv8l (COCO 80 classes, 83.7 MB)
- **Camera**: 640×480 downward-facing, 30 FPS
- **GPU inference**: ~90 FPS on GTX 1070 with FP32

## Project Structure

```
Object_Detection_sim_in_Gazebo/
├── README.md
├── run.sh                        # Auto-flight + detection
├── run_manual.sh                 # Manual keyboard control + detection
├── setup_repos.sh                # Apt repo setup (run once, needs sudo)
├── models/
│   └── yolov8l.pt                # YOLOv8l weights (downloaded on first run)
├── venv/                         # Python virtual environment
└── ros2_ws/
    └── src/drone_yolo_detection/
        ├── drone_yolo_detection/
        │   ├── yolo_detector.py          # YOLOv8l ROS 2 inference node
        │   ├── detection_visualizer.py   # OpenCV display node
        │   └── flight_controller.py      # Autonomous circle flight
        ├── launch/
        │   ├── drone_detection.launch.py # Auto-flight launch
        │   └── drone_manual.launch.py    # Manual control launch
        ├── worlds/
        │   └── drone_detection.sdf       # Gazebo world + iris drone
        └── materials/
            └── textures/                 # Procedural grass PBR textures
                ├── grass_albedo.png
                ├── grass_normal.png
                └── grass_roughness.png
```

## Installation

### 1. Add apt repositories (one-time, requires sudo)

```bash
sudo bash setup_repos.sh
sudo apt update
sudo apt install -y ros-jazzy-desktop ros-jazzy-ros-gz gz-harmonic \
    ros-jazzy-mavros ros-jazzy-mavros-extras python3-rosdep \
    ros-jazzy-teleop-twist-keyboard
```

### 2. Set up Python environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install "torch==2.3.1+cu121" "torchvision==0.18.1+cu121" \
    --index-url https://download.pytorch.org/whl/cu121
pip install ultralytics opencv-python-headless numpy colcon-common-extensions
```

### 3. Build the ROS 2 workspace

```bash
source /opt/ros/jazzy/setup.bash
source venv/bin/activate
colcon build --symlink-install
```

### 4. Download YOLOv8l weights

Weights are downloaded automatically on first run. To pre-download:

```bash
source venv/bin/activate
python3 -c "from ultralytics import YOLO; YOLO('yolov8l.pt')"
mv yolov8l.pt models/
```

## Usage

### Autonomous mode (drone circles automatically)

```bash
bash run.sh
```

The drone takes off after ~5 seconds and flies a slow circle at 5 m altitude. YOLOv8l detections appear as green bounding boxes in the OpenCV window.

### Manual control mode

```bash
bash run_manual.sh
```

A keyboard teleop terminal opens after ~4 seconds.

| Key | Action |
|-----|--------|
| `i` | Fly forward |
| `,` | Fly backward |
| `j` / `l` | Yaw left / right |
| `u` / `o` | Strafe left / right |
| `t` / `b` | Ascend / Descend |
| `k` | Hover (stop all motion) |
| `q` / `z` | Increase / decrease max speed |

Press `Ctrl+C` in the launch terminal to stop everything.

## ROS 2 Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/drone/camera/image_raw` | `sensor_msgs/Image` | Raw 640×480 camera feed from Gazebo |
| `/drone/detection/image` | `sensor_msgs/Image` | Annotated image with bounding boxes |
| `/drone/detection/results` | `std_msgs/String` | JSON array of detections per frame |
| `/iris/cmd_vel` | `geometry_msgs/Twist` | Drone velocity command input |

### Detection result format

```json
[
  {
    "label": "person",
    "confidence": 0.873,
    "bbox": [x1, y1, x2, y2]
  }
]
```

## Tuning

Edit parameters in the launch files or pass them at runtime:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `confidence` | `0.45` | Detection confidence threshold |
| `imgsz` | `640` | Inference image size (px) |
| `device` | `cuda:0` | Torch device (`cuda:0` or `cpu`) |
| `altitude` | `5.0` | Auto-flight altitude (m) |
| `circle_radius` | `4.0` | Auto-flight circle radius (m) |
| `angular_speed` | `0.3` | Auto-flight angular velocity (rad/s) |

## Regenerating Grass Textures

The grass PBR textures are generated procedurally. To regenerate at higher resolution, edit `SIZE = 1024` in the script and run:

```bash
source venv/bin/activate
python3 ros2_ws/src/drone_yolo_detection/materials/generate_grass.py
colcon build --symlink-install
```
