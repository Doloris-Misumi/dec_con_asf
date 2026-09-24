# L4DR K-Radar v1.0 Local Evaluation

Date: 2026-09-10 00:44:27

- Tag: `l4dr_v1_1_model34_smoke20b_260910`
- Repo: `/home/hongsheng/L4DR/K-Radar-main-repo`
- Config: `/home/hongsheng/L4DR/K-Radar-main-repo/configs/cfg_PP_L4DR_v1.1.yml`
- Local config: `/home/hongsheng/dec_con_asf/results/l4dr_kradar_v1_local_eval_smoke20b_260910/cfg_PP_L4DR_v1.1_local_eval.yml`
- Model: `/home/hongsheng/L4DR/checkpoints/L4DR-KRadar-v1.1-model_34.pt`
- Data root: `/home/hongsheng/k_radar_dataset`
- Label version: `v1_0`
- Subset: `True`
- Pipeline log dir: `/home/hongsheng/dec_con_asf/results/l4dr_kradar_v1_local_eval_smoke20b_260910/l4dr_logs/cfg_PP_L4DR_v1.1_local_eval/test_l4dr_v1_1_model34_smoke20b_260910`

## Overall, conf=0.3

| Metric | IoU=0.7 | IoU=0.5 | IoU=0.3 |
|---|---:|---:|---:|
| APBEV | 15.58 | 24.46 | 25.76 |
| AP3D | 0.00 | 14.55 | 22.73 |

## Weather AP3D, conf=0.3

| Condition | AP3D@0.7 | AP3D@0.5 | AP3D@0.3 | APBEV@0.7 | APBEV@0.5 | APBEV@0.3 |
|---|---:|---:|---:|---:|---:|---:|
| normal | 0.00 | 14.55 | 22.73 | 15.58 | 24.46 | 25.76 |
| overcast | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| fog | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| rain | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sleet | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lightsnow | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| heavysnow | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| unnormal | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## Raw Files

- `/home/hongsheng/dec_con_asf/results/l4dr_kradar_v1_local_eval_smoke20b_260910/raw/complete_results_none_0.3.txt`

