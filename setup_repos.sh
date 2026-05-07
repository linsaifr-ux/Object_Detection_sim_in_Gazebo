#!/bin/bash
set -e

ARCH=$(dpkg --print-architecture)

echo "[1/4] Adding ROS 2 Jazzy key..."
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "[2/4] Adding ROS 2 Jazzy repo..."
echo "deb [arch=${ARCH} signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu noble main" \
  > /etc/apt/sources.list.d/ros2.list

echo "[3/4] Adding Gazebo Harmonic key..."
curl -sSL https://packages.osrfoundation.org/gazebo.gpg \
  -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg

echo "[4/4] Adding Gazebo Harmonic repo..."
echo "deb [arch=${ARCH} signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable noble main" \
  > /etc/apt/sources.list.d/gazebo-stable.list

echo "All repos added successfully."
