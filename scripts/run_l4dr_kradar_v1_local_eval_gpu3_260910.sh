#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/hongsheng/dec_con_asf
PY=/home/hongsheng/miniconda3/envs/rl_3dod/bin/python
OUT=${ROOT}/results/l4dr_kradar_v1_local_eval_260910
LOGDIR=${ROOT}/logs/launcher
LOG=${LOGDIR}/l4dr_kradar_v1_local_eval_gpu3_260910.log
STATUS=${LOGDIR}/l4dr_kradar_v1_local_eval_gpu3_260910.status

mkdir -p "${OUT}" "${LOGDIR}"

{
  echo "Started at $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Output: ${OUT}"
  echo "GPU: 3"
  echo

  set +e
  "${PY}" -u "${ROOT}/tools/analysis/eval_l4dr_kradar_v1_conditional.py" \
    --gpu 3 \
    --num-workers 0 \
    --tag l4dr_v1_1_model34_local_eval_260910 \
    --out-dir "${OUT}" \
    --conf-thr 0.3
  rc=$?
  set -e

  echo
  echo "Finished at $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Exit code: ${rc}"
  echo "${rc}" > "${STATUS}"
  exit "${rc}"
} > "${LOG}" 2>&1
