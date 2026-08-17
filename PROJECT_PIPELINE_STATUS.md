# dec_con_asf 项目 pipeline 与当前进度

生成时间：2026-08-14，基于本地目录 `/home/hongsheng/dec_con_asf` 的代码、配置、日志和 `results/` 汇总文件整理。

## 1. 项目定位

`dec_con_asf` 是在 K-Radar / ASF 代码基底上做的跨模态解耦融合实验。基线是 Availability-aware Sensor Fusion via Unified Canonical Space，也就是 ASF 的三传感器 BEV patch 级融合；新增思想来自 DECALIGN，核心是把各模态 patch token 拆成共享目标信息和模态特有信息，再用这些解耦表征去控制 ASF 的 patch-level sensor fusion。

当前最贴合项目目标的一句话表述是：

> 基于 ASF 的统一 canonical patch 空间，引入任务感知的跨模态解耦控制器，将各模态 patch 表征分解为共享目标信息和模态特有信息，并利用该解耦表征预测前景门控、传感器可靠性权重和类别上下文，从而动态调制 ASF 的 patch-level sensor fusion。

## 2. 目录角色

- `configs/`：实验配置。重要配置包括官方 ASF v1 基线、PatchDec、DecControlled、TaskAwareDecControlled，以及 v1_0 / v2_0 两套标签实验。
- `models/fuser/a2_fusion.py`：ASF 原始 A2Fusion / UCP patch 融合实现。
- `models/fuser/patch_dec_a2_fusion.py`：本项目核心新增代码，包含 `PatchDecA2Fusion`、`ForegroundGatedPatchDecA2Fusion`、`DecControlledA2Fusion`、`TaskAwareDecControlledA2Fusion`。
- `models/fuser/__init__.py`：fuser registry，已注册上述新增 fuser。
- `models/skeletons/fusion_base_integrated.py`：三路 encoder + fuser + head 的集成 skeleton，并把 SCL 和 `patch_dec_loss` 并入总 loss。
- `pipelines/pipeline_detection_v1_0.py`：训练、验证、KITTI-style evaluation 主流程。
- `main_train_patch_dec.py`：当前解耦控制实验训练入口。
- `eval_ckpt_subset.py`：固定小验证子集上扫 checkpoint。
- `eval_model_full.py`：单个 checkpoint 的 full validation 与 optional conditional validation。
- `extract_results.py`：从日志/complete_results 中提取并整理结果。
- `logs/`：训练日志、TensorBoard event、checkpoint。
- `results/`：已导出的实验结果和对比表。
- `pretrained -> /home/hongsheng/K-Radar-main/pretrained`：预训练 encoder 权重软链接。

当前目录本身不是 git repository，`git status` 在 `dec_con_asf` 下不可用。

## 3. ASF baseline pipeline

ASF 的基础路径如下：

1. Dataset：`KRadarFusion_v1_0` 读取 K-Radar camera、LiDAR、radar sparse 数据。
2. Encoder：Camera / LiDAR / 4D Radar 使用预训练 backbone。
   - Camera 输出 `cam_bev_feat`，通常 256 通道。
   - LiDAR 输出 `spatial_features_2d`，通常 512 通道。
   - Radar 输出 `bev_feat`，通常 768 通道。
3. Encoder freeze：当前 ASF / TaskDec 训练配置中 `MODEL.FREEZE: True`，主干冻结，主要训练 fuser 和 detection head。
4. To-Embed：每个模态 BEV feature 通过 `Linear1` 或 1x1/linear 投到共同维度 `DIM_COMMON=256`。
5. Unified Canonical Projection：把 BEV feature 切成 `PATCH_SIZE=[2,2]` 的 canonical patches，再映射到 `DIM_PATCH=256`。
6. Aware Query + MHA：用 learnable `aware_query` 对三路 patch K/V 做 multi-head attention。
7. PFT + reshape：Post Feature Transform 后还原成 fused BEV feature。
8. Detection head：`AnchorHeadSingleIntegrated` 做 Sedan 或 Sedan+Bus 的 3D detection。
9. SCL：在 `MODEL.SCL: True` 时，对单模态和双模态组合也过 head 计算辅助 detection loss。

