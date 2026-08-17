# 方法发展脉络：从 DeCU/WCBR 到 Task-Dec-Controlled ASF

生成时间：2026-08-14。本文基于本地相关目录整理：`K-Radar-main`、`DeCU_v1_compare`、`DeCU`、`v2`、`decu_asf`、`asf_patch_dec`、`dec_con_asf`。

## 1. 总体判断

这条线不是“直接把 DECALIGN 插到 ASF 上”这么简单，而是经历了三次关键转向：

1. 从全局 weather / condition routing 转向 common-unique 解耦。
2. 从全局分支权重转向 ASF 的 canonical patch 空间。
3. 从“解耦作为辅助正则/残差”转向“解耦作为任务感知控制器”，直接调制 patch-level fusion。

现在最清楚、也最适合写成方法主线的表述是：

> 基于 ASF 的统一 canonical patch 空间，引入任务感知的跨模态解耦控制器，将各模态 patch 表征分解为共享目标信息和模态特有信息，并利用该解耦表征预测前景门控、传感器可靠性权重和类别上下文，从而动态调制 ASF 的 patch-level sensor fusion。

## 2. 目录角色

| 目录 | 角色 | 关键文件/结果 |
|---|---|---|
| `K-Radar-main` | ASF / K-Radar 基线与官方风格复现代码 | `models/fuser/a2_fusion.py`，`configs/v1_0/cfg_A2F_scl_final.yml`，`configs/ASF_v2_0_final*.yml`，`results/official_asf_*` |
| `DeCU_v1_compare` | 早期 Weather_Conditioned_Branch_Routing 形态 | `Weather_Conditioned_Branch_Routing/README.md`，`configs/cfg_rl_3df_gate.yml`，`models/condition/decoupled_condition.py` |
| `DeCU` | WCBR 重命名和系统化后的 DeCU 工程 | `PROJECT.md`，`architecture_overview.md`，`training_summary_vs_baseline.json`，`models/backbone_3d/rl_3df.py` |
| `v2` | DeCU/WCBR 的 v2 实验分支，并开始尝试 CASAP/ASF 化 | `docs/current_config.md`，`models/fuser/decu_asf_fusion.py`，`results/exp_260714_024354_casap_new.md` |
| `decu_asf` | 直接把 DeCU router 接到 frozen ASF encoder 的桥接实验 | `models/fuser/decu_router.py`，`models/fuser/decu_a2fusion.py`，`configs/cfg_decu_asf_rlc_official.yml` |
| `asf_patch_dec` | 第一代 ASF patch-level decoupling | `models/fuser/patch_dec_a2_fusion.py`，`results/comparison_obj_patchdec_20260803.md`，`results/patch_dec_epoch8_epoch10_analysis.md` |
| `dec_con_asf` | 当前主线：Task-aware decoupled controller for ASF | `models/fuser/patch_dec_a2_fusion.py`，`results/v1_task_dec_published_comparison_260812.md`，`PROJECT_PIPELINE_STATUS.md` |

## 3. 起点：ASF baseline

`K-Radar-main` 中的 ASF 路线是整个项目的强基线：

1. Camera、LiDAR、Radar 三个 encoder 生成 BEV feature。
2. 在当前 ASF/TaskDec 配置里 encoder 通常冻结，主要训练 fuser 和 detection head。
3. 各模态 feature 被投影到共同维度，再切成固定大小 patch。
4. UCP / canonical patch projection 把不同模态放到统一 patch token 空间。
5. `aware_query` 对三路 patch token 做 multi-head attention。
6. PFT 还原 fused BEV feature，接 `AnchorHeadSingleIntegrated`。
7. SCL 对单模态和双模态组合提供辅助 detection loss。

ASF 的优势是很明确的：它不是只做全局传感器权重，而是在 patch/token 层做可用性感知融合；这也给后续解耦控制提供了一个天然落点。

## 4. 第一阶段：Weather-Conditioned Branch Routing

最早的想法在 `DeCU_v1_compare/Weather_Conditioned_Branch_Routing` 里：

1. 项目还叫 Weather_Conditioned_Branch_Routing。
2. 依托 RL_3DOD / K-Radar 检测框架。
3. 先训练 image-based weather classifier。
4. 再用 weather / image condition token 去控制 LiDAR-Radar 分支融合。
5. `cfg_rl_3df_gate.yml` 里可以看到 weather auxiliary、condition model、branch preference 等模块。

这个阶段的核心假设是：恶劣天气下不同传感器可靠性变化明显，因此可以让天气条件 token 控制分支选择。

后来 `DeCU/PROJECT.md` 明确把这个方向重命名为 DeCU：Decoupled Common-Unique Representations for Weather-Adaptive Multi-Modal 3D Object Detection。也就是说，项目从“天气条件路由”升级成“跨模态 common/unique 解耦”。

