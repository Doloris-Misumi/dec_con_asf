# ObjDec 前四部分初稿命名统一记录

修改时间：2026-09-19T00:45:02+08:00。范围仅为摘要、Introduction、Related Work、Methods四份现有Markdown初稿。

论文标题：**Decoupling to Fuse: Learning Shared and Modality-Specific Representations for Multi-Sensor 3D Object Detection**。

方法名：**ObjDec**；全称：**Object-Guided Representation Decoupling（目标引导的表征解耦）**。

## 修改位置

| 文件 | 修改内容 | 原TaskDec提及数 |
|---|---|---:|
| [taskdec_abstract_initial_draft_260917.md](/home/hongsheng/dec_con_asf/results/taskdec_abstract_initial_draft_260917.md) | 文档标题、已确定论文标题、方法全称、中文摘要中的方法名和目标引导融合定位；结构说明及v2变体说明统一名称和object context术语。 | 8 |
| [taskdec_introduction_bilingual_initial_260917.md](/home/hongsheng/dec_con_asf/results/taskdec_introduction_bilingual_initial_260917.md) | 文档标题、已确定论文标题、方法全称、中英文架构介绍、实验段落、第二项贡献和正文外图示/变体说明。架构介绍使用多传感器融合架构；贡献名使用目标引导融合。 | 13 |
| [taskdec_related_work_bilingual_initial_260917.md](/home/hongsheng/dec_con_asf/results/taskdec_related_work_bilingual_initial_260917.md) | 文档标题、方法全称、章节安排、中英文两小节的本文方法定位及引用说明中的方法名；其他论文的术语和原始标题保留。 | 15 |
| [taskdec_methods_bilingual_initial_260917.md](/home/hongsheng/dec_con_asf/results/taskdec_methods_bilingual_initial_260917.md) | 文档标题、方法全称、中英文Overview、图2中英文图注、附录分工、v1/v2/V2X变体说明及实现链接的显示名称。 | 13 |

四稿原有TaskDec提及共49处，其中摘要和Introduction的两处旧标题整体改为已确定标题；其他提及统一为ObjDec。各稿增加一处方法全称说明。

## 术语处理

- 本文方法名：TaskDec → ObjDec。
- 本文架构/贡献中的“任务感知融合架构” → “目标引导融合架构”；已有“学习共享与模态特有表征，并利用目标相关信息引导融合”句子中的架构类别统一为“多传感器融合架构”，避免重复修饰。
- 对应英文：a task-aware architecture → a multi-sensor fusion architecture；A task-aware fusion architecture driven by learned representations → An object-guided fusion architecture driven by learned representations。
- 本文变体与实现说明中的task context/task-context → 目标上下文（object context）。已有objectness、object context和目标上下文用语继续沿用。

## 保留及核验

- FactorCL的task-relevant / 任务相关、BEVFusion原始论文标题中的Multi-Task，以及“检测任务”“分类/回归任务分解”等一般语义保持原义。
- 工程文件名、Markdown链接目标、配置键及`task_binary`保持不变；链接的展示名称可以使用ObjDec。没有重命名文件或训练类。
- 逐稿核验：原有数字、公式块、行内公式、行内代码和全部链接目标均与修改前一致；未改动训练源代码、配置、实验结果或运行任务。
- 本轮仅统一命名和对应方法定位，没有同步改写历史实验进度说明、重写摘要结果段或修改引用内容。

## 修改前备份与差异

- [修改前四稿](/home/hongsheng/dec_con_asf/results/draft_history/objdec_naming_260919_004502)
- [逐行差异](/home/hongsheng/dec_con_asf/results/draft_history/objdec_naming_260919_004502/changes.diff)
- [核验清单与文件SHA256](/home/hongsheng/dec_con_asf/results/draft_history/objdec_naming_260919_004502/manifest.json)
