# ASF v1.0 Confidence-Threshold Protocol Audit

Date: 2026-08-28

Scope: K-Radar v1.0, Sedan class, narrow RoI, C+L+4DR ASF / TaskDec comparison.

## Local Sources

- Official v1.0 ASF checkpoint: `/home/hongsheng/K-Radar-main/pretrained/v1_0_official/A2F_v1_0_model_10.pt`
  - SHA256: `3e6d3e44118c17f7aa663c1338927ed597fb9a5bc6022a6755ab55c6d5809753`
- Official ASF log bundle, minimal extracted logs:
  - `/home/hongsheng/K-Radar-main/official_downloads/asf_v1_official_logs_min/exp_250219_134333_A2F_v1_0`
  - `/home/hongsheng/K-Radar-main/official_downloads/asf_v1_official_logs_min/exp_250303_200024_A2F_v1_0`
- Parsed local summaries:
  - `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250219/summary_conf0.0.json`
  - `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303/summary_conf0.0.json`
  - `/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303/summary_conf0.3.json`
  - `/home/hongsheng/dec_con_asf/results/exp_260812_232650_TaskDecControlRobust_v1_model0_full/summary_conf0.3.json`

The `exp250303` official executed code loads the model from `exp_250219_134333_A2F_v1_0/models/model_10.pt` and runs:

```python
pline.validate_kitti_conditional(list_conf_thr=[0.0, 0.3], is_subset=False, is_print_memory=False)
```

The parsed configs for `exp250219` and `exp250303` are identical:

```text
67a67f7df64d20dd2efc4f035563bc93829a078efdefbc09b24e886c2c06a425  exp250303/config.yml
67a67f7df64d20dd2efc4f035563bc93829a078efdefbc09b24e886c2c06a425  exp250219/config.yml
```

## All-Condition Results

Metric order below is `BEV@0.7 / BEV@0.5 / BEV@0.3 / 3D@0.7 / 3D@0.5 / 3D@0.3`.

| Run | conf_thr | BEV@0.7 | BEV@0.5 | BEV@0.3 | 3D@0.7 | 3D@0.5 | 3D@0.3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Official ASF `exp250219` | 0.0 | 63.98 | 87.17 | 88.59 | 19.96 | 73.58 | 87.42 |
| Official ASF `exp250303` | 0.0 | 62.85 | 86.97 | 88.59 | 18.85 | 72.95 | 87.34 |
| Official ASF `exp250303` | 0.3 | 62.85 | 80.33 | 80.78 | 18.85 | 67.19 | 80.31 |
| TaskDec Robust `model_0` | 0.3 | 62.63 | 88.10 | 88.84 | 22.04 | 67.50 | 88.36 |
| TaskDec Robust `model_0` | 0.0 | 62.63 | 87.18 | 88.84 | 22.02 | 72.83 | 88.06 |
| ASF local repro `model_2` | 0.3 | 61.59 | 80.36 | 89.01 | 18.69 | 67.49 | 88.57 |

## Main Evidence

The public K-Radar README reports ASF v1.0 as `87.4% AP3D at IoU=0.3` and `73.6% AP3D at IoU=0.5`, without stating `conf_thr`. These numbers align with the official `exp250219` `conf_thr=0.0` log:

- `AP3D@0.3`: 87.42 -> 87.4
- `AP3D@0.5`: 73.58 -> 73.6

The official sensor-fusion guide reports the v1.0 table at IoU=0.3 only. Its `3D=87.4` and `BEV=88.6` also align with `conf_thr=0.0`, not with the same official checkpoint evaluated at `conf_thr=0.3`.

For a protocol-consistent comparison to methods whose public code/logs use `conf_thr=0.3`, the ASF released checkpoint should be compared using the official `exp250303` `conf_thr=0.3` log.

## Deltas Under Unified `conf_thr=0.3`

TaskDec Robust `model_0` minus official ASF `exp250303`, both evaluated at `conf_thr=0.3`:

| Metric | Delta |
|---|---:|
| BEV@0.7 | -0.22 |
| BEV@0.5 | +7.77 |
| BEV@0.3 | +8.06 |
| 3D@0.7 | +3.19 |
| 3D@0.5 | +0.31 |
| 3D@0.3 | +8.04 |

## Recommended Paper Framing

Use neutral wording. The local evidence supports a confidence-threshold protocol inconsistency / missing threshold disclosure. It does not by itself prove intent.

Suggested main-table wording:

> We re-evaluate the released ASF v1.0 checkpoint under the same `conf_thr=0.3` protocol used by prior K-Radar evaluation code/logs. Under this unified protocol, TaskDec Robust `model_0` improves AP3D@IoU=0.3 from 80.31 to 88.36 and slightly improves AP3D@IoU=0.5 from 67.19 to 67.50.

Suggested appendix note:

> The official ASF README/table values align with the released `conf_thr=0.0` logs. We therefore report official ASF numbers separately as a reproduced/protocol-sensitivity row and avoid mixing them directly with `conf_thr=0.3` baselines.

Avoid claiming that TaskDec Robust beats the official ASF reported `AP3D@IoU=0.5=73.6`; at `conf_thr=0.0`, TaskDec Robust has stronger AP3D@0.3 but lower AP3D@0.5 than the official reported/logged value.