## 5. 第二阶段：DeCU 的系统化

`DeCU` 目录里的设计比早期 WCBR 更完整：

1. `DecoupledConditionEncoder` 使用共享 common encoder 和每模态 unique encoder。
2. 输入包括 image token、radar token、lidar token、weather prompt token。
3. 输出 `condition_common_token` 和 `condition_unique_img/radar/lidar`。
4. 训练时加入 common 对齐、unique 分离、common/unique 解耦，以及 DecAlign 风格的 OT / prototype alignment。
5. `RL3DFBackbone_Branching` 和 `TokenGuidedBEVFusion` 用 condition token 控制分支、区域或 BEV 融合。

这个阶段已经包含了现在方法的思想源头：共享目标信息和模态特有信息要分开建模。

但实验暴露了一个很重要的问题：全局或半全局 branch routing 很容易塌缩。`training_summary_vs_baseline.json` 里记录了 mini split 上的典型失败：没有 CLIP 的 v1 路线出现 LiDAR collapse，branch entropy 到 0，LiDAR 权重到 1，Radar/Camera 权重到 0。`v2/docs/current_config.md` 里也能看到类似历史：原始 v2 会向单一模态塌缩，过强正则又会变成过度均匀。

这个阶段给出的经验是：仅靠全局条件 token 学传感器选择不够稳，尤其在 K-Radar 这种强检测基线面前，很容易变成不可靠的粗粒度路由。

## 6. 第三阶段：DeCU-ASF 桥接

接下来尝试把 DeCU 放进 ASF 体系里，主要有两条分支。

第一条在 `v2`：

1. `models/fuser/decu_asf_fusion.py` 把 DeCU condition token 用来调制 CASAP/ASF-like attention query。
2. `results/exp_260713_193610_casap_old.md` 记录了旧 CASAP 版本，UCP 里 LayerNorm/Tanh 让 branch 权重和空间选择异常均匀或 tie。
3. `results/exp_260714_024354_casap_new.md` 去掉 LayerNorm/Tanh 并加 SCL 后，best 3D@0.5 到 23.61，比旧版好很多。
4. 但这条线仍然远低于 frozen pretrained ASF 的水平，因为它更像从 RL_3DOD/DeCU 体系重新训练一个 detector，而不是在 ASF 强基线上微调融合。

第二条在 `decu_asf`：

1. 保留 ASF 的 pretrained frozen encoders。
2. `DecuRouter` 从 LiDAR/Radar BEV 全局池化得到 common/unique token。
3. `DecuA2Fusion` 把 router 产生的 `query_bias` 加到 ASF 的 aware query 上。
4. `FusionBaseIntegrated` 把 `decu_loss` 接入总 loss。

这条路更接近“公平增强 ASF”，但结果不好。`asf_patch_dec/results/comparison_obj_patchdec_20260803.md` 中 DeCU_ASF 在 full test conf=0.3 下 mean 3D@0.3 约 57.77，明显低于 official ASF v2 的约 66.55。

这一步的结论很关键：DeCU 的 global query bias 会破坏 ASF 已经学好的 patch-level attention；如果要结合 ASF，控制信号必须局部化、patch 化，并且不能只作为粗粒度 query 偏置。

## 7. 第四阶段：PatchDec on ASF

`asf_patch_dec` 是真正转向 ASF canonical patch 空间的第一版。

`PatchDecA2Fusion` 的做法：

1. 先沿用 ASF 的 UCP，把每个模态转成 canonical patch token。
2. 对每个模态 patch token 学 `patch_common` 和 `patch_unique`。
3. 用 GT box 生成 foreground patch mask。
4. 在 foreground patch 上约束 common/unique 正交、跨模态 common 对齐、跨模态 unique 分离。
5. 把 common/unique residual 小幅加回 patch token，再走 ASF 的 MHA/PFT/head。

后续 `ForegroundGatedPatchDecA2Fusion` 又加了 foreground gate：

1. 根据 patch token 预测前景门控。
2. 用 GT foreground mask 监督 gate。
3. gate 只控制 decoupled residual 的强弱，避免背景 patch 被过多改动。

实验结论比较清楚：

| 方法 | 主要现象 |
|---|---|
| PatchDec old | 基本贴近 ASF，但没有可靠提升 |
| ObjPatchDec Gentle/Strong | Strong 的中间 checkpoint 有一点改善，但 final 不稳定 |
| FgGated PatchDec | subset 上看起来不错，full test 只接近 baseline |

`comparison_obj_patchdec_20260803.md` 和 `patch_dec_epoch8_epoch10_analysis.md` 的整体结论是：PatchDec 证明了“在 ASF patch 空间做 common/unique 解耦是稳定的”，但如果只把解耦当正则或小 residual，它不足以稳定超过 ASF。

