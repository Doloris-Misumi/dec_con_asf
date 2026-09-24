# ObjDec-LR：官方恶劣天气子集评测尝试

2026-09-20。用户明确澄清：评测我们已有的 ObjDec-LR，而不是复现 M2-Fusion。允许使用一张空闲 GPU。

## 当前执行与缺口

已在物理 GPU2 完成既有 ObjDec-LR 的验证集逐帧预测导出。PID 317950 于23:00:37启动，23:04:10保存完成，随后退出；复核GPU2显存回到26MiB、利用率0%。固定当前按完整验证集选出的 best：第30轮；原训练继续在 GPU1 运行。输入只有 LiDAR 和 Radar。

**这次导出是准备步骤，尚未完成官方恶劣天气子集评测。** 目前没有获得 Table 6 对应的官方帧号清单和与当前发布包的版本映射。不能自行挑几张雨雪图，便当作官方同一子集与其 AP 对比。

推理池为本地去重验证集 1,487 帧，不额外使用训练集或测试集来挑样本。取得官方清单后，如果其中存在不在此池内的样本，需要继续核对原始集合及训练重叠，不能静默取交集后声称全子集结果。

## 复现材料查找

1. [官方仓库](https://github.com/yanglei18/V2X-Radar)的 `main` 固定为 `1624751e31260c68d544e60599079d2104ee8a73`；递归文件树共448项，未截断。已检查发布说明、配置/模型文件清单、分支、releases及公开issue记录；未找到明确的 Table 6 天气帧列表入口。
2. [官方 Hugging Face](https://huggingface.co/datasets/yanglei18/V2X-Radar/tree/main)当前 revision 为 `c38cce27cd84fdbd5671a797dd6df2bbe3dcc907`；V目录公开两个文件：`V2X-Radar-V.zip` 与 `ImageSets.zip`，没有单独的天气元数据文件。
3. 本地 `ImageSets.zip` 仅含 train、val、test、trainval 四份列表。数据zip内共56,950个非目录文件：11,390幅图像、22,780份点云文件、22,780份标定/标签txt；未含 JSON/YAML/CSV 天气映射。只读查看zip目录，没有重新解压或复制数据集。
4. [论文 §5.2、Table 6](https://papers.nips.cc/paper_files/paper/2025/file/a501f3238029713afdad57ce7924667a-Paper-Datasets_and_Benchmarks_Track.pdf)明确表示使用车端雨、雾、雪子集，但本轮没有据此定位到可执行的帧号筛选规则。不能从论文天气分布图还原精确样本清单。
5. 旧项目页 `https://openmpd.com/column/V2X-Radar` 本轮连接超时，未能核验该渠道。上面的“未找到”限定于已检查的公开资源，不等于证明作者没有其他资料。

原始API元数据与查找记录保存于 [audit目录](../analysis_exports/v2x_official_adverse_lr_audit_260920/)。没有向作者发布issue或发送消息。

## 推理设置及已有检查

- 模型：ObjDec-LR，0.16m、2×2 patch，第30轮 best，8,781,007参数。
- 保持原置信度阈值0.001、NMS阈值0.1、ROI、FP32、micro-batch=2与解码逻辑；仅数据加载worker数设为2。
- GPU2启动前显存26MiB、利用率0%，没有计算进程；GPU0/1/3原任务不变。
- PyTorch显存上限45%；全程峰值allocated为3.2073GiB，检查时nvidia-smi整卡约6.72GiB。不是新训练。
- 冻结源码和输入清单逐项SHA核验；best权重通过单个只读文件描述符复制为独立34MiB快照，避免原训练更新best时混读。
- 首batch检查：没有相机编码器/图像输入；去除GT后预测与原验证路径数值一致。所有正式导出预测均不传GT给模型。
- 仅保存checkpoint快照、逐帧检测框压缩NPZ及轻量日志/清单；不保存BEV、token或全部中间特征。

最终状态见 [status.json](../analysis_exports/v2x_official_adverse_lr_audit_260920/objdec_lr_val_cache/status.json)：`cache_complete_waiting_official_subset`，1,487/1,487帧。逐帧预测缓存约40.79MiB，加模型快照与审核材料约75MiB；保存后逐帧重新读取并核对数组一致。GPU进程已退出。

缓存SHA256：`0128ae8e72e0228a4006bd1a2b1308d499b92b2356525fc8c1f25e3a89ba025c`。checkpoint SHA256：`ac2da48ade80732f2bc35a127441e607de4f0a6a87bb332672fc439b474c442b`。推理及压缩校验阶段合计199.41秒，不能用作论文纯模型推理速度。

```bash
tail -n 5 -F /home/hongsheng/dec_con_asf/analysis_exports/v2x_official_adverse_lr_audit_260920/objdec_lr_val_cache/inference.log
```

保存目录：[objdec_lr_val_cache](../analysis_exports/v2x_official_adverse_lr_audit_260920/objdec_lr_val_cache/)。`reference_validation.json` 是已存在的第30轮完整验证结果副本，并非本次新增天气结果。

## 取得子集后的执行入口

已准备 [evaluate_subset.py](../analysis_exports/v2x_official_adverse_lr_audit_260920/evaluate_subset.py)：从缓存预测计算指定帧列表的严格/宽松IoU、3D/BEV、Easy/Moderate/Hard结果，并记录列表来源、SHA与类别GT数量。拒绝空列表、重复帧、未缓存帧及覆盖既有结果。

```bash
CUDA_VISIBLE_DEVICES=2 CUDA_HOME=/usr/local/cuda-11.3 \
  /home/hongsheng/dec_con_asf/v2x_taskdec/.venv/bin/python \
  /home/hongsheng/dec_con_asf/analysis_exports/v2x_official_adverse_lr_audit_260920/evaluate_subset.py \
  --ids /absolute/path/to/verified_official_weather_ids.txt \
  --source-url https://official-source.example/subset-description \
  --output /absolute/path/to/new_subset_result.json
```

以上是带占位参数的入口说明，当前没有官方列表，未执行该命令。该入口保留现有本地评测协议；即便补齐帧号，仍需核对数据版本、ROI和过滤规则才能与官方 Table 6 直接比较。宽松IoU 0.5/0.25/0.25只是对齐条件之一。

## 为什么完整车端多模态公开结果较少

可确认的是：原数据集以协同感知为主要研究背景，公开模型库主要给出 C 端协同配置；V端完整表侧重分传感器基准，另有L+R恶劣天气实验。后续HRCP、RC-GeoCP等也主要研究协同融合。由此推断，研究任务侧重点、公开实现和评测材料的覆盖范围，可能影响了V端完整多模态对照数量。

这不是关于“多模态效果不好”的证据，也不能从一次公开检索认定无人做过。当前遇到的天气子集发布材料缺口是具体的复现障碍，与模型是否有效是两回事。

下一项必要材料是官方 Table 6 的天气帧ID列表、所属划分和数据版本。若改为自行标注天气，需要另行说明是本地定义子集，并在该同一子集上比较本地方法，不能沿用Table 6分数做直接排名。

## 补充检索：其他发布渠道与历史版本

2026-09-20追加。结论仍是：**在本轮可访问、已检查的公开材料中，没有定位到可执行的官方天气帧清单。** 这不等于证明作者从未发布。

| 渠道 | 本轮新增核查 | 发现与边界 |
|---|---|---|
| NeurIPS正式补充材料 | 下载并提取完整PDF文字，检查Appendix D、G及天气/划分相关内容 | D再次说明雨、雾、雪子集；G/Fig.9展示天气示例。没有给出天气帧ID或明确的子集筛选脚本 |
| NeurIPS官方报告slides | 查看14页报告及第10页天气实验 | 再次明确为车端恶劣天气子集；资源页指向同一GitHub和HF，没有另列天气下载入口 |
| GitHub公开讨论 | 39条issue/PR元数据及48条评论 | #11、#32涉及普通ImageSets漏发与补发；没有找到天气清单链接。#33作者说明仓库并未包含论文所有实验基线 |
| GitHub历史版本 | 获取12条提交记录；检查初次代码发布和重构前两个完整文件树（456/459项，均未截断） | 没有定位到按天气命名的列表；本项为历史文件树检查，不声称审计了每一行历史代码 |
| HF当前与历史 | 6条提交、初始数据发布版本文件树、当前V目录、Community API | V端当前为数据ZIP与ImageSets ZIP；2026-04-08有补传ImageSets记录；Community为0条讨论。未找到独立天气元数据入口 |
| 本地数据与转换脚本 | 复用压缩包目录审计；检查官方V端info生成脚本 | 本地ImageSets只有train/val/test/trainval；转换脚本读取普通划分，没有发现天气分组逻辑 |
| 其他入口 | 重试旧项目页、查看官方百度网盘链接、尝试OpenReview讨论API | 旧项目页超时；百度目录未能打开；OpenReview API返回403。这三个渠道的未见内容不能记作“确认没有” |

来源：[正式补充材料](https://papers.nips.cc/paper_files/paper/2025/file/a501f3238029713afdad57ce7924667a-Supplemental-Datasets_and_Benchmarks_Track.pdf)、[官方报告slides](https://neurips.cc/media/neurips-2025/Slides/121426.pdf)、[Issue #32作者回复](https://github.com/yanglei18/V2X-Radar/issues/32#issuecomment-4205146271)、[Issue #33作者回复](https://github.com/yanglei18/V2X-Radar/issues/33#issuecomment-4550873709)、[HF提交历史](https://huggingface.co/datasets/yanglei18/V2X-Radar/commits/main)。原始材料保存在[recheck](../analysis_exports/v2x_official_adverse_lr_audit_260920/recheck/)，新增主要空间为约12MB的补充材料PDF。没有发送issue或联系作者。

### 1,487帧的表述

1,487帧可以作为我们固定的**完整去重验证集**使用；它来自官方当前val列表的1,498帧，按既有图像重复规则排除11帧。普通验证划分与天气子集是两件事。论文1,500与当前发布1,498的接近支持“约数或版本清理”的可能性，但不足以证明与Table 6使用相同帧，也不足以单凭两帧差异断定二者完全不同。

建议论文表述：`We evaluate on all 1,487 frames of the deduplicated validation split derived from the official release.` 仅在报告val时使用；最终test为另一个固定集合，不混用。其他本地方法使用相同列表、ROI、过滤与评测器时，可以继续进行本地比较。

## 自建天气子集的投入与建议

当前建议：**先做小规模、与模型结果无关的可行性检查；正式天气分组为附录可选项，不取代完整集比较。** ObjDec的主要论点是表征与融合架构，已有K-Radar完整天气证据；V2X最优先补强的是统一协议下的架构适用性。

1. 先按固定随机种子从1,487帧均匀抽取约100–150帧，只看原始观测，判断雨/雾/雪是否有足够覆盖、是否易于可靠区分。此轮抽样只决定标注是否可行，不用于报告天气AP或调整模型。
2. 若值得继续，覆盖完整固定验证集逐帧标注，保存frame_id、雨/雾/雪多标签、昼夜属性、置信度和歧义备注；允许“不确定”。湿路不自动等同正在下雨，地面积雪与降雪分开记录，夜间低照度不作为雾。仅凭相邻数字ID不能认定属于同一连续天气序列。
3. 标注时隐藏模型预测和方法名；在计算分组AP前锁定筛选规则与ID列表，保留其余样本及排除原因。统计各组帧数、各类别有效GT数；极少样本/目标的类别不作强结论。雨/雾/雪可重叠，联合恶劣天气组取去重并集，不平均三个AP。
4. 固定按完整验证集选出的checkpoint，不按天气挑权重。三模态组比较同设置ObjDec、Concat和ASF-style；双模态组比较ObjDec-LR与本地L4DR，披露训练轮数和网格差异。分组结果均重新在对应样本集合上计算AP，不能从总AP拆分或按帧平均。
5. 复用已导出的ObjDec-LR第30轮预测可先做方法检查；正式汇表若采用后续best，需要重新导出对应权重的预测。其他模型若没有逐帧缓存也需补推理，但不需要重新训练。

人工投入的粗略估计：若每帧初看3–5秒，1,487帧一遍约1.2–2.1小时；加歧义复核、清单和表格整理，可先预留2–4小时，复杂天气可能更久。这是工作量估算，不是实测承诺。现有LR全验证集预测导出约199秒（含压缩核验），说明前向成本较小；AP计算与其他模型导出耗时仍需另计，不能据此承诺整项实验数分钟完成。

所得证据可命名为“manually annotated weather subsets of our validation split”，适合附录跨天气分析。它不能恢复官方Table 6的未知划分，也不能直接用M2-Fusion论文行计算领先幅度。若抽查发现天气歧义多或有效样本少，停止定量分组、保留少量定性例子更合算。

本轮只完成检索与方案整理，未进行全量天气标注，未启动训练或新的GPU评测。

## 后续：100帧天气可行性抽查已完成

2026-09-20，在用户同意后，以固定随机种子260920从1,487帧中均匀无放回抽取100帧，只查看原始图像，完成一遍视觉检查。清单、四张接触表和逐帧观察见[抽查记录](../analysis_exports/v2x_weather_pilot_260920/README.md)。其中14帧可明确观察到积雪覆盖，但不等同正在降雪；低能见度、夜景光晕等仍存在天气归因歧义。所有正式气象标签仍为未指定，没有计算天气AP，也未扩展全量标注。

该抽查支持可进一步研究环境分组，但不能恢复官方Table 6划分。结合当前论文时间，建议优先验证VoD上2×2 patch及融合前局部编码的迁移，具体配置、差距和优先顺序见[VoD调优可行性审计](objdec_vod_v2x_tuning_transfer_feasibility_260920.md)。
