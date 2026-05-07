import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('drone_yolo_detection')
    world = os.path.join(pkg, 'worlds', 'drone_detection.sdf')

    gz_sim = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world],
        output='screen',
    )

    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='gz_ros_bridge',
        arguments=[
            '/iris/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
        output='screen',
    )

    gz_image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        name='gz_image_bridge',
        arguments=['/drone/camera/image_raw'],
        output='screen',
    )

    # Keyboard teleop → drone cmd_vel
    teleop = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop',
        remappings=[('/cmd_vel', '/iris/cmd_vel')],
        output='screen',
        prefix='gnome-terminal --',
    )

    yolo_detector = Node(
        package='drone_yolo_detection',
        executable='yolo_detector',
        name='yolo_detector',
        parameters=[{
            'camera_topic': '/drone/camera/image_raw',
            'confidence': 0.45,
            'device': 'cuda:0',
            'imgsz': 640,
        }],
        output='screen',
    )

    visualizer = Node(
        package='drone_yolo_detection',
        executable='detection_visualizer',
        name='detection_visualizer',
        output='screen',
    )

    return LaunchDescription([
        gz_sim,
        TimerAction(period=3.0, actions=[gz_bridge, gz_image_bridge]),
        TimerAction(period=4.0, actions=[teleop]),
        TimerAction(period=5.0, actions=[yolo_detector]),
        TimerAction(period=6.0, actions=[visualizer]),
    ])