这就是第二次关键转向：解耦不能只是旁路辅助，它必须参与控制 sensor fusion 本身。

## 8. 第五阶段：DecControlled ASF

`dec_con_asf` 里早期的 `DecControlledA2Fusion` 把 PatchDec 变成了控制器：

1. 每个模态 patch token 仍然分解为 common 和 unique。
2. 用 `common_mean + unique_abs_mean` 预测 foreground gate。
3. 对每个模态预测 patch-level sensor score。
4. 对 sensor score 做 softmax 得到 sensor reliability。
5. 用 foreground gate 和 sensor reliability 生成 `token_scale`。
6. `token_scale` 直接缩放 ASF MHA 的 K/V token。
7. 可选地把 dec token residual 加回原 token。

直觉上，这版开始真的调制 ASF：某个 patch 被认为是前景，且某个模态在该 patch 更可靠时，该模态的 K/V token 被增强；背景或不确定区域则弱化控制。

v2 双类结果显示这条方向比单纯 PatchDec 更有价值。`results/task_dec_control_comparison_260810.md` 里 `DecControlled Prev Strong` 在 conf=0.3 full test 的 mean 3D@0.3 为 66.91，是当时 v2 对比中较强的结果。但 Bus 和 Rain 仍然是弱点。

## 9. 第六阶段：Task-Aware DecControlled ASF

当前主线是 `TaskAwareDecControlledA2Fusion`。它在 DecControlled 的基础上加了任务上下文：

1. 从 `common_mean + unique_abs_mean` 预测 class hint。
2. v2 中 `DEC_CONTROL_NUM_CLASSES=2`，对应 Sedan 和 Bus。
3. v1 Sedan-only 中 `DEC_CONTROL_NUM_CLASSES=1`。
4. class probability 经过 class context MLP。
5. class context 参与调制 attention query。
6. class context 也参与调制 MHA 后、PFT 前的 fused token。
7. 训练时增加 class loss，由 GT foreground class 监督。

因此当前方法不再只是“传感器可靠性控制”，而是：

1. foreground-aware：哪些 patch 值得强控制。
2. sensor-aware：哪个模态在该 patch 更可靠。
3. task-aware：该 patch 更像哪类目标，query/fused token 应该如何偏置。

这正是用户总结里那句话对应的实现版本。

## 10. 当前 dec_con_asf pipeline

当前主线的 end-to-end pipeline 可以写成：

```text
K-Radar sample
  -> Camera / LiDAR / Radar frozen encoders
  -> per-modality BEV feature
  -> ASF to-embed
  -> UCP canonical patch tokens x_m,p
  -> common/unique decomposition:
       c_m,p = Common_m(x_m,p)
       u_m,p = Unique_m(x_m,p)
  -> foreground gate:
       g_p = Gate(mean_m c_m,p, mean_m |u_m,p|)
  -> sensor reliability:
       a_m,p = softmax_m SensorScore(x_m,p, c_m,p, u_m,p)
  -> token-level fusion control:
       scale_m,p = clamp(1 + strength * g_p * (M * a_m,p - 1))
       x'_m,p = scale_m,p * x_m,p + optional dec residual
  -> task context:
       cls_p = ClassHead(mean_m c_m,p, mean_m |u_m,p|)
       query_delta / fused_delta from class context
  -> ASF MHA with controlled K/V and modulated query
  -> PFT
  -> detection head
  -> detection loss + SCL loss + patch_dec/control/class auxiliary losses
```

## 11. 结果脉络

### v2 Sedan+Bus

结果来源：`dec_con_asf/results/task_dec_control_comparison_260810.md` 和 `asf_patch_dec/results/comparison_obj_patchdec_20260803.md`。

| 阶段 | conf=0.3 full mean 3D@0.3 | 判断 |
|---|---:|---|
| Official ASF v2 log | 66.55 | 强基线 |
| DeCU_ASF global query bias | 57.77 | 明显破坏 ASF |
| Obj/Fg PatchDec 系列 | 约 65.0 到 65.9 | 稳定但不够强 |
| DecControlled Prev Strong | 66.91 | patch-level 控制开始有效 |
| TaskDec Balanced v2 | 66.46 | 接近 Prev Strong，但 Bus/Rain 不够稳 |
| TaskDec Robust v2 | 64.61 | 控制过强，Bus/Rain 损伤明显 |

### v1 Sedan-only

结果来源：`dec_con_asf/results/v1_task_dec_published_comparison_260812.md`。

