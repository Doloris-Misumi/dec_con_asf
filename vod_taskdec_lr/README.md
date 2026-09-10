# VoD TaskDec L+R Sandbox

This folder is an isolated View-of-Delft adaptation workspace for TaskDec L+R.
It intentionally avoids modifying the existing K-Radar training/evaluation code.

Current scope:

- Read the local VoD public dataset from `/home/hongsheng/vod/view_of_delft_PUBLIC`.
- Build LiDAR/Radar BEV proxy features from real VoD point clouds.
- Feed `spatial_features_2d` and `bev_feat` into a copied TaskDec A2Fusion module.
- Train with an ASF/OpenPCDet-style anchor head and detection loss.

Useful commands:

```bash
cd /home/hongsheng/dec_con_asf/vod_taskdec_lr
CUDA_VISIBLE_DEVICES=3 /home/hongsheng/miniconda3/envs/rl_3dod/bin/python -u smoke_taskdec_lr.py \
  --config configs/taskdec_lr_smoke.yml \
  --gpu 3 \
  --out logs/taskdec_lr_smoke_gpu3_result.json
```

```bash
cd /home/hongsheng/dec_con_asf
CUDA_VISIBLE_DEVICES=3 /home/hongsheng/miniconda3/envs/rl_3dod/bin/python -u -m vod_taskdec_lr.train_taskdec_lr_detection \
  --config vod_taskdec_lr/configs/taskdec_lr_anchor_train.yml \
  --gpu 3
```

Next scope after training starts:

- Add VoD prediction export and evaluation using the VoD/KITTI devkit.
- Train internal `ASF-like L+R` and `TaskDec L+R` baselines under the same protocol.

Evaluation command:

```bash
cd /home/hongsheng/dec_con_asf
CUDA_VISIBLE_DEVICES=3 /home/hongsheng/miniconda3/envs/rl_3dod/bin/python -u -m vod_taskdec_lr.eval_taskdec_lr_vod \
  --config vod_taskdec_lr/configs/taskdec_lr_anchor_train.yml \
  --gpu 3 \
  --batch-size 4 \
  --ckpt vod_taskdec_lr/runs/exp_260905_153718_VoDTaskDecLRAnchor_ep100_gpu3/checkpoints/model_98.pt \
         vod_taskdec_lr/runs/exp_260905_153718_VoDTaskDecLRAnchor_ep100_gpu3/checkpoints/model_99.pt
```