## 4. 新增解耦融合 pipeline

### 4.1 PatchDecA2Fusion

`PatchDecA2Fusion` 是第一层解耦实验：

1. 继承 ASF 的 To-Embed / UCP / MHA / PFT。
2. 对每个模态的 UCP patch token 建两个 encoder：
   - `patch_common[key]`：共享目标相关表示。
   - `patch_unique[key]`：模态特有表示。
3. 训练时用 GT box 生成 foreground patch mask，只在前景 patch 上计算解耦正则。
4. 损失包括：
   - common 与 unique 正交：`abs(cos(common, unique))` 越小越好。
   - 跨模态 common 对齐：不同模态 common 的 cosine 越接近越好。
   - 跨模态 unique 分离：不同模态 unique 的 cosine 低于 margin。
5. 推理时不依赖 GT box，只把分解 residual 加回 patch token。

### 4.2 ForegroundGatedPatchDecA2Fusion

这是 PatchDec 的前景门控版本：

1. 从多模态 token 均值预测 foreground gate。
2. 训练时用 GT foreground patch mask 监督 gate。
3. gate 只调制 PatchDec residual，目的是让背景 patch 更接近原 ASF 表征。

### 4.3 DecControlledA2Fusion

这是从“辅助正则”升级到“控制融合”的版本：

1. 仍然先得到每个模态的 `common` 和 `unique`。
2. 用 `common_mean + unique_abs_mean` 预测 foreground gate。
3. 用每个模态的 `[base, common, unique, |common - common_mean|]` 预测 sensor score。
4. 对 sensor score 做 softmax 得到 patch-level sensor reliability / preference。
5. 生成 `token_scale`，直接缩放 ASF MHA 的 K/V token。
6. 可选把 `common + unique` 的 dec token residual 加到原 token 上。

直观含义：如果某个 patch 被判断为前景，且某个传感器的解耦表示更可靠，则该传感器在这个 patch 的 K/V token 会被放大；背景 patch 或不确定 patch 的控制会变弱。

### 4.4 TaskAwareDecControlledA2Fusion

这是当前主线：

1. 继承 `DecControlledA2Fusion` 的 foreground gate 和 sensor reliability control。
2. 新增 class head：从 `common_mean + unique_abs_mean` 预测 foreground class hint。
3. `DEC_CONTROL_NUM_CLASSES`：
   - v2 双类实验中是 2，对应 Sedan / Bus。
   - v1_0 Sedan-only 实验中是 1。
4. class probability 经过 `dec_control_class_context` 变成 class context。
5. class context 被 foreground gate 调制后注入：
   - query delta：调制 ASF attention query。
   - fused delta：调制 MHA 后、PFT 前的 fused token。
6. 总辅助 loss 在原 PatchDec loss 基础上增加 foreground gate loss 和 class loss。

这版最接近“任务感知的跨模态解耦控制器”。

## 5. Loss 接入方式

只有配置 `get_loss_from: detector` 时，pipeline 才会调用 `self.network.loss(dict_net)`，从而进入 `FusionBaseIntegrated.loss()`。

总 loss 结构：

```text
total_loss =
  head detection loss on fused feature
  + SCL individual / pair detection losses
  + PATCH_DEC_WEIGHT * patch_dec_loss
```

`patch_dec_loss` 内部可包含：

- `patch_dec_decouple`
- `patch_dec_common`
- `patch_dec_unique`
- `dec_control_gate_loss`
- `dec_control_class_loss`
- optional entropy / balance regularizer，目前权重为 0

当前关键配置都已经继承或设置了 `get_loss_from: detector`，所以辅助 loss 是实际生效的。

## 6. 配置谱系