| 方法 | Conf | 3D@0.3 | 3D@0.5 | 3D@0.7 | 判断 |
|---|---:|---:|---:|---:|---|
| Official ASF v1 | 0.0 | 87.34 | 72.95 | 18.85 | 基线 |
| TaskDec Balanced v1 final | 0.0 | 87.76 | 73.39 | 19.65 | 稳定小幅提升 |
| TaskDec Robust v1 final | 0.0 | 87.21 | 72.83 | 22.32 | 主指标略低，高 IoU 更好 |
| Official ASF v1 | 0.3 | 80.31 | 67.19 | 18.85 | 基线 |
| TaskDec Balanced v1 final | 0.3 | 80.59 | 67.45 | 19.65 | 稳定小幅提升 |
| TaskDec Robust v1 final | 0.3 | 80.42 | 67.21 | 22.32 | 高 IoU 更好 |

`v1_best_checkpoint_full_comparison_260813.md` 里 Robust `model_0` 的 conf=0.3 full 3D@0.3 达到 88.36，非常异常但潜在很重要。它还不能作为主结论，需要独立复跑确认。

### 最新训练状态

按 2026-08-14 21:04 左右重新读取：

| 实验 | 目录 | 状态 |
|---|---|---|
| `TaskDecControlMoreOpenGate_v1_0` | `logs/exp_260813_225556_TaskDecControlMoreOpenGate_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16` | epoch 8 完成，已进入 epoch 9，已有 `model_0.pt` 到 `model_8.pt` |
| `TaskDecControlStrongerControl_v1_0` | `logs/exp_260813_225557_TaskDecControlStrongerControl_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16` | epoch 8 完成，已进入 epoch 9，已有 `model_0.pt` 到 `model_8.pt` |

所以它们不是停在 epoch 0，也不是没有 checkpoint。接下来应该等它们完整结束后做 subset scan 和 full eval。

## 12. 方法主线应该如何讲

推荐论文/汇报里的故事线：

1. ASF 已经提供强大的 unified canonical patch space，但原始 ASF 的 patch fusion 主要依靠 learned attention，本身没有显式区分共享目标信息、模态噪声和类别上下文。
2. DeCU/DECALIGN 风格的 common-unique 解耦能表达“跨模态共享目标语义”和“模态特有可靠性/退化信息”。
3. 早期全局 branch routing 证明了 weather-aware routing 的动机，但也暴露出 collapse 和粗粒度控制问题。
4. 因此把解耦移动到 ASF 的 canonical patch token 上，而不是在全局 token 或 backbone 分支上操作。
5. 进一步，不把解耦只作为辅助 loss，而是用它预测 foreground gate、sensor reliability 和 class context。
6. 这些控制量动态调制 ASF 的 K/V token、attention query 和 fused token，从而形成任务感知、patch-level、sensor-aware 的融合机制。

一句更简洁的论文贡献可以写成：

> We extend ASF with a task-aware decoupled control module in the unified canonical patch space. The module decomposes each modality patch into common and unique factors, then converts them into foreground gates, sensor reliability weights, and class-aware context to modulate patch-level sensor fusion.

## 13. 当前最可靠结论

可靠结论：

1. DeCU/WCBR 的全局路由思想有动机，但在当前 K-Radar 检测设置中容易塌缩或破坏强基线。
2. 直接把 DeCU global query bias 接到 ASF 上效果明显变差。
3. 在 ASF canonical patch 空间做 common/unique 解耦是稳定的。
4. 只做 PatchDec 辅助正则/残差不足以稳定超过 ASF。
5. 把解耦表征转成 foreground gate 和 sensor reliability 去控制 K/V token，是比前几版更有希望的方向。
6. v1 Sedan-only 上，TaskDec Balanced final 已经稳定小幅超过 official ASF v1。
7. v2 Sedan+Bus 上，Bus 和 Rain 仍然是主要短板，说明 class-aware 控制还没有完全解决多类/恶劣天气鲁棒性。

暂不能过度声称的结论：

1. Robust `model_0` 的 88.36 full 3D@0.3 如果不复验，不能作为最终主结果。
2. `MoreOpenGate` 和 `StrongerControl` 还没有 final eval，当前只能说训练进入后段，不能说结果好坏。
3. 当前没有完整 ablation，因此还不能定量证明 gate、sensor score、class context 各自的独立贡献。

## 14. 下一步建议

1. 等 `MoreOpenGate` 和 `StrongerControl` 完整结束。
2. 对两组实验运行 checkpoint subset scan，优先看 `model_0` 到 final 的曲线。
3. 对 subset 最优、final、以及早期异常强 checkpoint 跑 full eval。
4. 复跑 Robust `model_0`，确认 88.36 是否可复现。
5. 做核心 ablation：无 dec token residual、无 K/V scale、无 query delta、无 fused delta、无 class loss、无 gate loss。
6. 导出 TensorBoard 里的 gate 前景/背景均值、sensor reliability 分布、class context 置信度，并按 weather/class 分组看它们和 AP 的关系。
7. 针对 v2 Bus/Rain 尝试更温和的 per-class scale clamp 或 class-specific gate，避免强控制误伤大车和雨天样本。
