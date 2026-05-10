"""
Synthetic data collector — analytical bounding box projection.

Camera pose is known (we set it). Object poses are known (we set them).
Bounding boxes computed by projecting 3D corners to 2D.
No segmentation camera needed.

Classes:  0=cube  1=cylinder
"""

import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')

import os
import signal
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import numpy as np
import cv2
import time
import random
import threading
import math
from pathlib import Path
from collections import deque

from gz.transport13 import Node as GzNode
from gz.msgs10 import pose_pb2, boolean_pb2

# ── Dataset output ────────────────────────────────────────────────────────────
DATASET_ROOT = Path('/home/frank/文件/Project/Object_Detection_sim_in_Gazebo/datasets/custom_shapes')

# ── Camera intrinsics (matches SDF: hfov=1.3962634, 640×480) ─────────────────
IMG_W, IMG_H = 640, 480
HFOV = 1.3962634
FX = FY = (IMG_W / 2) / math.tan(HFOV / 2)   # ≈ 381.3
CX, CY = IMG_W / 2.0, IMG_H / 2.0

# ── Scene objects ─────────────────────────────────────────────────────────────
# (name, class_id, half_w, half_d, half_h)  — half-extents of 3D bounding box
OBJECTS = [
    ('cube_0',     0, 0.50, 0.50, 0.50),
    ('cube_1',     0, 0.40, 0.40, 0.40),
    ('cube_2',     0, 0.60, 0.60, 0.60),
    ('cube_3',     0, 0.35, 0.35, 0.35),
    ('cube_4',     0, 0.50, 0.50, 0.50),
    ('cube_5',     0, 0.45, 0.45, 0.45),
    ('cylinder_0', 1, 0.40, 0.40, 0.75),
    ('cylinder_1', 1, 0.50, 0.50, 0.60),
    ('cylinder_2', 1, 0.30, 0.30, 0.90),
    ('cylinder_3', 1, 0.45, 0.45, 0.70),
    ('cylinder_4', 1, 0.35, 0.35, 0.80),
    ('cylinder_5', 1, 0.40, 0.40, 0.65),
]

# ── Randomization bounds ──────────────────────────────────────────────────────
CAM_X = (-8.0, 8.0)
CAM_Y = (-8.0, 8.0)
CAM_Z = (4.0, 12.0)
OBJ_X = (-9.0, 9.0)
OBJ_Y = (-9.0, 9.0)

WORLD = 'data_collection'
MIN_BOX_PX = 10   # discard boxes smaller than this


def project_point(px, py, pz, cam_x, cam_y, cam_z):
    """
    Project world point to image coords for downward-facing camera.
    Camera pitch=pi/2: looks down (-Z), right=World -Y, up=World -X.
    Verified empirically: u = CX - FX*(py-cam_y)/depth, v = CY - FY*(px-cam_x)/depth
    Returns (u, v) or None if behind camera.
    """
    depth = cam_z - pz
    if depth <= 0.01:
        return None
    u = CX - FX * (py - cam_y) / depth
    v = CY - FY * (px - cam_x) / depth
    return u, v


def object_bbox(obj_x, obj_y, obj_z, hw, hd, hh, cam_x, cam_y, cam_z):
    """
    Project 3D bounding box of an object to 2D image AABB.
    Returns (x1, y1, x2, y2) in pixels, or None if not visible.
    """
    corners = [
        (obj_x + sx * hw, obj_y + sy * hd, obj_z + sz * hh)
        for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)
    ]
    us, vs = [], []
    for cx_, cy_, cz_ in corners:
        pt = project_point(cx_, cy_, cz_, cam_x, cam_y, cam_z)
        if pt:
            us.append(pt[0])
            vs.append(pt[1])
    if not us:
        return None
    x1, x2 = max(0, min(us)), min(IMG_W, max(us))
    y1, y2 = max(0, min(vs)), min(IMG_H, max(vs))
    if x2 - x1 < MIN_BOX_PX or y2 - y1 < MIN_BOX_PX:
        return None
    return int(x1), int(y1), int(x2), int(y2)


def imgmsg_to_cv2(msg):
    h, w = msg.height, msg.width
    arr = np.frombuffer(msg.data, dtype=np.uint8)
    enc = msg.encoding.lower()
    if enc == 'rgb8':
        return cv2.cvtColor(arr.reshape((h, w, 3)), cv2.COLOR_RGB2BGR)
    return arr.reshape((h, w, 3)).copy()


