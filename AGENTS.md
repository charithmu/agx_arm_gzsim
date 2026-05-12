# agx_arm_gzsim Agent Guide

- This package is workspace-owned (we own it, unlike upstream-frozen `agx_arm_ros` and `pyAgxArm`). Improve it when needed to keep sim/real parity or to host sim-side launch glue for other packages.
- This package is the Gazebo simulation overlay for Piper Studio and should mirror the real stack as closely as practical.
- Keep simulation-specific controllers, worlds, and sensor plugins here rather than pushing them into higher-level packages.
- When adding wrist cameras or perception fixtures, preserve the same mount names, TF frames, and topic expectations intended for hardware.
- Keep controller names, planning groups, and robot-description semantics aligned with `agx_arm_ros` and `agx_arm_motion`.
- Prefer parameterized simulation assets over one-off demo-specific branches.