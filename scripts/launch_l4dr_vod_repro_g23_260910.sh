#!/usr/bin/env bash
set -euo pipefail

SESSION=taskdec_l4dr_vod_repro_260910
ROOT=/home/hongsheng/dec_con_asf
LOG=${ROOT}/logs/launcher/l4dr_vod_repro_g23_260910.log
OUT=${ROOT}/vod_taskdec_native/L4DR_taskdec/output/VoD_models/L4DR/l4dr_vod_repro_ep100_g23_260910

if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "Session already exists: ${SESSION}"
else
  tmux new-session -d -s "${SESSION}" "/bin/bash ${ROOT}/scripts/run_l4dr_vod_repro_g23_260910.sh"
  echo "Started L4DR VoD reproduction on GPU2,3"
fi

echo "Session: ${SESSION}"
echo "Log: ${LOG}"
echo "Output: ${OUT}"