class DataCollectorNode(Node):
    def __init__(self):
        super().__init__('data_collector')

        self.declare_parameter('target_images', 3000)
        self.declare_parameter('output_split', 'train')

        self.target = self.get_parameter('target_images').value
        split = self.get_parameter('output_split').value

        self.img_dir = DATASET_ROOT / 'images' / split
        self.lbl_dir = DATASET_ROOT / 'labels' / split
        self.img_dir.mkdir(parents=True, exist_ok=True)
        self.lbl_dir.mkdir(parents=True, exist_ok=True)

        self.count = len(list(self.img_dir.glob('*.jpg')))
        self.get_logger().info(
            f'Resuming from {self.count}. Target: {self.target} | Split: {split}'
        )

        self.gz = GzNode()
        self.rgb_buf = deque(maxlen=1)
        self.lock = threading.Lock()

        # Current poses (updated in randomize_scene)
        self.cam_x = self.cam_y = 0.0
        self.cam_z = 6.0
        self.obj_poses = {}   # name → (x, y, z)

        self.sub_rgb = self.create_subscription(
            Image, '/drone/camera/image_raw', self.rgb_cb, 5)

        self._thread = threading.Thread(target=self._collection_thread, daemon=True)
        self._thread.start()
        self.get_logger().info('Data collector starting in 6s...')

    def rgb_cb(self, msg):
        with self.lock:
            self.rgb_buf.append(msg)

    def set_pose(self, name, x, y, z, yaw=0.0):
        req = pose_pb2.Pose()
        req.name = name
        req.position.x, req.position.y, req.position.z = float(x), float(y), float(z)
        req.orientation.z = math.sin(yaw / 2)
        req.orientation.w = math.cos(yaw / 2)
        self.gz.request(f'/world/{WORLD}/set_pose',
                        req, pose_pb2.Pose, boolean_pb2.Boolean, 500)

    def randomize_scene(self):
        # Camera (drone) position
        self.cam_x = random.uniform(*CAM_X)
        self.cam_y = random.uniform(*CAM_Y)
        self.cam_z = random.uniform(*CAM_Z)
        self.set_pose('iris', self.cam_x, self.cam_y, self.cam_z)

        # Object positions
        placed = []
        for name, cls_id, hw, hd, hh in OBJECTS:
            for _ in range(30):
                ox = random.uniform(*OBJ_X)
                oy = random.uniform(*OBJ_Y)
                if all((ox-px)**2 + (oy-py)**2 > 2.5 for px, py in placed):
                    placed.append((ox, oy))
                    break
            oz = hh   # bottom at ground level
            yaw = random.uniform(0, math.pi)
            self.set_pose(name, ox, oy, oz, yaw)
            self.obj_poses[name] = (ox, oy, oz)

    def compute_labels(self):
        labels = []
        for name, cls_id, hw, hd, hh in OBJECTS:
            if name not in self.obj_poses:
                continue
            ox, oy, oz = self.obj_poses[name]
            bbox = object_bbox(ox, oy, oz, hw, hd, hh,
                               self.cam_x, self.cam_y, self.cam_z)
            if bbox is None:
                continue
            x1, y1, x2, y2 = bbox
            cx = ((x1 + x2) / 2) / IMG_W
            cy = ((y1 + y2) / 2) / IMG_H
            bw = (x2 - x1) / IMG_W
            bh = (y2 - y1) / IMG_H
            labels.append((cls_id, cx, cy, bw, bh))
        return labels

    def _collection_thread(self):
        time.sleep(6.0)
        self.get_logger().info('Collection started')

        while rclpy.ok() and self.count < self.target:
            self.randomize_scene()
            time.sleep(0.4)   # let Gazebo render new frame

            with self.lock:
                if not self.rgb_buf:
                    time.sleep(0.5)
                    continue
                msg = self.rgb_buf[-1]

            labels = self.compute_labels()
            if not labels:
                continue

            frame = imgmsg_to_cv2(msg)
            stem = f'{self.count:06d}'
            cv2.imwrite(str(self.img_dir / f'{stem}.jpg'), frame,
                        [cv2.IMWRITE_JPEG_QUALITY, 95])
            with open(self.lbl_dir / f'{stem}.txt', 'w') as f:
                for cls, cx, cy, bw, bh in labels:
                    f.write(f'{cls} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n')

            self.count += 1
            if self.count % 50 == 0:
                self.get_logger().info(f'Collected {self.count}/{self.target}')

        self.get_logger().info(f'Done — {self.count} images in {DATASET_ROOT}')
        os.kill(os.getpid(), signal.SIGINT)


def main(args=None):
    rclpy.init(args=args)
    node = DataCollectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()
