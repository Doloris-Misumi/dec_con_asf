# K-Radar v1.0 `conf_thr=0.3` SOTA Comparison

Date: 2026-08-28

Scope: K-Radar v1.0, narrow RoI, Sedan class. Metrics are AP in percent. `R` denotes 4D radar.

## Main Table: AP3D@IoU=0.3

This is the cleanest table for the main SOTA claim. Rows marked `confirmed` have direct code/log or local re-evaluation evidence for `conf_thr=0.3`. Rows marked `compatible` are reported under the same K-Radar v1.0 Sedan benchmark or the same 3D-LRF/L4DR protocol family, but the paper text does not explicitly expose the prediction confidence threshold.

| Rank | Method | Sensors | Protocol status | APBEV@0.3 | AP3D@0.3 | APBEV@0.5 | AP3D@0.5 | Source |
|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | TaskDec Robust `model_0` | C+L+R | confirmed, local full eval | 88.84 | 88.36 | 88.10 | 67.50 | local |
| 2 | AW-MoE-LRC | C+L+R | compatible; paper does not state `conf_thr` | - | 84.30 | - | 61.80 | AW-MoE Table III |
| 3 | AW-MoE | L+R | compatible; paper does not state `conf_thr` | 88.20 | 83.90 | 84.20 | 61.50 | AW-MoE Table II |
| 4 | Official ASF released ckpt `exp250303` re-eval | C+L+R | confirmed, local official log | 80.78 | 80.31 | 80.33 | 67.19 | local official log |
| 5 | L4DR-DA3D | L+R | compatible; paper does not state `conf_thr` | 80.40 | 79.30 | 78.50 | 61.90 | AW-MoE Table II |
| 6 | L4DR | L+R | confirmed by public v1.1 log | 79.49 | 77.96 | 77.54 | 53.50 | L4DR public log |
| 7 | WCBR | L+R | compatible; follows 3D-LRF protocol | 81.20 | 76.80 | 71.50 | 43.50 | WCBR Table 1 |
| 8 | 3D-LRF | L+R | confirmed by public eval script; values from published row | 84.00 | 74.80 | 73.60 | 45.20 | AW-MoE / published row |
| 9 | RTNH, LiDAR input | L | confirmed by K-Radar public eval script | 76.50 | 72.70 | 66.30 | 37.80 | AW-MoE Table II |
| 10 | InterFusion | L+R | compatible; reproduced in AW-MoE | 69.50 | 65.60 | 66.10 | 41.70 | AW-MoE Table II |
| 11 | WRCFormer | C+R | different modality family; appendix only | - | 58.70 | - | - | WRCFormer Table II |
| 12 | PointPillars | L | compatible; WCBR reproduced row | 51.90 | 47.30 | 49.10 | 22.40 | WCBR Table 1 |
| 13 | RTNH, radar input | R | confirmed by K-Radar public eval script | 41.10 | 37.40 | 36.00 | 14.10 | AW-MoE Table II |

## Direct SOTA Readout

- Against the strongest compatible recent competitor, AW-MoE-LRC, TaskDec Robust `model_0` is higher on AP3D@0.3 by `+4.06` points (`88.36 - 84.30`).
- Against the confirmed `conf_thr=0.3` ASF released-checkpoint baseline, TaskDec Robust `model_0` is higher on AP3D@0.3 by `+8.04` points (`88.36 - 80.31`) and AP3D@0.5 by `+0.31` points (`67.50 - 67.19`).
- Against confirmed/public-log L4DR, TaskDec Robust `model_0` is higher on AP3D@0.3 by `+10.40` points (`88.36 - 77.96`) and AP3D@0.5 by `+14.00` points (`67.50 - 53.50`).

Recommended claim:

> Under the confidence-filtered K-Radar v1.0 Sedan protocol (`conf_thr=0.3`), TaskDec Robust `model_0` achieves a new state of the art in AP3D@IoU=0.3. It also gives the strongest AP3D@IoU=0.5 among the compared `conf_thr=0.3` / protocol-compatible K-Radar v1.0 rows.

## Weather Breakdown: AP3D@IoU=0.3

