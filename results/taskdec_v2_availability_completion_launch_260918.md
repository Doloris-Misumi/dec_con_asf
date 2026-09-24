# K-Radar v2 Strong：ASF 表3布局的九项补测

**完成更新（2026-09-18 13:50:52，北京时间）：** 全部13,727帧、十种设置、两档阈值及全部天气已完成，无失败；完整输入conf=0.3的全部AP与旧归档完全一致。见[与ASF表3的完整对照](taskdec_v2_availability_vs_asf_table3_260918.md)。以下保留启动时的配置与预检记录。

2026-09-18 08:04:25（北京时间）在 **GPU2** 启动后台任务，PID `4168534`。本次只做推理与评测，不训练、不换权重。GPU1 的 L4DR 实验保持运行。

08:07:30核验：正式推理已完成150/13,727帧，每帧九项新增设置加完整输入复核，无失败，速度约0.93帧/秒。初始全量推理估计约4.1小时，完整指标计算另需时间。后续0.16m Concat控制器会等待本任务成功完成、退出且GPU2空闲后才接续。

## 固定模型

采用 `exp_260806_000825_DecControlledASFStrong_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/models/model_10.pt`。

- checkpoint SHA256：`8190ccb1ad2bb1b31bba959f8e24cd6cce3c13966d7e25830cff15062b94ae99`。
- 原全量两类平均 AP3D@0.3 / @0.5 为 **66.91 / 43.05**；已完成全量评测的 Strong 续训 `model_16` 为 66.63 / 42.03。因此沿用原 Strong 版本，不根据本轮某个缺模态结果切换 checkpoint。
- “最佳”指已有完整归档支持的 Strong 版本；本轮没有重新扫描全部历史 epoch。历史选择依据属于既有评测结果，不新增声称独立验证集选模。
- 此模型为 `DecControlledA2Fusion`，包含解耦、前景门控和模态控制，不含完整 TaskDec 的 task-context 分支。

## 九种新增输入与完整输入复核

| 编号 | 设置 | 推理方式 |
|---|---|---|
| 1 | R | 仅雷达参与融合 |
| 2 | L | 仅 LiDAR 参与融合 |
| 3 | C | 仅相机参与融合 |
| 4 | C* | 仅损坏相机参与融合 |
| 5 | L+R | 相机缺失 |
| 6 | C+R | LiDAR 缺失 |
| 7 | C+L | 雷达缺失 |
| 8 | C*+L+R | 相机失效，保留三分支 |
| 9 | C+L*+R | LiDAR 无回波，保留三分支 |
| 核查 | C+L+R | 同一遍数据额外复核原有完整输入行 |

每帧编码一次正常三路输入，损坏相机另过编码器，空 LiDAR 另过原稠密 backbone；各组合分别经过原融合器和检测头。原完整输入行也重新计算，因此最终十行使用同一运行环境，并输出与旧归档的逐指标差值。

## 与 ASF 表3对齐的范围

[ASF 原论文表3](https://arxiv.org/html/2503.07029v2#S4.T3)使用相同权重比较十种输入设置，在 K-Radar v2.0 上列出 Sedan、Bus/Truck 的 AP3D@0.3，以及 Total / Normal / Overcast / Sleet / Heavy snow。本次对齐这一布局、类别与同权重推理设计。

本地保持原 Strong 的完整评测协议：v2_0 标签、ROI `[0,-16,-2,72,16,7.6]`、13,727 测试帧、revised evaluator、z_center=0.5、NMS=0.01。主结果过滤 `conf>0.3`；补充 `conf>0.0` 仍保留检测头原有的 score prefilter=0.1，并非取消所有分数过滤。

会输出：

- 十行 × 两类的 ASF 表3形式表。
- 总体及全部七种天气的 AP3D / APBEV，IoU=0.3/0.5/0.7，两种后处理阈值。
- 各天气类别 GT 数；无该类 GT 的单元格显示 N/A，不把它当性能为0。
- 完整输入 C+L+R 与历史归档的差值；如任何对应 AP 差值超过0.05点，结果文档会明确标出需核查。

**星号仍采用上轮已固定的本地失效协议。** C*为原始RGB黑帧，经过原归一化与相机编码器；L*为无回波的显式空输入约定，即零高度压缩稀疏特征经过原LiDAR稠密backbone，保留其融合token。不是移除对应分支。ASF公开说明了前向LiDAR回波完全丢失，但未从已查材料获得完整摄像头损坏生成规则，故不能宣称损坏图像/严重程度与ASF逐样本完全一致，也不能直接把这里的数字与论文表3当作所有阈值相同的复现比较。

## 已完成预检

索引0、5000、13726的三帧中：

- 十种设置均正常输出；七种正常组合共21次与原始 `network.forward` 对照，通过框、分数、类别数值检查。
- 三帧完整输入预测与 Strong 原全量评测保存的预测一致（数值容差 atol=1e-3、rtol=1e-4）。
- GT、帧顺序、天气描述与原归档一致；全量过程逐帧继续核查。
- 两类 revised evaluator 正常工作。仅在预检中重复三帧满足评测器10个非空分块限制，预检AP不得用于论文；正式评测不重复样本。
- 预检 PyTorch 显存峰值约1.59GiB；设置30%分配上限。第三方CUDA分配不受该PyTorch上限完全约束。

## 日志与输出

```bash
tail -f /home/hongsheng/dec_con_asf/analysis_exports/taskdec_v2_availability_completion_260918/run.log
```

状态：同目录 `status.json`，每50帧更新；评测阶段逐组合、阈值和天气更新。脚本在独立后台会话运行，终端断开不影响任务。

仅保存压缩预测/GT/帧标识及轻量指标，不保存中间特征，不复制数据或权重。结果位于 `results.json`、`results.md`，中间结果为 `results_partial.json`；完整输入归档核查为 `clr_archive_check.json`。

脚本：`tools/analysis/run_taskdec_v2_availability_completion_260918.py`；启动器：`scripts/launch_taskdec_v2_availability_completion_260918.py`。若仅评测阶段失败，确认原进程退出后可用 `--evaluate-only` 从完整预测包恢复计算。
