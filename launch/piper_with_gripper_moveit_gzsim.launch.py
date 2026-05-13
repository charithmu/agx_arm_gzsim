"""
Launch Piper + gripper in Gazebo Harmonic with MoveIt2.

Gazebo provides ros2_control hardware via the gz_ros2_control plugin embedded in
the sim URDF. move_group connects to arm_controller / gripper_controller action
servers. RViz is opened with the MotionPlanning panel for interactive GUI control.

Architecture
------------
* piper_with_gripper_gzsim.launch.py  – Gazebo, RSP, controllers (included below)
* agx_arm_moveit _moveit_config_builder – SRDF, kinematics, planning pipelines
  (borrowed, not copied; stays in sync with upstream agx_arm_moveit automatically)
* agx_arm_gzsim/config/moveit_controllers.yaml – only sim-specific override:
  maps MoveIt to the ros2_control FollowJointTrajectory action servers

Usage
-----
  ros2 launch agx_arm_gzsim piper_with_gripper_moveit_gzsim.launch.py
  ros2 launch agx_arm_gzsim piper_with_gripper_moveit_gzsim.launch.py gz_args:="-v4"
"""

import sys
import yaml
from pathlib import Path

from ament_index_python.packages import get_package_share_directory

# Borrow agx_arm_moveit's config builder so SRDF, kinematics and planning
# pipelines stay in sync with the upstream package without copying anything.
sys.path.insert(
    0, str(Path(get_package_share_directory("agx_arm_moveit")) / "launch")
)
from _moveit_config_builder import build_moveit_config  # noqa: E402

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _launch_moveit(context):
    pkg_gzsim = get_package_share_directory("agx_arm_gzsim")
    pkg_moveit = get_package_share_directory("agx_arm_moveit")

    # All MoveIt config (SRDF, kinematics, planning pipelines, joint limits)
    # comes from agx_arm_moveit via the shared builder – no duplication here.
    moveit_config = build_moveit_config(context)

    # Override trajectory execution only: sim uses ros2_control action servers,
    # not the real-arm CAN interface.
    with open(Path(pkg_gzsim) / "config" / "moveit_controllers.yaml") as f:
        moveit_config.trajectory_execution = yaml.safe_load(f)

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {
                "use_sim_time": True,
                # Joints that settle just outside their limit boundary are still valid.
                "start_state_max_bounds_error": 0.1,
            },
        ],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        output="log",
        # Use agx_arm_moveit's RViz config which includes the MotionPlanning panel.
        arguments=["-d", str(Path(pkg_moveit) / "config" / "moveit.rviz")],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            moveit_config.joint_limits,
            {"use_sim_time": True},
        ],
    )

    return [move_group_node, rviz_node]


def generate_launch_description():
    return LaunchDescription(
        [
            # Fixed for this launch: piper + gripper.
            # Declared so build_moveit_config() can read them from the context.
            DeclareLaunchArgument("arm_type", default_value="piper"),
            DeclareLaunchArgument("effector_type", default_value="agx_gripper"),
            DeclareLaunchArgument("revo2_type", default_value="left"),
            DeclareLaunchArgument(
                "tcp_offset",
                default_value="[0.0, 0.0, 0.0, 0.0, 0.0, 0.0]",
                description="TCP offset [x, y, z, rx, ry, rz] in metres/radians.",
            ),
            DeclareLaunchArgument(
                "gz_args",
                default_value="",
                description="Extra arguments forwarded to gz sim (e.g. -v4 for verbose).",
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [
                        PathJoinSubstitution(
                            [
                                FindPackageShare("agx_arm_gzsim"),
                                "launch",
                                "piper_with_gripper_gzsim.launch.py",
                            ]
                        )
                    ]
                ),
                launch_arguments={
                    "use_rviz": "false",
                    "gz_args": LaunchConfiguration("gz_args"),
                }.items(),
            ),
            OpaqueFunction(function=_launch_moveit),
        ]
    )
