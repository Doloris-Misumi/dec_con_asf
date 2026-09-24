# TaskDec Fig.4：完整 BEV foreground gate 初稿

日期：2026-09-10。主模型 Robust model_0，K-Radar v1.0 test，R+L+C。

- 正文初稿：[PDF](paper_fig4_taskdec_bev_gate_draft.pdf)、[PNG](paper_fig4_taskdec_bev_gate_draft.png)。
- 21 帧候选总览：[三页 PDF](candidate_contact_sheet.pdf)，以及 `candidate_contact_sheet_1/2/3.png`。
- 全部数值与来源：[逐帧指标](frame_metrics.csv)、[manifest](manifest.json)、[核查记录](validation.json)、[正文选帧及英文图注](selected_frames.json)。
- [导出与绘图脚本](../../tools/analysis/export_taskdec_bev_gate.py)。

## 当前初稿与选帧依据

两个场景并排，每列由上到下为真实前向相机、LiDAR BEV + GT、预测 gate + GT。

| 场景 | 雷达帧 / 相机帧 / LiDAR 帧 | Sedan GT 数 | 完整网格 FG 均值 | BG 均值 | 选择理由 |
|---|---|---:|---:|---:|---|
| 阴天高速，seq13 | 00146 / 00321 / 00107 | 2 | 0.2995 | 0.1112 | 画面可辨识；约 22 m 和 60 m 的车辆都有局部响应，便于解释空间位置与距离 |
| 雨夜路口，seq25 | 00154 / 00464 / 00155 | 4 | 0.2882 | 0.1181 | 真实车辆、雨滴与灯光干扰直观；多个近距目标响应清楚，约 27 m 的目标响应相对较弱 |

候选来自已有 168 帧采样 gate 数据：每种天气 24 帧，按采样 FG−BG 均值差降序，在第 1、13、18 名各选一帧，共七种天气、21 帧。随后对这 21 帧重新推理完整网格，并查看相机及空间图决定正文两帧。完整网格 FG/BG 均值与原先采样均值不同，不能混用。

初稿刻意保留雨夜远一些目标的较弱响应及框外响应。可写“局部较高的 gate 响应与所示车辆区域对应”，不能据此声称所有目标均被强化、证明检测性能改善或传感器主导权切换。选帧属于定性展示，不是无偏抽样或新的全量评测。

`seq49_rdr00593`（小雪）虽然已完整导出，但独立复算有波动：最大逐 patch 差 0.03666、平均绝对差 0.00117，原因未定位。该候选暂不用于正文；没有用重跑结果覆盖首次导出。

## 空间与变量语义

- 每帧完整 gate 为 **16×90，共 1,440 个 float32 值**；21 帧合计 30,240 个 patch，无抽样补零、无特征降维替代。
- 使用实际主配置 ROI：x=0–72 m，y=−6.4–6.4 m；BEV patch 为 0.8×0.8 m。这里不是数据集示例代码中的 ±16 m 横向范围。
- 数组按 `[y, x]` 保存，x 最快变化，与 fuser 的 `(b y x)` 展平顺序一致。图中前向 x 向右，横向 y 向上，保持米制等比例和完整 ROI。
- 显示真实预测的 foreground gate：直接读取 `_dec_control_scores` 的返回值 `gate`，而不是 GT mask、sensor reliability 或 attention map。主模型 gate min/max 为 0/1，因此 `gate` 与 `gate_probability` 相同。
- 所有图采用统一 `[0,1]` 色标、nearest 显示原始网格，不做逐帧归一化、平滑或选区放大。
- 绿色框为原始尺寸的 Sedan GT。FG/BG 统计另外按训练实现的 **0.7 m 外扩 margin** 确定 patch 中心是否属于前景；画图没有用外扩 GT 替代原始框。
- `network.eval()`、batch size 1。SECOND 的预处理需要 `gt_boxes` 字段，因此在进入 **fuser** 时移除该字段，gate 前向完成后恢复供下游兼容。GT 仅在推理之后用于前景统计和叠加参照。
- LiDAR 从原始 PCD 读取，按该序列标定平移至雷达坐标，再按模型 xyz ROI 过滤。未保存点云副本。
- 相机显示原始 stereo 图的 front0 半幅（1280×720，RGB），不去雾、提亮或增强。它提供更宽视野的场景参照，不是 BEV 的坐标投影。相机中没有绘制检测预测框；本图不承担 Fig.5 的 ASF–TaskDec 检测比较。
- 雨夜案例的一个近距 GT 延伸到 x<0，按模型 ROI 边界裁切显示，原始完整 GT 仍保存在 NPZ 中。

