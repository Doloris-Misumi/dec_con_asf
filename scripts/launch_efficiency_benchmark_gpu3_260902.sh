#!/usr/bin/env bash
set -u

GPU=3
PY=/home/hongsheng/miniconda3/envs/rl_3dod/bin/python
ROOT=/home/hongsheng/dec_con_asf
LOG=${ROOT}/logs/launcher/efficiency_benchmark_gpu3_260902.log

mkdir -p "${ROOT}/logs/launcher" "${ROOT}/results/efficiency_260902"

echo "[$(date '+%F %T')] efficiency benchmark start on gpu ${GPU}" | tee "${LOG}"

"${PY}" -u "${ROOT}/benchmark_inference_speed.py" \
  --repo-root /home/hongsheng/K-Radar-main \
  --config ./configs/v1_0/cfg_A2F_scl_final_local.yml \
  --model ./pretrained/v1_0_official/A2F_v1_0_model_10.pt \
  --gpu "${GPU}" \
  --tag official_asf_v1_model10_rlc \
  --infer-mode rlc \
  --warmup 20 \
  --iters 100 \
  --num-workers 0 \
  >> "${LOG}" 2>&1
ASF_STATUS=$?
echo "[$(date '+%F %T')] official_asf_eff_exit=${ASF_STATUS}" | tee -a "${LOG}"

"${PY}" -u "${ROOT}/benchmark_inference_speed.py" \
  --repo-root /home/hongsheng/dec_con_asf \
  --config ./logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml \
  --model ./logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/models/model_0.pt \
  --gpu "${GPU}" \
  --tag taskdec_robust_v1_model0_rlc \
  --infer-mode rlc \
  --warmup 20 \
  --iters 100 \
  --num-workers 0 \
  >> "${LOG}" 2>&1
TASKDEC_STATUS=$?
echo "[$(date '+%F %T')] taskdec_eff_exit=${TASKDEC_STATUS}" | tee -a "${LOG}"

python3 "${ROOT}/scripts/collect_efficiency_table_260902.py" >> "${LOG}" 2>&1
echo "[$(date '+%F %T')] efficiency benchmark finished" | tee -a "${LOG}"
