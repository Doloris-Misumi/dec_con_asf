# L4DR K-Radar v1.0 Local Evaluation

Date: 2026-09-10 02:49:33

- Tag: `l4dr_v1_1_model34_local_eval_260910`
- Repo: `/home/hongsheng/L4DR/K-Radar-main-repo`
- Config: `/home/hongsheng/L4DR/K-Radar-main-repo/configs/cfg_PP_L4DR_v1.1.yml`
- Local config: `/home/hongsheng/dec_con_asf/results/l4dr_kradar_v1_local_eval_260910/cfg_PP_L4DR_v1.1_local_eval.yml`
- Model: `/home/hongsheng/L4DR/checkpoints/L4DR-KRadar-v1.1-model_34.pt`
- Data root: `/home/hongsheng/k_radar_dataset`
- Label version: `v1_0`
- Subset: `False`
- Pipeline log dir: `/home/hongsheng/dec_con_asf/results/l4dr_kradar_v1_local_eval_260910/l4dr_logs/cfg_PP_L4DR_v1.1_local_eval/test_l4dr_v1_1_model34_local_eval_260910`

## Overall, conf=0.3

| Metric | IoU=0.7 | IoU=0.5 | IoU=0.3 |
|---|---:|---:|---:|
| APBEV | 12.27 | 32.06 | 32.98 |
| AP3D | 0.55 | 12.37 | 24.80 |

## Weather AP3D, conf=0.3

| Condition | AP3D@0.7 | AP3D@0.5 | AP3D@0.3 | APBEV@0.7 | APBEV@0.5 | APBEV@0.3 |
|---|---:|---:|---:|---:|---:|---:|
| normal | 0.49 | 11.38 | 22.66 | 10.70 | 23.18 | 23.81 |
| overcast | 1.52 | 4.94 | 19.76 | 11.73 | 21.06 | 21.34 |
| fog | 2.26 | 18.70 | 41.71 | 37.66 | 53.87 | 55.31 |
| rain | 1.52 | 14.31 | 35.72 | 19.13 | 38.43 | 39.13 |
| sleet | 0.68 | 17.31 | 30.80 | 15.54 | 29.77 | 31.22 |
| lightsnow | 0.69 | 21.65 | 32.19 | 11.25 | 31.95 | 32.26 |
| heavysnow | 0.38 | 7.85 | 26.66 | 4.70 | 18.69 | 27.78 |
| unnormal | 0.83 | 13.18 | 33.12 | 13.83 | 34.97 | 36.09 |

## Raw Files

- `/home/hongsheng/dec_con_asf/results/l4dr_kradar_v1_local_eval_260910/raw/complete_results_none_0.3.txt`

