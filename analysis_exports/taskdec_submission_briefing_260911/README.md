# TaskDec 现有结果与投稿讨论 PPT

整理日期：2026-09-11。用途：与师兄讨论现有实验、方法贡献、正文安排及补证据优先级。

- [可编辑 PPTX](TaskDec_现有结果与投稿讨论_260911.pptx)
- [同版 PDF](TaskDec_现有结果与投稿讨论_260911.pdf)
- [逐页讲稿与来源](汇报讲稿与来源.md)
- [第 1–12 页总览](slides_overview_01.jpg)、[第 13–24 页总览](slides_overview_02.jpg)
- [数据与页面清单](deck_manifest.json)
- [生成脚本](../../tools/analysis/make_taskdec_submission_ppt.py)

共 **24 页：前 18 页主讲，后 6 页备份**。建议主讲 15–20 分钟，按讨论情况翻阅备份。每页 PPT 均已填写演讲者备注；Markdown 讲稿另外提供同样的讲述提示和本地来源。

## 主讲路线

| 页码 | 内容 |
|---|---|
| 1–2 | 项目标题与三条主要结果 |
| 3–5 | 真实雨夜动机参照、可编辑框架、三路控制计算 |
| 6–9 | 主评测口径、K-Radar 主比较、天气分解、组件消融 |
| 10–11 | 代表性 PCA、完整 BEV gate 图 |
| 12–15 | 缺模态、VoD、早期 v2 扩展、推理开销 |
| 16–18 | 5 图 4 表的正文规划、讨论议程、建议行动顺序 |
| 19–24 | 完整 AP、天气精确值、ASF 敏感性、VoD L4DR 复现、机制诊断、强度与权重 |

## 已采用的写作决定

- 主比较采用官方 ASF checkpoint 的 `conf_thr=0.3` 复评；其他文献行注明来源。
- 消融记录完整模型与移除项均经过 1000 样本小测选择，不因 checkpoint 编号不同推断流程不一致。
- VoD 重点为原生强 PP-Concat 上的架构适配收益：EAA +0.30、DC 基本持平。披露 warm start 和 AMP/FP32 差异。
- 新增 9 月 10 日 L4DR VoD 本地复现：71.00 EAA / 84.84 DC，仍高于当前 TaskDec-PP；主讲简述，备份列完整比较。
- K-Radar 本地 L4DR 协议错配诊断不用于有效性能排名。
- v2 正向补充结果明确为不含 task context 的早期 DecControlled 变体。
- 缺模态显示 LR/LC 的正向结果，同时保留 RC 退化以及 LR 在严格 IoU 下的小幅下降。
- PCA 与 gate 为诊断证据，不声称统计独立、全天气统一优势或传感器主导权切换。
- 本地 ASF 重训 88.57 等敏感性结果在备份中保留，方便讨论。

## 编辑与生成

PPT 使用 16:9 版式，文字、表格、指标卡片、天气差值图和框架示意可直接编辑。PCA、空间 gate 与统计图作为真实科学图像嵌入；原始结果没有更改。字体为 `Noto Sans CJK SC`，PDF 已按本机字体渲染，便于跨设备预览。

框架页和动机页是汇报示意，论文 Fig.1/Fig.2 仍应按原规划完成正式图稿。Fig.4 使用已有完整 gate 初稿，PCA 从既有坐标生成两种天气的汇报版，不运行新推理或训练。

重建 PPT 与讲稿：

```bash
cd /home/hongsheng/dec_con_asf
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=4 /home/hongsheng/miniconda3/envs/rl_3dod/bin/python tools/analysis/make_taskdec_submission_ppt.py
```

在可正常启动 LibreOffice 的环境中导出 PDF：

```bash
libreoffice -env:UserInstallation=file:///tmp/taskdec_ppt_pdf_profile --headless --convert-to pdf --outdir /home/hongsheng/dec_con_asf/analysis_exports/taskdec_submission_briefing_260911 /home/hongsheng/dec_con_asf/analysis_exports/taskdec_submission_briefing_260911/TaskDec_现有结果与投稿讨论_260911.pptx
```

核查记录见 [validation.json](validation.json)。本次仅制作汇报文件，没有占用 GPU、复制 checkpoint 或重新运行实验。
