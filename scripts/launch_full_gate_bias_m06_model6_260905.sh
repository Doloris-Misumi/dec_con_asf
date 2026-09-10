#!/usr/bin/env bash
set -euo pipefail

cd /home/hongsheng/dec_con_asf

PY=/home/hongsheng/miniconda3/envs/rl_3dod/bin/python
EXP=./logs/exp_260904_075622_TaskDecGateBiasM06_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16
TAG=full_gate_bias_m06_v1_model6_gpu2_260905

mkdir -p logs/launcher
printf '%s\n' "$$" > "logs/launcher/${TAG}.runner.pid"

export PYTHONPATH=/home/hongsheng/dec_con_asf/ops:/home/hongsheng/dec_con_asf:${PYTHONPATH:-}

exec "${PY}" -u eval_model_full.py \
  --config "${EXP}/config.yml" \
  --model "${EXP}/models/model_6.pt" \
  --gpu 2 \
  --epoch 6 \
  --confs 0.0,0.3 \
  --num-workers 0 \
  --conditional