| Method | Sensors | Protocol status | Total | Normal | Overcast | Fog | Rain | Sleet | LightSnow | HeavySnow |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| TaskDec Robust `model_0` | C+L+R | confirmed | 88.36 | 87.66 | 90.39 | 90.57 | 88.90 | 80.42 | 89.28 | 71.41 |
| Official ASF released ckpt `exp250303` re-eval | C+L+R | confirmed | 80.31 | 79.57 | 89.89 | 90.67 | 80.97 | 80.20 | 80.89 | 71.71 |
| AW-MoE-LRC | C+L+R | compatible | 84.30 | 84.70 | 91.00 | 95.30 | 84.00 | 72.90 | 89.60 | 63.70 |
| AW-MoE | L+R | compatible | 83.90 | 84.20 | 90.00 | 95.30 | 84.40 | 72.90 | 90.20 | 64.00 |
| L4DR-DA3D | L+R | compatible | 79.30 | 85.90 | 88.40 | 89.20 | 79.70 | 65.80 | 89.00 | 60.20 |
| L4DR | L+R | confirmed public log | 77.96 | 77.73 | 80.04 | 88.56 | 79.16 | 60.11 | 78.91 | 51.91 |
| 3D-LRF | L+R | confirmed script / published row | 74.80 | 81.20 | 87.20 | 86.10 | 73.80 | 49.50 | 87.90 | 67.20 |

## Strict IoU=0.5 Check

The strict localization ranking is also favorable under this protocol family, but the margin over ASF released ckpt is small and should be phrased carefully.

| Rank | Method | Sensors | Protocol status | AP3D@0.5 | APBEV@0.5 |
|---:|---|---|---|---:|---:|
| 1 | TaskDec Robust `model_0` | C+L+R | confirmed | 67.50 | 88.10 |
| 2 | Official ASF released ckpt `exp250303` re-eval | C+L+R | confirmed | 67.19 | 80.33 |
| 3 | L4DR-DA3D | L+R | compatible | 61.90 | 78.50 |
| 4 | AW-MoE-LRC | C+L+R | compatible | 61.80 | - |
| 5 | AW-MoE | L+R | compatible | 61.50 | 84.20 |
| 6 | RAF on L4DR | C+L+R | no `conf_thr` stated; IoU=0.5 only | 57.40 | 82.00 |
| 7 | L4DR | L+R | confirmed public log | 53.50 | 77.54 |
| 8 | 3D-LRF | L+R | confirmed script / published row | 45.20 | 73.60 |
| 9 | WCBR | L+R | compatible; follows 3D-LRF protocol | 43.50 | 71.50 |

## Protocol Notes

- ASF official paper/README values should not be placed in this `conf_thr=0.3` main table. They align with the official `conf_thr=0.0` logs and belong in an appendix/protocol-sensitivity table.
- For the main text, use the local official ASF released checkpoint re-evaluated at `conf_thr=0.3`: `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303/summary_conf0.3.md`.
- For our row, use TaskDec Robust `model_0`: `/home/hongsheng/dec_con_asf/results/exp_260812_232650_TaskDecControlRobust_v1_model0_full/summary_conf0.3.md`.
- AW-MoE, AW-MoE-LRC, L4DR-DA3D, WCBR, RAF, and WRCFormer are useful recent-method context. Only AW-MoE/AW-MoE-LRC are close to the v1.0 AP3D@0.3 SOTA claim, and both remain below TaskDec Robust `model_0`.

## Source URLs

- K-Radar public evaluator confirms `list_conf_thr=[0.3, 0.5, 0.7]`: `https://raw.githubusercontent.com/kaist-avelab/K-Radar/main/main_cond_0.py`
- 3D-LRF public evaluator confirms `list_conf_thr=[0.3]`: `https://raw.githubusercontent.com/yujeong-star/RL_3DOD/main/main_cond_0.py`
- L4DR public v1.1 log is headed `Conf thr: 0.3`: `https://raw.githubusercontent.com/ylwhxht/L4DR/main/K-Radar-main-repo/logs/v1.1.txt`
- L4DR K-Radar evaluator includes `list_conf_thr=[0.1,0.2,0.3]`: `https://github.com/ylwhxht/L4DR/blob/main/K-Radar-main-repo/main_cond_0.py`
- AW-MoE arXiv, Tables II-III: `https://arxiv.org/pdf/2603.16261`
- WCBR arXiv, Table 1: `https://arxiv.org/pdf/2604.05405`
- WRCFormer arXiv, Tables I-II: `https://arxiv.org/pdf/2512.22972`
- RAF arXiv, Table 1: `https://arxiv.org/pdf/2607.04587`
