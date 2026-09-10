#!/usr/bin/env bash
set -euo pipefail

cd /home/hongsheng/K-Radar-main

PY=/home/hongsheng/miniconda3/envs/rl_3dod/bin/python
CONFIG=./configs/v1_0/cfg_A2F_scl_final_local.yml
MODEL=./pretrained/v1_0_official/A2F_v1_0_model_10.pt
GPU="${1:?usage: launch_official_asf_availability_eval_260902.sh <gpu> <mode> [mode...]}"
shift

export PYTHONPATH=/home/hongsheng/K-Radar-main/ops:/home/hongsheng/K-Radar-main:${PYTHONPATH:-}
mkdir -p /home/hongsheng/K-Radar-main/logs_avail_eval

for mode in "$@"; do
  tag="availability_official_asf_v1_model10_${mode}_gpu${GPU}_260902"
  log="/home/hongsheng/K-Radar-main/logs_avail_eval/${tag}.log"
  printf '[%s] mode=%s gpu=%s config=%s model=%s\n' "$(date '+%F %T')" "${mode}" "${GPU}" "${CONFIG}" "${MODEL}" | tee "${log}"
  "${PY}" -u main_cond_avail_args.py \
    --gpu "${GPU}" \
    --config "${CONFIG}" \
    --model "${MODEL}" \
    --infer_mode "${mode}" \
    --conf_thr 0.0 0.3 \
    >> "${log}" 2>&1
  printf '[%s] done mode=%s\n' "$(date '+%F %T')" "${mode}" | tee -a "${log}"
done
