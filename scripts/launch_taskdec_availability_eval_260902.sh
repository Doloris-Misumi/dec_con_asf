#!/usr/bin/env bash
set -euo pipefail

cd /home/hongsheng/dec_con_asf

PY=/home/hongsheng/miniconda3/envs/rl_3dod/bin/python
EXP=./logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16
CONFIG="${EXP}/config.yml"
MODEL="${EXP}/models/model_0.pt"
GPU="${1:?usage: launch_taskdec_availability_eval_260902.sh <gpu> <mode> [mode...]}"
shift

export PYTHONPATH=/home/hongsheng/dec_con_asf/ops:/home/hongsheng/dec_con_asf:${PYTHONPATH:-}
mkdir -p logs/launcher

for mode in "$@"; do
  tag="availability_taskdec_robust_v1_model0_${mode}_gpu${GPU}_260902"
  log="logs/launcher/${tag}.log"
  printf '[%s] mode=%s gpu=%s config=%s model=%s\n' "$(date '+%F %T')" "${mode}" "${GPU}" "${CONFIG}" "${MODEL}" | tee "${log}"
  "${PY}" -u eval_model_full.py \
    --config "${CONFIG}" \
    --model "${MODEL}" \
    --gpu "${GPU}" \
    --epoch 0 \
    --confs 0.0,0.3 \
    --num-workers 0 \
    --infer-mode "${mode}" \
    >> "${log}" 2>&1
  printf '[%s] done mode=%s\n' "$(date '+%F %T')" "${mode}" | tee -a "${log}"
done
