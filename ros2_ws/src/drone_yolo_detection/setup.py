from setuptools import setup
import os
from glob import glob

package_name = 'drone_yolo_detection'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.sdf')),
        (os.path.join('share', package_name, 'models'), [f for f in glob('models/**/*', recursive=True) if os.path.isfile(f)]),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'materials', 'textures'), glob('materials/textures/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@example.com',
    description='YOLOv8l object detection from Gazebo drone camera feed',
    license='MIT',
    entry_points={
        'console_scripts': [
            'yolo_detector = drone_yolo_detection.yolo_detector:main',
            'detection_visualizer = drone_yolo_detection.detection_visualizer:main',
            'flight_controller = drone_yolo_detection.flight_controller:main',
            'data_collector = drone_yolo_detection.data_collector:main',
        ],
    },
)
