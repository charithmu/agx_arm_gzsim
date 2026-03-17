"""
Launch the Piper arm + gripper in Gazebo Harmonic (visualization only, no MoveIt).

Usage:
  ros2 launch agx_arm_gzsim piper_with_gripper_gzsim.launch.py
  ros2 launch agx_arm_gzsim piper_with_gripper_gzsim.launch.py use_rviz:=false
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_gzsim = get_package_share_directory("agx_arm_gzsim")

    # Gazebo Harmonic resolves package:// URIs via GZ_SIM_RESOURCE_PATH.
    # We add the share parent so model://agx_arm_description/... resolves correctly.
    desc_share = get_package_share_directory("agx_arm_description")
    existing_gz_path = os.environ.get("GZ_SIM_RESOURCE_PATH", "")
    gz_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=os.path.dirname(desc_share)
        + (os.pathsep + existing_gz_path if existing_gz_path else ""),
    )

    declare_use_rviz = DeclareLaunchArgument(
        "use_rviz",
        default_value="true",
        description="Launch RViz for visualization",
    )
    declare_gz_args = DeclareLaunchArgument(
        "gz_args",
        default_value="",
        description="Extra arguments forwarded to gz sim (e.g. -v4 for verbose)",
    )

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare("agx_arm_gzsim"), "urdf", "piper_with_gripper_gzsim.urdf.xacro"]
            ),
            " initial_positions_file:=",
            PathJoinSubstitution(
                [FindPackageShare("agx_arm_gzsim"), "config", "initial_positions.yaml"]
            ),
        ]
    )
    robot_description = {
        "robot_description": ParameterValue(robot_description_content, value_type=str)
    }

    rsp_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    gz_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"])]
        ),
        launch_arguments={
            "gz_args": [
                LaunchConfiguration("gz_args"),
                " -r ",
                PathJoinSubstitution(
                    [FindPackageShare("agx_arm_gzsim"), "worlds", "empty.sdf"]
                ),
            ],
            "gz_version": "8",
            "on_exit_shutdown": "true",
        }.items(),
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="log",
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        parameters=[
            {
                "topic": "/robot_description",
                "name": "piper",
                "allow_renaming": True,
                "z": 0.0,
            }
        ],
    )

    jsb_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
        parameters=[{"use_sim_time": True}],
        output="screen",
    )
    arm_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arm_controller", "-c", "/controller_manager"],
        parameters=[{"use_sim_time": True}],
        output="screen",
    )
    gripper_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller", "-c", "/controller_manager"],
        parameters=[{"use_sim_time": True}],
        output="screen",
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        condition=IfCondition(LaunchConfiguration("use_rviz")),
        arguments=[
            "-d",
            PathJoinSubstitution([FindPackageShare("agx_arm_gzsim"), "config", "sim.rviz"]),
        ],
        parameters=[{"use_sim_time": True}],
        output="log",
    )

    # Sequencing: spawn after Gazebo is ready, then bring up controllers in order.
    delayed_spawn = TimerAction(period=3.0, actions=[spawn_entity])

    start_jsb_after_spawn = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[jsb_spawner],
        )
    )

    start_controllers_after_jsb = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=jsb_spawner,
            on_exit=[arm_spawner, gripper_spawner],
        )
    )

    return LaunchDescription(
        [
            gz_resource_path,
            declare_use_rviz,
            declare_gz_args,
            rsp_node,
            gz_sim_launch,
            clock_bridge,
            delayed_spawn,
            start_jsb_after_spawn,
            start_controllers_after_jsb,
            rviz_node,
        ]
    )
