import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
import numpy as np
import cv2
import json


def imgmsg_to_cv2(msg):
    h, w = msg.height, msg.width
    arr = np.frombuffer(msg.data, dtype=np.uint8)
    enc = msg.encoding.lower()
    if enc == 'rgb8':
        return cv2.cvtColor(arr.reshape((h, w, 3)), cv2.COLOR_RGB2BGR)
    elif enc == 'bgr8':
        return arr.reshape((h, w, 3)).copy()
    elif enc in ('mono8', '8uc1'):
        return arr.reshape((h, w))
    else:
        return arr.reshape((h, w, 3)).copy()


class DetectionVisualizerNode(Node):
    def __init__(self):
        super().__init__('detection_visualizer')

        self.latest_detections = []

        self.sub_image = self.create_subscription(
            Image, '/drone/detection/image', self.image_callback, 10
        )
        self.sub_det = self.create_subscription(
            String, '/drone/detection/results', self.detection_callback, 10
        )

        self.get_logger().info('Detection visualizer ready — press Q in window to quit')

    def detection_callback(self, msg):
        self.latest_detections = json.loads(msg.data)

    def image_callback(self, msg):
        frame = imgmsg_to_cv2(msg)
        info = f'Objects detected: {len(self.latest_detections)}'
        cv2.putText(frame, info, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 200, 255), 2)
        cv2.imshow('Drone YOLOv8l Detection', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            rclpy.shutdown()

    def destroy_node(self):
        cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = DetectionVisualizerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
