# R1Lite Terminal-Only Inference

This is the terminal equivalent of the Android EHI flow in [pick_up_anything_user_guideline.md](./pick_up_anything_user_guideline.md).

## Read This First

This document assumes you are running `EFMNode` on a machine that already has:

- ROS2 available,
- network access to the robot,
- the ability to subscribe and publish the robot ROS topics in real time.

If you are on a cluster compute node without ROS2 and without sudo access, this is **not** the right document for that machine.

In practice:

- `robot computer / ROS host`: needs ROS2, talks to the robot, runs teleop / control / topic I/O
- `compute node`: can be used for model-only or offline inference experiments, but not this direct `EFMNode -> robot` control path

The key difference is:

- The Android app sends instructions through `rosbridge`.
- This terminal workflow writes instructions directly into `EFMNode/scheduler/instruction/instruction.txt`.
- `EFMNode` then reads that file and runs inference without needing the tablet app.

## Do I Need ROS On The Compute Node?

For the workflow in this file: **yes, the host running `EFMNode` needs ROS2**.

Why:

- [scheduler.py](/local/galaxea/EFMNode/scheduler/scheduler.py) always creates a `Ros2Bridge`
- [ros2_bridge.py](/local/galaxea/EFMNode/core/communication/ros2_bridge.py) imports `rclpy` and directly subscribes to camera / state topics and publishes robot actions
- [run_r1lite_terminal.sh](/local/galaxea/EFMNode/scripts/run_r1lite_terminal.sh) only sources ROS if it already exists; it does not install ROS for you

So if your compute node does not have ROS2, it cannot run this real-robot terminal-control path as written.

## What To Do In Your Setup

If your teleop / robot-control machine is already running on `192.168.1.25`, that is the machine that should run the terminal-control path in this file, not the cluster compute node.

Use the cluster compute node only for one of these:

- offline / open-loop model evaluation
- checkpoint inspection
- model-only serving experiments

Use the robot computer for:

- `EFMNode`
- ROS topic I/O
- sending terminal instructions to the live robot

## If You Only Want To Test Model Inference First

You do **not** need ROS for a pure model-only test.

Two reasonable non-ROS options are:

1. Open-loop evaluation with [eval_open_loop.py](/local/galaxea/GalaxeaVLA/scripts/eval_open_loop.py) or [eval_open_loop.sh](/local/galaxea/GalaxeaVLA/scripts/run/eval_open_loop.sh)
2. Model-only websocket serving with [policy_server.py](/local/galaxea/EFMNode/serving/policy_server.py)

The first option is the safest if your immediate goal is just: "does the checkpoint load and produce actions?"

The terminal-control workflow below is only for the live robot path.

## When This Path Fits

Use this terminal path when:

- you can connect the host to the `R1Lite` over Ethernet,
- you can start the robot and ROS2 normally,
- you want to type instructions from a shell instead of using the tablet,
- you are okay with text-only commands instead of the app UI.

This path uses `use_vlm = false`, so it does not depend on the EHI app or `rosbridge`.

## 1. Bring Up Robot + Network

Follow the same robot-side steps from:

- [pick_up_anything_user_guideline.md](./pick_up_anything_user_guideline.md)
- [pp-how_to_set_up_the_network_between_the_host_and_robot.md](./pp-how_to_set_up_the_network_between_the_host_and_robot.md)
- [pp-ros2_discovery_setup.md](./pp-ros2_discovery_setup.md)

At minimum, make sure the host can reach the robot:

```bash
ping 10.42.0.<ROBOT_PORT>
ssh r1lite@10.42.0.<ROBOT_PORT>
```

On the robot, start the usual robot-side stack:

```bash
cd ~
chmod +x ./model_test.sh
./model_test.sh
```

That script comes from [model_test.sh](/local/galaxea/GalaxeaVLA/docs/supports/pick_up_anything_demo/model_test.sh).

## 2. Start Terminal-Mode EFMNode

Run this on the ROS-enabled host or robot computer, not on a cluster node without ROS:

```bash
cd /local/galaxea/EFMNode
./scripts/run_r1lite_terminal.sh \
  --model-path /local/galaxea/outputs/galaxea_finetune/real/g0plus_r1lite_openworld_all/2026-04-01_01-32-11/checkpoints/step_20000
```

Notes:

- The default config is [config.r1lite_terminal.toml](/local/galaxea/EFMNode/config.r1lite_terminal.toml).
- If you need a different config, pass `--config-path /abs/path/to/file.toml`.
- The script clears the instruction file to `nothing` before startup so the robot does not replay an old command.

## 3. Send Instructions From Terminal

Open a second terminal on that same ROS-enabled host and run:

```bash
cd /local/galaxea/EFMNode
./scripts/send_terminal_instruction.sh "pick up the red bottle"
```

Other useful commands:

```bash
./scripts/send_terminal_instruction.sh reset
./scripts/send_terminal_instruction.sh nothing
```

## 4. What Changed Relative to the App Flow

The Android flow starts three host-side pieces:

- `EFMNode`
- `g0_vlm_node`
- `rosbridge_server`

For terminal-only control, you only need `EFMNode` for the text-command path.

In the local codebase:

- [instruction.py](/local/galaxea/EFMNode/scheduler/instruction/instruction.py) already supports a file-based instruction source when `use_vlm = false`.
- [run_r1lite_terminal.sh](/local/galaxea/EFMNode/scripts/run_r1lite_terminal.sh) starts that mode.
- [send_terminal_instruction.sh](/local/galaxea/EFMNode/scripts/send_terminal_instruction.sh) updates the instruction file safely from the shell.

## 5. If You Want the Docker Version Later

The official pick-up-anything guide uses a Docker image and launches:

- [g0plus_hs_start_v1.sh](/local/galaxea/GalaxeaVLA/docs/supports/pick_up_anything_demo/g0plus_hs_start_v1.sh)
- [docker_g0plus_hs_start_v1.sh](/local/galaxea/GalaxeaVLA/docs/supports/pick_up_anything_demo/docker_g0plus_hs_start_v1.sh)

If you stay with that Docker path, the same terminal idea still applies, but you would run the instruction sender inside the container path where `EFMNode` is actually running.

## 6. Current Limits

- This terminal path is text-driven; it does not reproduce the tablet UI preview or spoken input.
- If your checkpoint specifically depends on VLM-generated bounding boxes, you would need an extra terminal-side VLM step rather than the plain file-based instruction path.
- ROS2, GPU driver, and robot connectivity still need to be working exactly as they do for the app-based demo.
