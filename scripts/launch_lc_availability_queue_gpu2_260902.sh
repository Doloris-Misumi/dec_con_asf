#!/usr/bin/env bash
set -u

GPU=2
PY=/home/hongsheng/miniconda3/envs/rl_3dod/bin/python
QUEUE_LOG=/home/hongsheng/dec_con_asf/logs/launcher/availability_lc_queue_gpu2_260902.log

mkdir -p /home/hongsheng/dec_con_asf/logs/launcher
mkdir -p /home/hongsheng/K-Radar-main/logs_avail_eval

echo "[$(date '+%F %T')] LC queue start on gpu ${GPU}" | tee "${QUEUE_LOG}"

cd /home/hongsheng/dec_con_asf || exit 1
export PYTHONPATH=/home/hongsheng/dec_con_asf/ops:/home/hongsheng/dec_con_asf:${PYTHONPATH:-}
TASKDEC_LOG=/home/hongsheng/dec_con_asf/logs/launcher/availability_taskdec_robust_v1_model0_lc_gpu2_260902.log
echo "[$(date '+%F %T')] mode=lc gpu=${GPU} taskdec" | tee "${TASKDEC_LOG}"
"${PY}" -u eval_model_full.py \
  --config ./logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/config.yml \
  --model ./logs/exp_260810_221258_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/models/model_0.pt \
  --gpu "${GPU}" \
  --epoch 0 \
  --confs 0.0,0.3 \
  --num-workers 0 \
  --infer-mode lc \
  >> "${TASKDEC_LOG}" 2>&1
TASKDEC_STATUS=$?
echo "[$(date '+%F %T')] taskdec_lc_exit=${TASKDEC_STATUS}" | tee -a "${QUEUE_LOG}" "${TASKDEC_LOG}"

cd /home/hongsheng/K-Radar-main || exit 1
export PYTHONPATH=/home/hongsheng/K-Radar-main/ops:/home/hongsheng/K-Radar-main:${PYTHONPATH:-}
ASF_LOG=/home/hongsheng/K-Radar-main/logs_avail_eval/availability_official_asf_v1_model10_lc_gpu2_260902.log
echo "[$(date '+%F %T')] mode=lc gpu=${GPU} official_asf" | tee "${ASF_LOG}"
"${PY}" -u main_cond_avail_args.py \
  --gpu "${GPU}" \
  --config ./configs/v1_0/cfg_A2F_scl_final_local.yml \
  --model ./pretrained/v1_0_official/A2F_v1_0_model_10.pt \
  --infer_mode lc \
  --conf_thr 0.0 0.3 \
  >> "${ASF_LOG}" 2>&1
ASF_STATUS=$?
echo "[$(date '+%F %T')] official_asf_lc_exit=${ASF_STATUS}" | tee -a "${QUEUE_LOG}" "${ASF_LOG}"

cd /home/hongsheng/dec_con_asf || exit 1
python3 scripts/collect_availability_table_260902.py >> "${QUEUE_LOG}" 2>&1
echo "[$(date '+%F %T')] LC queue finished" | tee -a "${QUEUE_LOG}"
