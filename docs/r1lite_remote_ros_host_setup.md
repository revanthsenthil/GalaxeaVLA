# R1Lite Remote ROS Host Setup

This guide is for the case where:

- the robot computer is already running the low-level robot controllers,
- a separate host PC runs ROS2 Humble and `EFMNode`,
- the host PC sends commands to the robot over the network.

Example host:

- `revanths@192.168.1.10`

## What Must Live On The Host PC

The host needs:

- ROS2 Humble
- `GalaxeaVLA/`
- `EFMNode/`
- your fine-tuned checkpoint directory
- the `paligemma-3b-pt-224` pretrained backbone files

The current fine-tuned checkpoint also contains absolute paths in `config.yaml`, so those paths must either:

- exist on the host exactly as written, or
- be rewritten before use

## Recommended Transfer Flow

From the source machine, prepare a deployment bundle:

```bash
cd /local/galaxea
./prepare_r1lite_host_bundle.sh \
  --checkpoint-dir /local/galaxea/outputs/galaxea_finetune/real/g0plus_r1lite_openworld_all/2026-04-01_01-32-11/checkpoints/step_20000 \
  --output-dir /local/galaxea/deploy/r1lite_infer_bundle \
  --remote-root /home/revanths/r1lite_infer_bundle
```

This bundle includes:

- `model/config.yaml`
- `model/dataset_stats.json`
- `model/model.pt` or `model_state_dict.pt`
- `model/efmnode.toml`
- `paligemma-3b-pt-224/`

Copy the bundle and source trees to the host:

```bash
rsync -avh --progress /local/galaxea/deploy/r1lite_infer_bundle/ revanths@192.168.1.10:/home/revanths/r1lite_infer_bundle/
rsync -avh --progress --exclude .git --exclude .venv /local/galaxea/GalaxeaVLA/ revanths@192.168.1.10:/home/revanths/GalaxeaVLA/
rsync -avh --progress --exclude .git /local/galaxea/EFMNode/ revanths@192.168.1.10:/home/revanths/EFMNode/
```

`scp -r` also works, but `rsync` is easier to resume for multi-GB transfers.

## Host Setup On 192.168.1.10

After ROS2 Humble is installed:

```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=0
export ROS_DOMAIN_ID=<match-the-robot-domain>
```

Then install the Python environment:

```bash
cd ~/GalaxeaVLA
uv sync --index-strategy unsafe-best-match
source .venv/bin/activate
uv pip install -e .
```

If `EFMNode` later needs websocket serving/client mode, also install:

```bash
python -m pip install websockets
```

## Verify ROS Connectivity First

Before launching inference, confirm the host can see the robot graph:

```bash
ros2 node list
ros2 topic list
```

If discovery does not work with `ROS_DOMAIN_ID` alone, follow:

- [pp-ros2_discovery_setup.md](./pp-ros2_discovery_setup.md)

## Launch Sequence

1. Stop teleop publishers so they are not competing with inference for `/motion_target/*`.
2. On the host PC:

```bash
source /opt/ros/humble/setup.bash
cd ~/GalaxeaVLA
source .venv/bin/activate
cd ~/EFMNode
./scripts/preflight_r1lite_inference.sh --model-path /home/revanths/r1lite_infer_bundle/model
./scripts/run_r1lite_terminal.sh --model-path /home/revanths/r1lite_infer_bundle/model
```

3. In a second terminal on the host:

```bash
source /opt/ros/humble/setup.bash
cd ~/GalaxeaVLA
source .venv/bin/activate
cd ~/EFMNode
./scripts/send_terminal_instruction.sh "pick up the red bottle"
```

## Important Notes

- `EFMNode` now accepts either `model_state_dict.pt` or `model.pt` for PyTorch inference.
- The host must see the expected robot topics, especially the head camera topic.
- If the head camera topic is missing, `EFMNode` will not produce live observations.
- The checkpoint alone is not enough; the Paligemma pretrained files are also required for model construction.
