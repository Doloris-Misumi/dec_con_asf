#!/usr/bin/env bash
set -euo pipefail

cd /home/hongsheng/dec_con_asf

PY=/home/hongsheng/miniconda3/envs/rl_3dod/bin/python
MORE_EXP=./logs/exp_260813_225556_TaskDecControlMoreOpenGate_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16
STRONG_EXP=./logs/exp_260813_225557_TaskDecControlStrongerControl_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16

export PYTHONPATH=/home/hongsheng/dec_con_asf/ops:/home/hongsheng/dec_con_asf:${PYTHONPATH:-}

mkdir -p logs

launch_eval() {
  local tag="$1"
  local gpu="$2"
  local config="$3"
  local model="$4"
  local epoch="$5"
  local log="logs/${tag}.log"
  local pidfile="logs/${tag}.pid"

  nohup "${PY}" -u eval_model_full.py \
    --config "${config}" \
    --model "${model}" \
    --gpu "${gpu}" \
    --epoch "${epoch}" \
    --confs 0.0,0.3 \
    --num-workers 0 \
    --conditional \
    > "${log}" 2>&1 &

  local pid=$!
  printf '%s\n' "${pid}" > "${pidfile}"
  printf '%s gpu=%s epoch=%s pid=%s log=%s\n' "${tag}" "${gpu}" "${epoch}" "${pid}" "${log}"
}

launch_eval \
  full_v1_more_open_gate_model0_gpu0_260816 \
  0 \
  "${MORE_EXP}/config.yml" \
  "${MORE_EXP}/models/model_0.pt" \
  0

sleep 2

launch_eval \
  full_v1_stronger_control_model2_gpu1_260816 \
  1 \
  "${STRONG_EXP}/config.yml" \
  "${STRONG_EXP}/models/model_2.pt" \
  2

sleep 2

launch_eval \
  full_v1_stronger_control_model4_gpu2_260816 \
  2 \
  "${STRONG_EXP}/config.yml" \
  "${STRONG_EXP}/models/model_4.pt" \
  4

sleep 2

launch_eval \
  full_v1_more_open_gate_model2_gpu3_260816 \
  3 \
  "${MORE_EXP}/config.yml" \
  "${MORE_EXP}/models/model_2.pt" \
  2
