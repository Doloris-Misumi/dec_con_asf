#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/hongsheng/dec_con_asf/vod_taskdec_native/L4DR_taskdec
CONDA_ENV=/home/hongsheng/miniconda3/envs/rl_3dod
LOGDIR=/home/hongsheng/dec_con_asf/logs/launcher
LOG=${LOGDIR}/l4dr_vod_repro_g23_260910.log
STATUS=${LOGDIR}/l4dr_vod_repro_g23_260910.status
TAG=l4dr_vod_repro_ep100_g23_260910

mkdir -p "${LOGDIR}"
cd "${ROOT}/tools"
export PATH="${CONDA_ENV}/bin:${PATH}"
export CONDA_PREFIX="${CONDA_ENV}"

{
  echo "Started at $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Repo: ${ROOT}"
  echo "Config: cfgs/VoD_models/L4DR.yaml"
  echo "Extra tag: ${TAG}"
  echo "Python: $(which python)"
  echo "CUDA_VISIBLE_DEVICES=2,3"
  echo

  set +e
  CUDA_VISIBLE_DEVICES=2,3 bash scripts/dist_train.sh 2 \
    --cfg_file cfgs/VoD_models/L4DR.yaml \
    --extra_tag "${TAG}" \
    --sync_bn \
    --workers 4 \
    --ckpt_save_interval 1 \
    --max_ckpt_save_num 30 \
    --num_epochs_to_eval 1
  rc=$?
  set -e

  echo
  echo "Finished at $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Exit code: ${rc}"
  echo "${rc}" > "${STATUS}"
  exit "${rc}"
} > "${LOG}" 2>&1
