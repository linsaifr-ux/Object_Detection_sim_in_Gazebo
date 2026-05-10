import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('drone_yolo_detection')
    world = os.path.join(pkg, 'worlds', 'data_collection.sdf')

    split_arg = DeclareLaunchArgument('output_split', default_value='train')
    images_arg = DeclareLaunchArgument('target_images', default_value='3000')

    gz_sim = ExecuteProcess(
        cmd=['gz', 'sim', '-r', '--headless-rendering', world],
        output='screen',
    )

    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='gz_ros_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
        output='screen',
    )

    gz_image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        name='gz_rgb_bridge',
        arguments=['/drone/camera/image_raw'],
        output='screen',
    )

    data_collector = Node(
        package='drone_yolo_detection',
        executable='data_collector',
        name='data_collector',
        parameters=[{
            'target_images': LaunchConfiguration('target_images'),
            'output_split':  LaunchConfiguration('output_split'),
        }],
        output='screen',
    )

    return LaunchDescription([
        split_arg,
        images_arg,
        gz_sim,
        TimerAction(period=4.0, actions=[gz_bridge, gz_image_bridge]),
        TimerAction(period=6.0, actions=[data_collector]),
    ])
