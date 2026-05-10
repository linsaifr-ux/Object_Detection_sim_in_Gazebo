import sys
if sys.prefix == '/home/frank/文件/Project/Object_Detection_sim_in_Gazebo/venv':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/frank/文件/Project/Object_Detection_sim_in_Gazebo/install/drone_yolo_detection'