## 保存内容与空间占用

每帧一个 `seq*_rdr*.npz`，包含 `gate`、`gate_probability`、`foreground_mask`、`gt_boxes`（x,y,z,l,w,h,theta,class）、`x_centers`、`y_centers` 和 `roi_xyz`。路径、天气、跨传感器帧号、标定、checkpoint SHA-256 和统计保存在 manifest 中。

21 帧压缩数据及初始索引合计约 **0.26 MiB**；连同正文 PDF/PNG、三页候选 PDF/PNG 和说明，整个目录 **不足 4 MiB**。不保存 common/unique/BEV 特征，不复制原始照片、PCD 或 checkpoint；关闭 pipeline 日志、模型保存及源码备份。三帧独立核查的临时副本已在核查后清理。

## 核查与运行记录

- 21 个 NPZ 都可用 `allow_pickle=False` 读取；全部 patch 为有限 float32，gate 位于 [0,1]，且与 probability 一致。
- 已核对相机、雷达、LiDAR 帧号与原始 label header；独立用旋转框几何复算的 FG mask 与全部导出一致。
- 与既有 PCA 导出的 1,066 个重叠采样 patch 对照：20 帧各自的最大 gate 差小于 0.0001；seq49/rdr00593 最大差 0.004645，另作了独立复算并标记不用。
- **正文两帧在独立进程重跑后，全部 2,880 个 gate 值逐项相同，最大绝对差为 0。**
- 推理峰值 PyTorch allocated 约 1,006 MiB（非整卡显存）；GPU 3，单帧推理。绘图阶段只用 CPU。
- 两次推理均在打印 `Finished`、保存完整数据之后，于进程退出阶段出现 `free(): invalid pointer`，exit code 134。历史 [缺模态记录](../../results/paper_availability_missing_modalities_260902.md) 及训练日志也出现同样退出错误。本次没有掩盖或修复该底层问题；保留原始导出并独立核查。CPU 绘图正常退出（code 0），PDF 为单页且已检查 PNG 预览。

## 可直接使用的图注草稿

**中文：** K-Radar v1.0 测试场景中的空间前景门控。每列依次展示前向相机、标定后的 LiDAR BEV 和 TaskDec 预测的 foreground gate；绿色轮廓为 Sedan GT，仅作位置参照。Gate 来自主模型 R+L+C 推理，融合器前向不接收 GT 框，使用完整 0.8 m patch 网格、统一 [0,1] 色标，不进行平滑。所示车辆区域呈现局部较高响应，同时保留不同目标间的响应差异。相机视野宽于 BEV 评测 ROI。

英文图注保存在 [selected_frames.json](selected_frames.json)。正式投稿可把帧号、完整网格及 margin 细节移到附录，保留共享色标、GT 语义和定性结论的边界。

## 复现与换帧

仅修改选帧或排版时运行 CPU 绘图，不需要再次加载模型：

```bash
cd /home/hongsheng/dec_con_asf
PYTHONDONTWRITEBYTECODE=1 /home/hongsheng/miniconda3/envs/rl_3dod/bin/python tools/analysis/export_taskdec_bev_gate.py render --select seq13_rdr00146,seq25_rdr00154 --contact-sheet
```

重新导出 21 帧（会覆盖同名 gate；通常无需重跑）：

```bash
cd /home/hongsheng/dec_con_asf
ulimit -c 0
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 /home/hongsheng/miniconda3/envs/rl_3dod/bin/python tools/analysis/export_taskdec_bev_gate.py export --gpu 3
```

GPU 运行需在可见 CUDA 设备的环境中执行。当前运行时可能在导出后出现上述 native 退出错误，不能仅用进程退出码判断是否获得完整文件，需同时核对 manifest、NPZ 和完成记录。输出目录通过 `--out-dir` 指定；`--select` 也可用于只导出候选中的指定帧。
