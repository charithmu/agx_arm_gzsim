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
| `piper_with_gripper_moveit` | – |

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

### With MoveIt2 (Gazebo + move_group + RViz MotionPlanning)

```bash
ros2 launch agx_arm_gzsim piper_with_gripper_moveit_gzsim.launch.py
```

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

MoveIt reuses the `piper_with_gripper_moveit` package for SRDF, kinematics, and joint limits, with the robot description and controller config overridden for simulation.

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
- **Initial positions**: `joint2`, `joint3`, and `gripper_joint1` all have `0.0` as a joint limit. They start at `0.01`, `-0.01`, and `0.001` respectively to avoid floating-point boundary violations that prevent MoveIt planning.
- **Controllers use position interface**: this matches the Gazebo Harmonic reference setup (e.g. panda) and requires no PID tuning. The `GazeboSimSystem` plugin handles the position-to-effort conversion internally.
