#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/hongsheng/dec_con_asf
OUT=${ROOT}/results/l4dr_kradar_v1_local_eval_260910
LOGDIR=${ROOT}/logs/launcher
LOG=${LOGDIR}/l4dr_kradar_v1_local_eval_gpu3_260910.log
SESSION=taskdec_l4dr_v1_eval_260910

mkdir -p "${OUT}" "${LOGDIR}"

if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "Session already exists: ${SESSION}"
else
  tmux new-session -d -s "${SESSION}" "/bin/bash ${ROOT}/scripts/run_l4dr_kradar_v1_local_eval_gpu3_260910.sh"
  echo "Started L4DR K-Radar v1.0 local eval on GPU3"
fi
echo "Session: ${SESSION}"
echo "Log: ${LOG}"
echo "Output: ${OUT}"
