# V1.0 Stable/KV-only/ASF Repro Analysis

Generated: 2026-08-19

Scope: Sedan, K-Radar v1.0/narrow RoI. Current paper-facing external protocol is `conf_thr=0.3`; `conf=0.0` is kept as ASF Table-1/default-evaluator sensitivity.

## Newly Exported Full Results

| Method / checkpoint | Conf | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 | Note |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Official ASF v1 released `exp250303` | 0.3 | 62.85 | 18.85 | 80.33 | 67.19 | 80.78 | 80.31 | Protocol baseline |
| ASF local repro `model_2` | 0.3 | 61.59 | 18.69 | 80.36 | 67.49 | 89.01 | 88.57 | Repro is very strong at `3D@0.3` |
| TaskDec MoreOpenGate `model_2` | 0.3 | 62.22 | 22.06 | 80.35 | 67.80 | 89.00 | 88.51 | Strong TaskDec `3D@0.3` row |
| TaskDec StrongerControl `model_4` | 0.3 | 62.49 | 22.45 | 80.42 | 68.06 | 89.06 | 80.51 | Best recent TaskDec `3D@0.5` row |
| TaskDec Stable final `model_10` | 0.3 | 56.85 | 4.44 | 83.61 | 40.82 | 86.74 | 81.26 | Final epoch collapsed in 3D localization |
| TaskDec KVOnlyStable final `model_10` | 0.3 | 29.46 | 3.24 | 72.38 | 35.44 | 84.55 | 78.27 | Much weaker; not a main candidate |

`conf=0.0` sanity:

| Method / checkpoint | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 |
|---|---:|---:|---:|---:|---:|---:|
| Official ASF v1 released `exp250303` | 62.85 | 18.85 | 86.97 | 72.95 | 88.59 | 87.34 |
| ASF local repro `model_2` | 61.57 | 18.68 | 87.41 | 72.96 | 88.80 | 87.96 |
| TaskDec Stable final `model_10` | 56.85 | 3.88 | 83.61 | 40.82 | 86.74 | 80.60 |
| TaskDec KVOnlyStable final `model_10` | 29.46 | 3.24 | 72.38 | 35.17 | 84.55 | 78.27 |

## Interpretation

1. Stable and KV-only final checkpoints are not useful main-table results. Stable final keeps moderate `BEV@0.5` but its `3D@0.5=40.82` and `3D@0.7=4.44` show severe 3D localization degradation. KV-only final is worse across nearly all strict metrics.
2. The ASF local repro `model_2` is a strong baseline/checkpoint: at `conf=0.3`, it reaches `3D@0.3=88.57`, slightly above MoreOpenGate `model_2` (`88.51`). This confirms that `conf=0.3` strongly reflects score calibration and checkpoint choice.
3. MoreOpenGate `model_2` remains a good TaskDec representative because it combines high `3D@0.3=88.51` with better strict 3D than ASF repro (`3D@0.5=67.80` vs `67.49`, `3D@0.7=22.06` vs `18.69`).
4. StrongerControl `model_4` is the better strict-IoU representative: `3D@0.5=68.06`, `3D@0.7=22.45`, but its `3D@0.3` falls to `80.51`, so it is not the best headline row for `3D@0.3`.
5. Stable/KV-only reinforce the earlier training-dynamics concern: longer training can sharply hurt `3D@0.5`, `3D@0.7`, and sometimes `BEV@0.5`, even when `BEV@0.3` remains superficially high.

## 1000-Sample Checkpoint Selection

Top existing subset results, sorted mainly by `conf=0.3 3D@0.3`, with `3D@0.5/BEV@0.5` used as tie-breakers:

| Run | Top epoch | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 | Recommendation |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| ASF local repro subset | 2 | 62.18 | 19.39 | 88.64 | 68.11 | 89.30 | 88.81 | Already full-tested; no urgent extra full eval |
| TaskDec Balanced subset | 2 | 62.89 | 22.11 | 80.64 | 68.25 | 89.28 | 88.79 | Already full-tested earlier |
| TaskDec MoreOpenGate subset | 10 | 61.58 | 19.05 | 80.41 | 68.14 | 89.26 | 88.75 | Later run only had epoch 9/10 subset; full candidates remain m2/m10 if needed |
| TaskDec Stable subset | 0 | 62.69 | 17.95 | 88.48 | 74.67 | 89.22 | 88.69 | Best new candidate for full eval after missing 9/10 subset finishes |
| TaskDec Stable subset | 2 | 61.92 | 22.08 | 80.62 | 67.70 | 89.22 | 88.67 | Strong but less balanced than epoch 0 |
| TaskDec StrongerControl subset | 2 | 62.46 | 22.30 | 80.54 | 68.35 | 89.18 | 88.67 | Already full-tested selected variants |
| TaskDec Robust subset | 0 | 62.29 | 19.25 | 88.39 | 74.46 | 89.20 | 88.50 | Already full-tested; important reproducibility row |

`conf=0.0` subset view gives a similar early-epoch preference:

| Run | Top epoch | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 |
|---|---:|---:|---:|---:|---:|
| ASF local repro subset | 2 | 88.02 | 73.61 | 89.30 | 88.45 |
| TaskDec Stable subset | 0 | 87.61 | 73.32 | 89.22 | 88.45 |
| TaskDec Robust subset | 0 | 88.05 | 72.99 | 89.20 | 88.44 |
| TaskDec Balanced subset | 2 | 88.07 | 73.95 | 89.20 | 88.40 |

## Missing Subset Evaluations Started

Started on 2026-08-19:

