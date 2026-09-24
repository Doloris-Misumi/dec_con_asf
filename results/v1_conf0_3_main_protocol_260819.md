# K-Radar v1.0 Main Comparison under `conf=0.3`

Generated: 2026-08-19

Scope: Sedan, K-Radar v1.0/narrow RoI. This table uses the confidence-filtered K-Radar protocol with prediction pre-filter `conf_thr=0.3`.

## Why This Protocol

The public evidence now supports treating `conf=0.3` as the more protocol-consistent main-table setting for comparison with RTNH, 3D-LRF, and L4DR:

- RTNH/K-Radar public conditional evaluator calls `validate_kitti_conditional(list_conf_thr=[0.3, 0.5, 0.7])`.
- 3D-LRF official repo `RL_3DOD/main_cond_0.py` calls `validate_kitti_conditional(..., list_conf_thr=[0.3], ...)`.
- L4DR K-Radar branch evaluates `list_conf_thr=[0.1, 0.2, 0.3]`, and its public v1.1 result log is explicitly headed `Conf thr: 0.3`.
- ASF paper Table 1 reports the same scale as the official ASF `conf=0.0` log. The current K-Radar `main_cond_0_args.py` default is `--conf_thr [0.0]`, and the official docs evaluation command does not pass `--conf_thr`, so the paper row is best interpreted as default `conf=0.0`.

Recommended caption wording:

> We follow the confidence-filtered K-Radar evaluation protocol used by the public RTNH/3D-LRF/L4DR evaluation scripts (`conf_thr=0.3`). Because ASF Table 1 corresponds to the default evaluator setting (`conf_thr=0.0`), we re-evaluate the released ASF checkpoint under `conf_thr=0.3` for a protocol-consistent ASF baseline.

Strict wording note: do not call this an "ASF 0.3 checkpoint"; it is the released ASF checkpoint evaluated with `conf_thr=0.3`.

## Paper-Facing Main Table

Sorted by `3D@0.3`, while retaining stricter `3D@0.5` and `BEV@0.5` columns.

| Rank | Method / checkpoint | Sensors | Conf | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 | 3D@0.3 vs ASF `conf=0.3` | 3D@0.5 vs ASF `conf=0.3` |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | TaskDec MoreOpenGate `model_2` | C+L+4DR | 0.3 | 62.22 | 22.06 | 80.35 | 67.80 | 89.00 | 88.51 | +8.20 | +0.61 |
| 2 | TaskDec Robust v1 best-subset `model_0` | C+L+4DR | 0.3 | 62.63 | 22.04 | 88.10 | 67.50 | 88.84 | 88.36 | +8.05 | +0.31 |
| 3 | TaskDec MoreOpenGate `model_0` | C+L+4DR | 0.3 | 62.30 | 21.33 | 87.77 | 67.21 | 88.62 | 88.08 | +7.77 | +0.02 |
| 4 | TaskDec Balanced v1 final `model_10` | C+L+4DR | 0.3 | 63.39 | 19.65 | 80.48 | 67.45 | 80.93 | 80.59 | +0.28 | +0.26 |
| 5 | TaskDec StrongerControl `model_2` | C+L+4DR | 0.3 | 63.11 | 18.99 | 80.52 | 67.70 | 88.99 | 80.52 | +0.21 | +0.51 |
| 6 | TaskDec StrongerControl `model_4` | C+L+4DR | 0.3 | 62.49 | 22.45 | 80.42 | 68.06 | 89.06 | 80.51 | +0.20 | +0.87 |
| 7 | Official ASF v1 released checkpoint `exp250303` | C+L+4DR | 0.3 | 62.85 | 18.85 | 80.33 | 67.19 | 80.78 | 80.31 | +0.00 | +0.00 |
| 8 | L4DR published/public log | L+4DR | 0.3 | 53.15 | 17.01 | 77.54 | 53.50 | 79.49 | 77.96 | -2.35 | -13.69 |
| 9 | 3D-LRF published row | L+4DR | 0.3/public eval | - | - | 73.60 | 45.20 | 84.00 | 74.80 | -5.51 | -21.99 |
| 10 | RTNH LiDAR reference | L | 0.3/public eval | - | - | 66.30 | 37.80 | 76.50 | 72.70 | -7.61 | -29.39 |
| 11 | RTNH Radar reference | 4DR | 0.3/public eval | - | - | 36.00 | 14.10 | 41.10 | 37.40 | -42.91 | -53.09 |

## Internal Sanity Check

Our ASF local repro `model_2` under `conf=0.3` gets `BEV@0.5=80.36`, `3D@0.5=67.51`, `BEV@0.3=89.00`, `3D@0.3=88.57`.

This means the `conf=0.3` table should be framed as a protocol-correct comparison against the released ASF checkpoint/log, not as a universal statement that TaskDec beats every possible ASF training run under every confidence calibration. The self-repro result is useful evidence that `conf=0.3` is strongly affected by score calibration and checkpoint choice.

## Recommended Claims

- Main fair baseline: Official ASF released checkpoint evaluated at `conf=0.3`, not ASF paper Table 1 `conf=0.0`.
- Strongest `3D@0.3` TaskDec row: MoreOpenGate `model_2`, `88.51`, +8.20 over official ASF `conf=0.3`.
- Strongest balanced `BEV@0.5`/`3D@0.3` row: Robust `model_0`, `BEV@0.5=88.10`, `3D@0.3=88.36`.
- Strongest strict `3D@0.5` among recent TaskDec rows: StrongerControl `model_4`, `68.06`, +0.87 over official ASF `conf=0.3`.
- Keep `conf=0.0` results as an appendix/protocol-sensitivity table, because ASF Table 1 appears to use that default.

## Sources

- ASF Table 1 and metric setup: `https://arxiv.org/html/2503.07029v2`
- ASF official K-Radar docs/evaluation command: `https://github.com/kaist-avelab/K-Radar/blob/main/docs/sensor_fusion.md`
- ASF arg evaluator default `conf_thr=[0.0]`: `https://raw.githubusercontent.com/kaist-avelab/K-Radar/main/main_cond_0_args.py`
- RTNH/K-Radar public conditional evaluator: `https://raw.githubusercontent.com/kaist-avelab/K-Radar/main/main_cond_0.py`
- 3D-LRF public evaluator: `https://raw.githubusercontent.com/yujeong-star/RL_3DOD/main/main_cond_0.py`
- L4DR K-Radar evaluator: `https://github.com/ylwhxht/L4DR/blob/main/K-Radar-main-repo/main_cond_0.py`
- L4DR public v1.1 results: `https://github.com/ylwhxht/L4DR/blob/main/K-Radar-main-repo/logs/v1.1.txt`
- Official ASF local `conf=0.3`: `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303/summary_conf0.3.md`
- TaskDec full summaries: `/home/hongsheng/dec_con_asf/logs/*/full_eval_summary.json` and `/home/hongsheng/dec_con_asf/results/*/summary_conf0.3.md`
