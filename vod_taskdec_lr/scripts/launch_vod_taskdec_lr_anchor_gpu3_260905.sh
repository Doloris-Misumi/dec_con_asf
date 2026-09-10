#!/usr/bin/env bash
set -euo pipefail

cd /home/hongsheng/dec_con_asf
export CUDA_VISIBLE_DEVICES=3

TS="$(date +%y%m%d_%H%M%S)"
RUN_NAME="exp_${TS}_VoDTaskDecLRAnchor_ep100_gpu3"
LOG_DIR="vod_taskdec_lr/logs/launcher"
LOG_PATH="${LOG_DIR}/vod_taskdec_lr_anchor_ep100_gpu3_${TS}.log"

mkdir -p "${LOG_DIR}"
echo "[launcher] run_name=${RUN_NAME}"
echo "[launcher] log_path=${LOG_PATH}"

/home/hongsheng/miniconda3/envs/rl_3dod/bin/python -u -m vod_taskdec_lr.train_taskdec_lr_detection \
  --config vod_taskdec_lr/configs/taskdec_lr_anchor_train.yml \
  --gpu 3 \
  --run-name "${RUN_NAME}" \
  --epochs 100 \
  --batch-size 2 \
  --num-workers 0 \
  2>&1 | tee "${LOG_PATH}"
