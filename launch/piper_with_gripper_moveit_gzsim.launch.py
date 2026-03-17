"""
Launch the Piper arm + gripper in Gazebo Harmonic with MoveIt2.

Includes piper_with_gripper_gzsim.launch.py (Gazebo + controllers), then adds
move_group and RViz2 with the MoveIt MotionPlanning plugin.

Usage:
  ros2 launch agx_arm_gzsim piper_with_gripper_moveit_gzsim.launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    pkg_gzsim = get_package_share_directory("agx_arm_gzsim")
    pkg_moveit = get_package_share_directory("piper_with_gripper_moveit")

    # Build MoveIt config from piper_with_gripper_moveit, overriding:
    #   robot_description -> Gazebo URDF (gz_ros2_control hardware plugin)
    #   trajectory_execution -> sim-specific moveit_controllers.yaml
    moveit_config = (
        MoveItConfigsBuilder("piper", package_name="piper_with_gripper_moveit")
        .robot_description(
            file_path=os.path.join(
                pkg_gzsim, "urdf", "piper_with_gripper_gzsim.urdf.xacro"
            ),
            mappings={
                "initial_positions_file": os.path.join(
                    pkg_gzsim, "config", "initial_positions.yaml"
                )
            },
        )
        .trajectory_execution(
            file_path=os.path.join(pkg_gzsim, "config", "moveit_controllers.yaml")
        )
        .to_moveit_configs()
    )

    gzsim_launch = IncludeLaunchDescription(
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
        launch_arguments={"use_rviz": "false"}.items(),
    )

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {
                "use_sim_time": True,
                # Clamp joints that settle just outside their limit boundary.
                "start_state_max_bounds_error": 0.1,
            },
        ],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        output="log",
        arguments=["-d", os.path.join(pkg_moveit, "config", "moveit.rviz")],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            moveit_config.joint_limits,
            {"use_sim_time": True},
        ],
    )

    return LaunchDescription(
        [
            gzsim_launch,
            move_group_node,
            rviz_node,
        ]
    )
