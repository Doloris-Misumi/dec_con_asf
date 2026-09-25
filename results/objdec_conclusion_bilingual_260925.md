# ObjDec Conclusion（2026-09-25）

## 中文

本文提出 ObjDec，一种以在对应局部区域中学习和使用共享与模态特有表征为核心的多传感器三维检测架构。目标区域监督为表征解耦提供明确的检测指向，学习到的表征则直接参与 token 更新，并通过前景门控、模态贡献控制和目标上下文引导跨模态交互。K-Radar 上的实验、组件消融与表征分析，支持了该设计在所报告评测设置下的有效性。在 V2X-Radar-V 上的训练与评测进一步表明，该架构适用于不同的目标类别和传感器组合。这些结果支持以表征解耦组织局部传感器融合，并通过目标引导将学习到的表征与检测任务联系起来。

## English

We presented ObjDec, a multi-sensor 3D detection architecture centered on learning and using shared and modality-specific representations in corresponding local regions. Object-region supervision gives representation decoupling a detection-specific focus, while the learned representations contribute directly to token updates and guide cross-modal interaction through foreground gating, modality contribution control, and object context. Experiments on K-Radar, together with component ablations and representation analyses, support the effectiveness of this design under the reported evaluation settings. Training and evaluation on V2X-Radar-V further demonstrate its applicability to different object categories and sensor combinations. These findings support representation decoupling as a useful organizing principle for local sensor fusion, with object guidance connecting the learned representations to detection.