### v2.0 / 双类 Sedan+Bus 路线

这些配置基于 `configs/ASF_obj_patch_dec_gentle.yml`，使用 `label_version: v2_0`，RoI 是 `[0,-16,-2,72,16,7.6]`，评测 Sedan 和 Bus or Truck。

- `ASF_patch_dec_v1.yml`：早期 PatchDec。
- `ASF_obj_patch_dec_gentle.yml` / `ASF_obj_patch_dec_strong.yml`：PatchDec gentle / strong。
- `ASF_fg_gated_patch_dec*.yml`：前景门控 PatchDec。
- `ASF_dec_controlled_gentle.yml`：`DecControlledA2Fusion`，较弱控制。
- `ASF_dec_controlled_strong.yml`：`DecControlledA2Fusion`，较强控制，v2 对比里仍是较强参考。
- `ASF_task_dec_controlled_balanced.yml`：`TaskAwareDecControlledA2Fusion`，2-class class context，较平衡。
- `ASF_task_dec_controlled_robust.yml`：`TaskAwareDecControlledA2Fusion`，控制更强，但对 Bus 和雨天有损伤。

### v1.0 / Sedan-only 路线

这些配置基于 `configs/v1_0/cfg_A2F_scl_final.yml`，使用 `label_version: v1_0`，窄 RoI `[0,-6.4,-2,72,6.4,6.0]`，只评测 Sedan。

- `configs/v1_0/cfg_A2F_scl_final.yml`：本地官方 ASF v1 复现/参考配置。
- `ASF_task_dec_controlled_balanced_v1_0.yml`：TaskDec Balanced，当前稳定最好的 final model。
- `ASF_task_dec_controlled_robust_v1_0.yml`：TaskDec Robust，final 主指标略低，但高 IoU 指标好。
- `ASF_task_dec_controlled_more_open_gate_v1_0.yml`：更开放 foreground gate，最新尝试未完成。
- `ASF_task_dec_controlled_stronger_control_v1_0.yml`：更强控制，最新尝试未完成。

## 7. 训练与评测入口

常用训练入口：

```bash
python main_train_patch_dec.py \
  --config ./configs/ASF_task_dec_controlled_balanced_v1_0.yml \
  --gpu 2 \
  --num-workers 0 \
  --final-conf-thr 0.0,0.3
```

训练流程：

1. 构建 `PipelineDetection_v1_0(path_cfg, mode='train')`。
2. 应用 runtime overrides，例如 `--num-workers`、`--max-epoch`、`--disable-train-val`。
3. 运行 `train_network()`。
4. 如果没有 `--skip-final-conditional`，训练后跑 `validate_kitti_conditional()`。

扫 checkpoint 子集：

```bash
python eval_ckpt_subset.py \
  --config ./configs/ASF_task_dec_controlled_robust_v1_0.yml \
  --exp-dir ./logs/exp_xxx \
  --gpu 3 \
  --num-subset 1000 \
  --confs 0.3 \
  --epochs all \
  --num-workers 0
```

full eval 单 checkpoint：

```bash
python eval_model_full.py \
  --config ./configs/ASF_task_dec_controlled_robust_v1_0.yml \
  --model ./logs/exp_xxx/models/model_0.pt \
  --gpu 3 \
  --epoch 0 \
  --confs 0.0,0.3 \
  --conditional \
  --num-workers 0
```

## 8. 已完成实验与结果

### 8.1 v2.0 双类实验

结果来源：`results/task_dec_control_comparison_260810.md`。

conf=0.3，condition=all，mean(Sedan, Bus)：

| Run | mean BEV@0.3 | mean 3D@0.3 | sed 3D@0.3 | bus 3D@0.3 |
|---|---:|---:|---:|---:|
| DecControlled Prev Strong | 71.23 | 66.91 | 74.58 | 59.24 |
| TaskDec Balanced | 71.40 | 66.46 | 74.51 | 58.42 |
| TaskDec Robust | 69.20 | 64.61 | 74.59 | 54.62 |

