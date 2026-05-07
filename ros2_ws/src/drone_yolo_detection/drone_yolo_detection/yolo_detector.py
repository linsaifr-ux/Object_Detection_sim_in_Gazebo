import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from ultralytics import YOLO
import numpy as np
import cv2
import json
import os

MODEL_PATH = os.path.expanduser(
    '~/文件/Project/Object_Detection_sim_in_Gazebo/models/yolov8l.pt'
)

ENCODING_CHANNELS = {
    'rgb8': ('RGB', 3), 'bgr8': ('BGR', 3),
    'mono8': ('GRAY', 1), '8UC1': ('GRAY', 1),
    'rgba8': ('RGBA', 4), 'bgra8': ('BGRA', 4),
}


def imgmsg_to_cv2(msg):
    enc = msg.encoding.lower()
    h, w = msg.height, msg.width
    arr = np.frombuffer(msg.data, dtype=np.uint8)
    if enc in ('rgb8',):
        frame = arr.reshape((h, w, 3))
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    elif enc in ('bgr8',):
        return arr.reshape((h, w, 3)).copy()
    elif enc in ('mono8', '8uc1'):
        return arr.reshape((h, w))
    elif enc in ('rgba8',):
        frame = arr.reshape((h, w, 4))
        return cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
    elif enc in ('bgra8',):
        frame = arr.reshape((h, w, 4))
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    else:
        raise ValueError(f'Unsupported encoding: {msg.encoding}')


def cv2_to_imgmsg(frame):
    msg = Image()
    msg.height, msg.width = frame.shape[:2]
    msg.encoding = 'bgr8'
    msg.step = msg.width * 3
    msg.data = frame.tobytes()
    return msg


class YoloDetectorNode(Node):
    def __init__(self):
        super().__init__('yolo_detector')

        self.declare_parameter('camera_topic', '/drone/camera/image_raw')
        self.declare_parameter('confidence', 0.45)
        self.declare_parameter('device', 'cuda:0')
        self.declare_parameter('imgsz', 640)

        camera_topic = self.get_parameter('camera_topic').value
        self.conf = self.get_parameter('confidence').value
        self.device = self.get_parameter('device').value
        self.imgsz = self.get_parameter('imgsz').value

        self.get_logger().info(f'Loading YOLOv8l from {MODEL_PATH}')
        self.model = YOLO(MODEL_PATH)
        self.model.to(self.device)
        self.get_logger().info(f'YOLOv8l loaded on {self.device}')

        self.sub = self.create_subscription(Image, camera_topic, self.image_callback, 10)
        self.pub_image = self.create_publisher(Image, '/drone/detection/image', 10)
        self.pub_detections = self.create_publisher(String, '/drone/detection/results', 10)

        self.get_logger().info(f'Subscribed to {camera_topic}')

    def image_callback(self, msg):
        frame = imgmsg_to_cv2(msg)

        results = self.model(
            frame,
            imgsz=self.imgsz,
            conf=self.conf,
            device=self.device,
            verbose=False,
        )

        detections = []
        annotated = frame.copy()

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                label = self.model.names[int(box.cls[0])]
                detections.append({'label': label, 'confidence': round(conf, 3),
                                   'bbox': [x1, y1, x2, y2]})
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(annotated, f'{label} {conf:.2f}', (x1, y1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        det_msg = String()
        det_msg.data = json.dumps(detections)
        self.pub_detections.publish(det_msg)

        out_msg = cv2_to_imgmsg(annotated)
        out_msg.header = msg.header
        self.pub_image.publish(out_msg)


def main(args=None):
    rclpy.init(args=args)
    node = YoloDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
