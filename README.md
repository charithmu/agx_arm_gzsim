# agx_arm_gzsim

Gazebo Harmonic simulation for the **Piper 6-DOF arm with parallel-jaw gripper**.  
Supports standalone visualization and full MoveIt2 motion planning.

## Prerequisites

| Dependency | Version |
|---|---|
| ROS 2 | Jazzy |
| Gazebo | Harmonic (gz-sim 8) |
| gz_ros2_control | 1.2+ |
| `agx_arm_description` | – |
| `agx_arm_moveit` | – |

## Build

```bash
cd <workspace>
colcon build --packages-select agx_arm_gzsim
source install/setup.bash
```

## Launch

### Visualization only (Gazebo + RViz)

```bash
ros2 launch agx_arm_gzsim piper_with_gripper_gzsim.launch.py
```

Optional arguments:
- `use_rviz:=false` — skip RViz
- `gz_args:="-v4"` — pass extra flags to gz sim (e.g. verbose logging)
- `tcp_offset_xyz:="0 0 0.1358"` — publish `tcp_link` in TF at a fixed offset from `gripper_base`
- `tcp_offset_rpy:="0 0 0"` — rotate the published `tcp_link` frame if needed

### With MoveIt2 (Gazebo + move_group + RViz MotionPlanning)

```bash
ros2 launch agx_arm_gzsim piper_with_gripper_moveit_gzsim.launch.py
```

Optional arguments:
- `tcp_offset:="[0.0, 0.0, 0.1358, 0.0, 0.0, 0.0]"` — MoveIt TCP offset `[x, y, z, rx, ry, rz]`; defaults to the midpoint between the gripper jaws

In RViz, use the **MotionPlanning** panel to plan and execute trajectories for the `arm` and `gripper` planning groups.

## Architecture

```
piper_with_gripper_moveit_gzsim.launch.py
├── piper_with_gripper_gzsim.launch.py
│   ├── robot_state_publisher      (publishes /robot_description)
│   ├── gz sim                     (Gazebo Harmonic, empty world)
│   ├── ros_gz_bridge              (/clock bridge)
│   ├── gz spawn                   (spawns robot, starts controller_manager)
│   ├── joint_state_broadcaster
│   ├── arm_controller             (JointTrajectoryController, position)
│   └── gripper_controller         (JointTrajectoryController, position)
├── move_group                     (MoveIt2, OMPL planning)
└── rviz2                          (MoveIt MotionPlanning plugin)
```

MoveIt reuses the `agx_arm_moveit` package for SRDF, kinematics, and joint limits, with only the trajectory execution config overridden for simulation.

## Package structure

```
config/
  initial_positions.yaml    Joint start positions (slightly inside limit boundaries)
  ros2_controllers.yaml     Controller manager + JTC config for Gazebo
  moveit_controllers.yaml   MoveIt controller manager + trajectory execution tolerances
  sim.rviz                  RViz config for visualization-only launch
launch/
  piper_with_gripper_gzsim.launch.py          Gazebo + RViz (no MoveIt)
  piper_with_gripper_moveit_gzsim.launch.py   Gazebo + MoveIt + RViz
urdf/
  piper_with_gripper_gzsim.urdf.xacro   Top-level robot description for Gazebo
  piper_gzsim.ros2_control.xacro        ros2_control hardware interfaces
worlds/
  empty.sdf                 Flat ground plane world
```

## Notes

- **Headless display**: if running without a physical display, set `DISPLAY=:1` before launching (or start a virtual framebuffer with `Xvfb :1`).
- **Initial positions**: keep the startup pose strictly inside the URDF joint limits. For Piper + gripper, `joint2`, `joint3`, and `gripper_joint1` have `0.0` as one of their hard stops, so they start at `0.01`, `-0.01`, and `0.001` instead of exactly on the boundary.
- **TCP frame**: Gazebo now publishes `tcp_link` into TF from the sim overlay, with the default offset placed at the midpoint between the gripper jaws (`gripper_base -> tcp_link = [0, 0, 0.1358]`). The MoveIt launch uses the same default offset so planning and TF agree out of the box.
- **Controllers use position interface**: this matches the Gazebo Harmonic reference setup (e.g. panda) and requires no PID tuning. The `GazeboSimSystem` plugin handles the position-to-effort conversion internally.