阶段结论：

- TaskDec Balanced 接近但没有超过 Prev Strong 的 mean 3D@0.3。
- TaskDec Robust 对 stricter IoU 有一定帮助，但压低 Bus 和 adverse-weather mean。
- Rain 仍未解决，TaskDec Balanced / Robust 在 rain mean 3D@0.3 上低于 Prev Strong。

### 8.2 v1.0 Sedan-only final runs

结果来源：`results/v1_task_dec_published_comparison_260812.md`。

| Method | Conf | BEV@0.3 | 3D@0.3 | BEV@0.5 | 3D@0.5 | 3D@0.7 |
|---|---:|---:|---:|---:|---:|---:|
| Official ASF v1 | 0.0 | 88.59 | 87.34 | 86.97 | 72.95 | 18.85 |
| TaskDec Balanced v1 | 0.0 | 88.73 | 87.76 | 87.33 | 73.39 | 19.65 |
| TaskDec Robust v1 | 0.0 | 88.57 | 87.21 | 86.93 | 72.83 | 22.32 |
| Official ASF v1 | 0.3 | 80.78 | 80.31 | 80.33 | 67.19 | 18.85 |
| TaskDec Balanced v1 | 0.3 | 80.93 | 80.59 | 80.48 | 67.45 | 19.65 |
| TaskDec Robust v1 | 0.3 | 80.87 | 80.42 | 80.43 | 67.21 | 22.32 |

阶段结论：

- Balanced final 是稳定主线：相对 Official ASF v1，conf=0.0 的 3D@0.3 提升 +0.42，conf=0.3 的 3D@0.3 提升 +0.28。
- Robust final 主指标不如 Balanced，但 3D@0.7 从 18.85 提到 22.32，说明更强控制可能改善定位严格指标。
- LightSnow 在 conf=0.3 下提升明显，但 Rain 仍不是稳定增益点。

### 8.3 v1.0 best-checkpoint full eval

结果来源：`results/v1_best_checkpoint_full_comparison_260813.md`。

| Run | Selected ckpt | Conf | BEV@0.3 | 3D@0.3 | BEV@0.5 | 3D@0.5 | 3D@0.7 |
|---|---|---:|---:|---:|---:|---:|---:|
| Balanced final | model_10 | 0.3 | 80.93 | 80.59 | 80.48 | 67.45 | 19.65 |
| Balanced best-subset | model_2 | 0.3 | 89.01 | 80.37 | 80.38 | 67.57 | 21.90 |
| Robust final | model_10 | 0.3 | 80.87 | 80.42 | 80.43 | 67.21 | 22.32 |
| Robust best-subset | model_0 | 0.3 | 88.84 | 88.36 | 88.10 | 67.50 | 22.04 |

注意：

- Balanced `model_2` 的 subset 优势没有转移到 full test，full 3D@0.3 反而低于 final。
- Robust `model_0` 的 full 3D@0.3 = 88.36，非常强，但 epoch 0 成为最优很异常。
- 这个结果如果可复现，会改变主结论；如果不可复现，就应以 Balanced final 的小幅稳定提升作为当前可靠结果。

## 9. 最新进行中实验

2026-08-13 晚启动了两个 v1_0 新实验。注意：早先根据旧日志尾部把它们误判为 epoch 0 停止是不正确的；按 2026-08-14 21:04 左右重新读取的日志和 checkpoint，它们已经进入训练后段。

- `TaskDecControlMoreOpenGate_v1_0`
  - 配置：`configs/ASF_task_dec_controlled_more_open_gate_v1_0.yml`
  - 日志：`logs/train_v1_more_open_gate_gpu2.log`
  - 实验目录：`logs/exp_260813_225556_TaskDecControlMoreOpenGate_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16`
  - 状态：epoch 8 已完成，日志显示已进入 `Training epoch = 9/10`。
  - 已保存 checkpoint：`model_0.pt` 到 `model_8.pt`，对应 `util_0.pt` 到 `util_8.pt`。