| Task | GPU | Session | Launcher log | Checkpoints |
|---|---:|---|---|---|
| Stable missing subset | 2 | `subset_stable_9_10_gpu2_260819_v2` | `logs/launcher/subset_stable_epochs9_10_gpu2_260819_tmux_v2.log` | `model_9.pt`, `model_10.pt` |
| KV-only subset sweep | 3 | `subset_kv_only_0_10_gpu3_260819_v2` | `logs/launcher/subset_kv_only_epochs0_10_gpu3_260819_tmux_v2.log` | `model_0.pt` to `model_10.pt` |

The first launch failed because `PYTHONPATH` did not include the compiled `ops` directory. The running tmux launches explicitly export:

`PYTHONPATH=/home/hongsheng/dec_con_asf/ops:/home/hongsheng/dec_con_asf:${PYTHONPATH:-}`

## Next Full-Eval Priority

1. Wait for the two running subset jobs to finish.
2. If Stable epoch 9/10 do not unexpectedly beat epoch 0, full-test Stable `model_0.pt` first. It is the strongest new candidate because subset `conf=0.3` has `3D@0.3=88.69`, `3D@0.5=74.67`, and `BEV@0.5=88.48`.
3. Consider Stable `model_4.pt` only as a secondary full eval: it has good `BEV@0.5=88.04` and `3D@0.7=22.56`, but weaker `3D@0.5=67.56`.
4. For KV-only, do not full-test anything until the subset sweep proves there is an early checkpoint much better than final.

## 2026-08-20 Completed Follow-up

All follow-up jobs have finished. `tmux ls` reports no active server. `nvidia-smi` still shows two GPU0/GPU1 Python processes, but they are unrelated root `scripts/serve_b1k.py` services, not this K-Radar/TaskDec project.

### Newly Completed Full Evaluations

`conf=0.3`, sedan, K-Radar v1.0/narrow RoI:

| Method / checkpoint | Sensors | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 | Note |
|---|---|---:|---:|---:|---:|---:|---:|---|
| TaskDec Stable `model_0` | C+L+4DR | 62.77 | 21.58 | 80.30 | 67.24 | 88.98 | 88.54 | Full eval did not preserve subset `BEV@0.5=88.48` |
| TaskDec Balanced v1 `model_0` | C+L+4DR | 61.89 | 18.73 | 80.02 | 66.99 | 88.63 | 88.18 | Also drops from its strong subset row |
| TaskDec Robust v1 `model_0`, eval `L+4DR` | L+4DR | 62.30 | 18.22 | 80.09 | 66.87 | 88.87 | 88.37 | First-stage overall result; conditional `all` has a 3D@0.3 mismatch, see below |

`conf=0.0` sanity:

| Method / checkpoint | Sensors | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 |
|---|---|---:|---:|---:|---:|---:|---:|
| TaskDec Stable `model_0` | C+L+4DR | 62.77 | 21.58 | 87.08 | 72.73 | 88.86 | 88.02 |
| TaskDec Balanced v1 `model_0` | C+L+4DR | 61.89 | 18.73 | 86.87 | 71.96 | 88.52 | 87.75 |
| TaskDec Robust v1 `model_0`, eval `L+4DR` | L+4DR | 62.30 | 18.22 | 86.97 | 72.82 | 88.73 | 87.86 |

### Newly Completed Subset Evaluations

`conf=0.3`, 1000-sample subset:

| Run | Best / checked epoch | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 | Takeaway |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Stable missing subset | 9 | 49.14 | 8.21 | 83.44 | 56.82 | 87.34 | 84.86 | Late epochs are much weaker |
| Stable missing subset | 10 | 58.05 | 4.38 | 85.39 | 42.47 | 87.51 | 84.31 | Confirms late localization collapse |
| KVOnlyStable sweep | 0 | 61.59 | 17.31 | 88.46 | 67.18 | 89.07 | 88.56 | Best KV-only subset checkpoint |
| KVOnlyStable sweep | 1 | 52.61 | 19.25 | 87.86 | 64.29 | 89.05 | 88.00 | Secondary early checkpoint |
| KVOnlyStable sweep | 4 | 61.85 | 21.62 | 87.26 | 67.32 | 88.59 | 87.79 | Best strict 3D@0.7/3D@0.5 tradeoff among KV-only |
| KVOnlyStable sweep | 10 | 29.10 | 4.64 | 71.16 | 37.01 | 85.12 | 79.60 | Final epoch collapses badly |

### Updated Interpretation

1. The paper-facing main candidates remain Robust v1 `model_0` C+L+4DR and MoreOpenGate `model_0`/`model_2`, not Stable/Balanced `model_0`.
2. Stable and Balanced had very attractive 1000-sample early checkpoints, but full validation brings `conf=0.3 BEV@0.5` back to the 80-ish band. They are useful evidence for checkpoint/score-calibration instability, not strong final rows.
3. KVOnlyStable is a useful ablation direction because epoch 0 is strong on the subset, but its late-epoch degradation is severe. It needs full eval only if we want a dedicated "remove value/stronger control component" ablation, not as a headline method.
4. Robust v1 `model_0` evaluated without camera reaches ASF-like `L+4DR` scale: `BEV@0.5=80.09`, `3D@0.5=66.87`. It does not retain the C+L+4DR `BEV@0.5=88.10` advantage, so it should be framed as a camera-removal availability stress test.
5. There is an internal mismatch for Robust v1 `model_0` L+4DR: first-stage overall reports `3D@0.3=88.37`, while conditional `all` reports `3D@0.3=80.30`. Stable/Balanced first-stage and conditional `all` agree, so do not use the Robust L+4DR `3D@0.3` as a headline number until this mismatch is diagnosed or rerun.
