#!/usr/bin/env bash
set -euo pipefail

tag="${1:?usage: run_full_eval_one_260816.sh <tag>}"

cd /home/hongsheng/dec_con_asf

PY=/home/hongsheng/miniconda3/envs/rl_3dod/bin/python
MORE_EXP=./logs/exp_260813_225556_TaskDecControlMoreOpenGate_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16
STRONG_EXP=./logs/exp_260813_225557_TaskDecControlStrongerControl_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16

case "${tag}" in
  full_v1_more_open_gate_model0_gpu0_260816)
    gpu=0
    config="${MORE_EXP}/config.yml"
    model="${MORE_EXP}/models/model_0.pt"
    epoch=0
    ;;
  full_v1_stronger_control_model2_gpu1_260816)
    gpu=1
    config="${STRONG_EXP}/config.yml"
    model="${STRONG_EXP}/models/model_2.pt"
    epoch=2
    ;;
  full_v1_stronger_control_model4_gpu2_260816)
    gpu=2
    config="${STRONG_EXP}/config.yml"
    model="${STRONG_EXP}/models/model_4.pt"
    epoch=4
    ;;
  full_v1_more_open_gate_model2_gpu3_260816)
    gpu=3
    config="${MORE_EXP}/config.yml"
    model="${MORE_EXP}/models/model_2.pt"
    epoch=2
    ;;
  *)
    printf 'Unknown tag: %s\n' "${tag}" >&2
    exit 2
    ;;
esac

mkdir -p logs
printf '%s\n' "$$" > "logs/${tag}.pid"
export PYTHONPATH=/home/hongsheng/dec_con_asf/ops:/home/hongsheng/dec_con_asf:${PYTHONPATH:-}

exec "${PY}" -u eval_model_full.py \
  --config "${config}" \
  --model "${model}" \
  --gpu "${gpu}" \
  --epoch "${epoch}" \
  --confs 0.0,0.3 \
  --num-workers 0 \
  --conditional \
  > "logs/${tag}.log" 2>&1