- `TaskDecControlStrongerControl_v1_0`
  - 配置：`configs/ASF_task_dec_controlled_stronger_control_v1_0.yml`
  - 日志：`logs/train_v1_stronger_control_gpu3.log`
  - 实验目录：`logs/exp_260813_225557_TaskDecControlStrongerControl_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16`
  - 状态：epoch 8 已完成，日志显示已进入 `Training epoch = 9/10`。
  - 已保存 checkpoint：`model_0.pt` 到 `model_8.pt`，对应 `util_0.pt` 到 `util_8.pt`。

当前沙箱内的 `ps` 不能可靠看到宿主机外部训练进程，因此进程是否仍在运行以日志持续刷新和 checkpoint 更新时间为准。

## 10. 当前进度判断

已完成：

- ASF baseline 的三模态 UCP patch fusion 路线已经能训练和评测。
- DECALIGN 风格的 common / unique patch 分解已经实现。
- foreground patch mask、foreground gate、sensor reliability score、token scale 都已接入。
- Task-aware class context 已实现，并能调制 query 和 fused token。
- `patch_dec_loss` 已通过 `FusionBaseIntegrated.loss()` 进入训练总 loss。
- v2 双类和 v1 Sedan-only 都已有完整实验和结果汇总。
- v1 Balanced final 有稳定小幅提升。
- `TaskDecControlMoreOpenGate_v1_0` 至少已有 epoch 8 checkpoint。
- `TaskDecControlStrongerControl_v1_0` 至少已有 epoch 8 checkpoint。

未完成或需要复验：

- Robust `model_0` 的 88.36 full 3D@0.3 需要独立复跑确认。
- `more_open_gate` 和 `stronger_control` 两个最新实验还没有 final/conditional evaluation 汇总，需要等训练完全结束后评测。
- v2 双类实验中 Bus 和 Rain 仍是主要短板。
- 目前控制器主要基于 foreground / class / sensor token 表征，还没有显式 weather-aware 或 class-preserving gate。
- 还没有形成最终论文级 ablation 表，例如去掉 gate、去掉 class context、只调 K/V、只调 query、不同 `PATCH_DEC_WEIGHT` 等。

## 11. 建议下一步

优先级建议：

1. 复验 Robust `model_0` full eval。
   - 用相同 checkpoint 再跑一次 `eval_model_full.py`。
   - 确认 `model_0.pt` 是 epoch 0 训练后保存，而不是初始化或混入其他权重。
   - 检查 conf=0.3 下 BEV@0.3 / 3D@0.3 同时跃升是否来自评测阈值或结果缓存。
2. 等 `more_open_gate` 和 `stronger_control` 完整结束后立刻评测。
   - 先用 `eval_ckpt_subset.py` 扫 `model_0` 到 final。
   - 再对 subset 最优、final、以及可疑早期强 checkpoint 跑 `eval_model_full.py`。
   - 重点验证“早期 checkpoint 反而好”的现象是否可复现。
3. 做控制器 ablation。
   - `DEC_CONTROL_USE_DEC_TOKEN=False`
   - `DEC_CONTROL_QUERY_STRENGTH=0`
   - `DEC_CONTROL_FUSED_RES_STRENGTH=0`
   - gate loss off / class loss off
   - sensor scale clamp 范围减弱或增强
4. 针对 v2 Bus 和 Rain 调整。
   - class-aware 的 gate 不应过度抑制 Bus。
   - 可以引入 class-specific context / per-class gate，或者给 Bus/Rain 样本更温和的 scale clamp。
5. 把当前最佳可靠结论暂定为：
   - v1 Sedan-only：TaskDec Balanced final 稳定小幅超过官方 ASF v1。
   - v2 Sedan+Bus：TaskDec 思路有效但未超过 DecControlled Prev Strong，主要瓶颈在 Bus 和 Rain。
