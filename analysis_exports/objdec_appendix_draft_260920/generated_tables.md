<a id="table-c1"></a>
### Table C.1. v1完整指标与置信度 / Complete v1 metrics and confidence settings

| Method | conf | 3D@0.3 | 3D@0.5 | 3D@0.7 | BEV@0.3 | BEV@0.5 | BEV@0.7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ASF released archive | 0.3 | 80.31 | 67.19 | 18.85 | 80.78 | 80.33 | 62.85 |
| ASF released archive | 0.0 | 87.34 | 72.95 | 18.85 | 88.59 | 86.97 | 62.85 |
| ASF local | 0.3 | 88.57 | 67.49 | 18.69 | 89.01 | 80.36 | 61.59 |
| ASF local | 0.0 | 87.96 | 72.96 | 18.68 | 88.80 | 87.41 | 61.57 |
| ObjDec | 0.3 | 88.36 | 67.50 | 22.04 | 88.84 | 88.10 | 62.63 |
| ObjDec | 0.0 | 88.06 | 72.83 | 22.02 | 88.84 | 87.18 | 62.63 |

**中文。** 同一方法两行使用同一权重；conf表示检测头预过滤之外的导出阈值。官方ASF行为权重对应归档。部分主指标为便于核对保留，新增严格IoU与阈值设置构成补充。

**English.** Each pair uses the same checkpoint and changes the export confidence filter, in addition to the detector prefilter. Released ASF results are checkpoint-associated archives. Main metrics are retained as anchors for the additional IoU and threshold results.

<a id="table-c2"></a>
### Table C.2. v2逐类完整指标 / Complete class-wise v2 metrics

| Method | Class | 3D@0.3 | 3D@0.5 | 3D@0.7 | BEV@0.3 | BEV@0.5 | BEV@0.7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ASF released archive | Sedan | 74.98 | 52.09 | 11.85 | 77.85 | 71.70 | 43.21 |
| ASF released archive | Bus/Truck | 58.13 | 31.06 | 7.93 | 67.85 | 53.21 | 20.85 |
| L4DR released, aligned | Sedan | 76.79 | 54.68 | 11.23 | 79.90 | 73.61 | 49.16 |
| L4DR released, aligned | Bus/Truck | 62.17 | 41.78 | 10.49 | 67.12 | 56.86 | 29.65 |
| ASF local | Sedan | 74.45 | 51.52 | 11.58 | 77.37 | 71.11 | 42.23 |
| ASF local | Bus/Truck | 55.09 | 27.88 | 7.52 | 64.27 | 46.43 | 16.84 |
| L4DR local | Sedan | 74.49 | 54.28 | 14.08 | 75.13 | 71.59 | 48.20 |
| L4DR local | Bus/Truck | 56.58 | 33.39 | 5.56 | 61.46 | 49.86 | 22.50 |
| DecControlled Strong | Sedan | 74.58 | 52.14 | 12.31 | 77.32 | 71.27 | 44.26 |
| DecControlled Strong | Bus/Truck | 59.24 | 33.97 | 9.92 | 65.14 | 50.59 | 23.13 |

**中文。** conf=0.3。补充正文以两类Mean为主的比较。Strong不含object context；本地训练组匹配训练集、11轮与有效batch，初始化和模态差异见B。

**English.** Confidence is 0.3. These class-wise results complement the class means in the main text. Strong omits object context. Local runs match the training split, 11 epochs, and effective batch size; initialization and modality differences are specified in Appendix B.

<a id="table-c3"></a>
### Table C.3. v1天气分组 / Weather-wise v1 3D AP

| Method | IoU | Total | Normal | Overcast | Fog | Rain | Sleet | Light snow | Heavy snow |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASF released archive | 0.3 | 80.31 | 79.57 | 89.89 | 90.67 | 80.97 | 80.20 | 80.89 | 71.71 |
| ASF local | 0.3 | 88.57 | 87.83 | 90.16 | 90.77 | 80.92 | 80.51 | 89.45 | 71.64 |
| ObjDec | 0.3 | 88.36 | 87.66 | 90.39 | 90.57 | 88.90 | 80.42 | 89.28 | 71.41 |
| ASF released archive | 0.5 | 67.19 | 64.56 | 79.71 | 79.57 | 67.33 | 67.28 | 77.63 | 61.61 |
| ASF local | 0.5 | 67.49 | 64.70 | 80.10 | 79.59 | 68.31 | 66.82 | 78.46 | 61.67 |
| ObjDec | 0.5 | 67.50 | 65.98 | 80.26 | 79.71 | 74.92 | 57.60 | 78.33 | 60.51 |

**中文。** Sedan，conf=0.3。Total在整个评测集合上重新计算，不是天气AP均值。

**English.** Sedan at confidence 0.3. Total is evaluated over the combined set and is not an average of weather APs.

<a id="table-c4a"></a>
### Table C.4a. v2天气分组 AP3D@0.3 / Weather-wise v2 3D AP

| Method | Class | Total | Normal | Overcast | Fog | Rain | Sleet | Light snow | Heavy snow |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASF released archive | Sedan | 74.98 | 74.14 | 82.35 | 92.26 | 66.37 | 70.43 | 88.24 | 63.61 |
| L4DR released, aligned | Sedan | 76.79 | 75.52 | 83.57 | 93.60 | 78.25 | 67.17 | 87.71 | 58.49 |
| ASF local | Sedan | 74.45 | 73.45 | 82.15 | 92.09 | 65.80 | 70.81 | 89.77 | 63.36 |
| L4DR local | Sedan | 74.49 | 73.12 | 80.06 | 92.33 | 76.27 | 54.55 | 82.74 | 51.99 |
| DecControlled Strong | Sedan | 74.58 | 73.51 | 84.30 | 94.46 | 68.11 | 72.52 | 89.56 | 63.57 |
| ASF released archive | Bus/Truck | 58.13 | 53.28 | 75.33 | — | 7.89 | 59.55 | 88.26 | 68.20 |
| L4DR released, aligned | Bus/Truck | 62.17 | 56.27 | 87.43 | — | 2.96 | 74.75 | 80.47 | 63.76 |
| ASF local | Bus/Truck | 55.09 | 50.39 | 65.31 | — | 3.59 | 50.78 | 84.75 | 68.02 |
| L4DR local | Bus/Truck | 56.58 | 54.60 | 82.07 | — | 7.81 | 59.89 | 89.16 | 54.27 |
| DecControlled Strong | Bus/Truck | 59.24 | 51.63 | 73.82 | — | 10.08 | 57.47 | 89.56 | 72.34 |

**中文。** conf=0.3；“—”表示该天气无此类别GT，不能作为零分参与平均。

**English.** Confidence is 0.3. A dash indicates no GT objects of the class in that weather group and is excluded from any class–weather comparison.

<a id="table-c4b"></a>
### Table C.4b. v2天气分组 AP3D@0.5 / Weather-wise v2 3D AP

| Method | Class | Total | Normal | Overcast | Fog | Rain | Sleet | Light snow | Heavy snow |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASF released archive | Sedan | 52.09 | 49.63 | 53.38 | 80.55 | 46.85 | 44.05 | 59.25 | 49.52 |
| L4DR released, aligned | Sedan | 54.68 | 50.21 | 56.53 | 83.81 | 53.03 | 47.42 | 62.32 | 53.33 |
| ASF local | Sedan | 51.52 | 48.90 | 57.16 | 79.89 | 45.96 | 44.83 | 59.25 | 51.24 |
| L4DR local | Sedan | 54.28 | 52.33 | 49.24 | 83.44 | 54.95 | 41.22 | 59.28 | 38.72 |
| DecControlled Strong | Sedan | 52.14 | 49.39 | 59.62 | 80.30 | 48.30 | 49.13 | 60.75 | 50.49 |
| ASF released archive | Bus/Truck | 31.06 | 23.93 | 47.04 | — | 2.48 | 38.83 | 70.81 | 32.55 |
| L4DR released, aligned | Bus/Truck | 41.78 | 36.60 | 76.06 | — | 0.68 | 62.92 | 53.30 | 41.11 |
| ASF local | Bus/Truck | 27.88 | 21.16 | 46.68 | — | 1.94 | 30.29 | 70.58 | 32.28 |
| L4DR local | Bus/Truck | 33.39 | 32.18 | 55.89 | — | 6.60 | 43.05 | 69.00 | 17.00 |
| DecControlled Strong | Bus/Truck | 33.97 | 23.94 | 49.65 | — | 5.05 | 38.48 | 75.09 | 39.37 |

**中文。** conf=0.3；“—”表示该天气无此类别GT，不能作为零分参与平均。

**English.** Confidence is 0.3. A dash indicates no GT objects of the class in that weather group and is excluded from any class–weather comparison.

<a id="table-d1"></a>
### Table D.1. 正文消融的补充指标 / Additional ablation metrics

| Variant | 3D@0.7 | BEV@0.7 | BEV@0.3 |
| --- | --- | --- | --- |
| Full ObjDec | 22.04 | 62.63 | 88.84 |
| w/o modality contribution control | 11.08 | 61.36 | 80.38 |
| w/o object context | 17.10 | 54.91 | 80.68 |
| w/o decoupling supervision | 16.49 | 55.71 | 80.65 |
| w/o foreground gate | 19.41 | 55.49 | 80.65 |

**中文。** v1，conf=0.3；正文已展示的3D@0.3/@0.5及BEV@0.5不再重复。完整模型取与C.1一致的原始JSON，移除项来自对应结果归档。

**English.** v1 at confidence 0.3. The 3D@0.3/@0.5 and BEV@0.5 columns already shown in the main ablation table are omitted. The full-model row follows the same JSON as Table C.1; ablated rows follow their experiment records.

<a id="table-e1"></a>
### Table E.1. 按模态对拆分的全量高维相似度 / Full-set similarity by modality pair

| Weather | Frames | Sequences | FG patches | Shared C–L | Shared C–R | Shared L–R | Specific C–L | Specific C–R | Specific L–R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Normal | 4309 | 17 | 317581 | 0.9455 | 0.9584 | 0.9621 | 0.3429 | 0.6545 | 0.3410 |
| Overcast | 383 | 2 | 33918 | 0.9520 | 0.9574 | 0.9676 | 0.4211 | 0.6501 | 0.4111 |
| Fog | 1049 | 6 | 43909 | 0.9391 | 0.9505 | 0.9647 | 0.4659 | 0.6612 | 0.4572 |
| Rain | 1317 | 8 | 125257 | 0.9431 | 0.9565 | 0.9586 | 0.3855 | 0.6511 | 0.3767 |
| Sleet | 1106 | 7 | 41665 | 0.9584 | 0.9478 | 0.9638 | 0.5112 | 0.6529 | 0.4840 |
| Light snow | 803 | 4 | 36196 | 0.9470 | 0.9582 | 0.9622 | 0.4787 | 0.6590 | 0.4643 |
| Heavy snow | 1098 | 7 | 44123 | 0.9525 | 0.9481 | 0.9601 | 0.4954 | 0.6458 | 0.4693 |

**中文。** 原始256维空间；先对帧内匹配前景位置求平均，再对天气内各帧等权平均。

**English.** Cosines in the original 256-dimensional space are averaged over matched foreground locations within each frame, then equally over frames within a weather group.

<a id="table-e2"></a>
### Table E.2. L–R相似度分位数 / L–R similarity quantiles

| Weather | Branch | Pair | Median | 5th percentile | 95th percentile |
| --- | --- | --- | --- | --- | --- |
| normal | common | LiDAR–4D Radar | 0.9632 | 0.9433 | 0.9776 |
| normal | unique | LiDAR–4D Radar | 0.3384 | 0.2113 | 0.4948 |
| heavysnow | common | LiDAR–4D Radar | 0.9662 | 0.9141 | 0.9806 |
| heavysnow | unique | LiDAR–4D Radar | 0.4538 | 0.2578 | 0.7363 |

**中文。** 每个观测值为一帧中匹配前景patch余弦的均值；分位范围描述帧间变异，不是置信区间。

**English.** Each observation is a frame-level mean of matched-patch cosines. Quantiles describe variation across frames, not confidence intervals.

<a id="table-e3"></a>
### Table E.3. 正文gate选例的逐帧统计 / Frame-level statistics of the main gate examples

| Weather | Frame ID | GT objects | FG patches | FG gate mean | BG gate mean | FG − BG |
| --- | --- | --- | --- | --- | --- | --- |
| Normal | seq20_rdr00628 | 1 | 28 | 0.3154 | 0.1208 | 0.1946 |
| Overcast | seq13_rdr00146 | 2 | 60 | 0.2995 | 0.1112 | 0.1883 |
| Fog | seq39_rdr00582 | 1 | 40 | 0.2942 | 0.1078 | 0.1864 |
| Rain | seq25_rdr00154 | 4 | 142 | 0.2882 | 0.1181 | 0.1702 |
| Sleet | seq50_rdr00456 | 2 | 65 | 0.2913 | 0.1179 | 0.1734 |
| Light snow | seq43_rdr00169 | 1 | 35 | 0.3711 | 0.1103 | 0.2608 |
| Heavy snow | seq55_rdr00385 | 1 | 35 | 0.2817 | 0.1186 | 0.1631 |

**中文。** 每帧均为1,440个完整patch。前景依据0.7m扩张GT区域在预测后划分；这些是七个定性选例的帧内统计，不是七天气总体均值。

**English.** Each frame has 1,440 complete patches. Foreground regions use GT footprints expanded by 0.7 m after prediction. Values summarize seven qualitative examples, not weather-wide means.

<a id="table-f1"></a>
### Table F.1. v1固定权重的输入可用性 / v1 input availability with fixed weights

| Input | conf | 3D@0.3 | 3D@0.5 | BEV@0.5 | Δ 3D@0.3 vs CLR |
| --- | --- | --- | --- | --- | --- |
| C+L+R | 0.3 | 88.36 | 67.50 | 88.10 | +0.00 |
| C+L+R | 0.0 | 88.06 | 72.83 | 87.18 | +0.00 |
| L+R | 0.3 | 88.06 | 71.68 | 85.45 | -0.30 |
| L+R | 0.0 | NR | NR | NR | NR |
| C+L | 0.3 | 86.77 | 72.58 | 86.35 | -1.59 |
| C+L | 0.0 | 86.16 | 69.74 | 83.76 | -1.90 |
| C+R | 0.3 | 57.62 | 34.59 | 55.52 | -30.74 |
| C+R | 0.0 | 63.65 | 38.48 | 60.28 | -24.41 |
| L | 0.3 | 79.58 | 60.05 | 77.96 | -8.77 |
| L | 0.0 | 85.46 | 59.23 | 77.96 | -2.60 |
| R | 0.3 | 49.81 | 26.64 | 46.80 | -38.55 |
| R | 0.0 | 61.75 | 30.86 | 52.60 | -26.31 |
| C | 0.3 | 0.86 | 0.16 | 0.21 | -87.49 |
| C | 0.0 | 0.32 | 0.03 | 0.14 | -87.74 |
| C* | 0.3 | 0.00 | 0.00 | 0.00 | -88.36 |
| C* | 0.0 | 0.17 | 0.01 | 0.07 | -87.89 |
| C*+L+R | 0.3 | 88.36 | 67.41 | 88.09 | +0.00 |
| C*+L+R | 0.0 | 88.06 | 72.75 | 87.17 | +0.00 |
| C+L*+R | 0.3 | 50.26 | 34.83 | 49.27 | -38.09 |
| C+L*+R | 0.0 | 63.05 | 38.48 | 61.12 | -25.01 |

**中文。** 10,065帧，正式v1 ObjDec。LR的conf=0.3行使用保存预测的已核查复算值（来源保留两位小数）；NR表示本稿尚无已核实的LR conf=0.0汇总，不是零分。所有其余行来自原始JSON。

**English.** The same v1 ObjDec checkpoint is evaluated on 10,065 frames. The LR/conf=0.3 row uses the audited recomputation of saved predictions, reported to two decimals in its source. NR denotes an unverified summary for LR/conf=0.0, not zero performance. Other rows are read from their JSON records.

<a id="table-f2"></a>
### Table F.2. v2固定Strong权重的输入可用性 / v2 input availability with fixed Strong weights

| Input | conf | Mean 3D@0.3 | Mean 3D@0.5 | Mean BEV@0.5 | Δ mean 3D@0.3 vs CLR |
| --- | --- | --- | --- | --- | --- |
| C+L+R | 0.3 | 66.91 | 43.05 | 60.93 | +0.00 |
| C+L+R | 0.0 | 69.41 | 43.81 | 63.23 | +0.00 |
| L+R | 0.3 | 66.02 | 41.81 | 59.93 | -0.89 |
| L+R | 0.0 | 68.96 | 42.77 | 62.74 | -0.46 |
| C+L | 0.3 | 64.08 | 41.17 | 57.80 | -2.83 |
| C+L | 0.0 | 65.13 | 41.16 | 58.53 | -4.28 |
| C+R | 0.3 | 34.25 | 16.99 | 29.97 | -32.66 |
| C+R | 0.0 | 34.73 | 16.82 | 29.89 | -34.68 |
| L | 0.3 | 59.39 | 32.36 | 53.45 | -7.53 |
| L | 0.0 | 62.33 | 33.47 | 54.75 | -7.08 |
| R | 0.3 | 30.51 | 13.59 | 26.28 | -36.40 |
| R | 0.0 | 31.63 | 13.45 | 26.70 | -37.79 |
| C | 0.3 | 0.01 | 0.00 | 0.01 | -66.90 |
| C | 0.0 | 0.01 | 0.00 | 0.01 | -69.40 |
| C* | 0.3 | 0.01 | 0.01 | 0.01 | -66.90 |
| C* | 0.0 | 0.01 | 0.01 | 0.00 | -69.40 |
| C*+L+R | 0.3 | 66.93 | 42.98 | 60.91 | +0.01 |
| C*+L+R | 0.0 | 69.40 | 43.73 | 63.19 | -0.01 |
| C+L*+R | 0.3 | 27.99 | 14.11 | 25.01 | -38.92 |
| C+L*+R | 0.0 | 34.70 | 15.51 | 30.76 | -34.71 |

**中文。** 13,727帧，Sedan与Bus/Truck等权平均；每个conf的差值均对应该conf下的完整输入。星号表示F节定义的本地损坏输入。

**English.** Equal class means over Sedan and Bus/Truck on 13,727 frames. Deltas use the full-input result at the same confidence filter. Stars denote the locally defined corruptions in Appendix F.

<a id="table-g1"></a>
### Table G.1. 空间粒度与完整预算结果 / Spatial granularity and full-budget results

| Method | Sensors | Grid (m) | Best epoch | Val mean 3D | Test Vehicle | Test Pedestrian | Test Cyclist | Test mean 3D | Test mean BEV |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Concat | C+L+R | 0.4 | 75 | 74.31 | 81.52 | 65.81 | 79.98 | 75.77 | 81.26 |
| ASF-style | C+L+R | 0.4 | 75 | 72.76 | 78.57 | 58.93 | 79.02 | 72.17 | 78.21 |
| ObjDec 4×4 | C+L+R | 0.4 | 80 | 71.31 | 78.82 | 58.75 | 79.09 | 72.22 | 78.76 |
| ObjDec 2×2 | C+L+R | 0.4 | 80 | 74.19 | 80.73 | 62.36 | 78.99 | 74.03 | 80.26 |
| Concat | C+L+R | 0.16 | 75 | 81.46 | 84.81 | 76.84 | 84.05 | 81.90 | 86.47 |
| ASF-style | C+L+R | 0.16 | 80 | 81.03 | 84.54 | 76.17 | 83.18 | 81.30 | 85.72 |
| ObjDec 2×2 | C+L+R | 0.16 | 70 | 81.41 | 84.06 | 75.94 | 84.13 | 81.38 | 86.27 |
| L4DR | L+R | 0.16 | 80 | 77.19 | 83.17 | 73.25 | 78.31 | 78.24 | 82.56 |
| ObjDec-LR 2×2 | L+R | 0.16 | 75 | 79.12 | 83.87 | 74.84 | 80.24 | 79.65 | 83.81 |

**中文。** 均为80轮预算下按val选择的best，Moderate AP_R40；旧0.4m组补充正文0.16m表。Val与test分别列出，不用训练期val替代test。

**English.** Best checkpoints are selected by validation under an 80-epoch budget, using Moderate AP_R40. The 0.4 m group supplements the main 0.16 m comparison. Validation and test results are reported separately.

<a id="table-g2"></a>
### Table G.2. 已完成0.16m组的BEV及末轮补充 / BEV and last-checkpoint results for completed 0.16 m runs

| Method | Checkpoint | Epoch | BEV Vehicle | BEV Pedestrian | BEV Cyclist | Mean BEV | Mean 3D |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Concat | best | 75 | 92.12 | 80.66 | 86.64 | 86.47 | 81.90 |
| Concat | last | 80 | 92.02 | 80.70 | 86.69 | 86.47 | 81.97 |
| ASF-style | best | 80 | 90.95 | 80.41 | 85.80 | 85.72 | 81.30 |
| ASF-style | last | 80 | 90.95 | 80.41 | 85.80 | 85.72 | 81.30 |
| ObjDec 2×2 | best | 70 | 90.91 | 80.88 | 87.02 | 86.27 | 81.38 |
| ObjDec 2×2 | last | 80 | 90.84 | 81.16 | 87.07 | 86.35 | 81.55 |
| L4DR | best | 80 | 89.74 | 76.60 | 81.35 | 82.56 | 78.24 |
| L4DR | last | 80 | 89.74 | 76.60 | 81.35 | 82.56 | 78.24 |
| ObjDec-LR 2×2 | best | 75 | 90.02 | 78.34 | 83.08 | 83.81 | 79.65 |
| ObjDec-LR 2×2 | last | 80 | 90.10 | 78.21 | 83.09 | 83.80 | 79.75 |

**中文。** 去重test。best按val选择；last为第80轮，报告其结果不改变选模规则。五组0.16m实验的best/last均已完成。

**English.** Deduplicated test results. Best is selected by validation, whereas last is epoch 80. Reporting last does not change the selection rule. Best/last evaluations are complete for all five 0.16 m runs.

<a id="table-g3a"></a>
### Table G.3a. VoD整体标注区域 / VoD Entire Annotated Area (EAA)

| Method | Source | Epoch | Car | Pedestrian | Cyclist | Mean |
| --- | --- | --- | --- | --- | --- | --- |
| PP-Concat (historical) | Local | 80 | 66.88 | 63.38 | 79.39 | 69.88 |
| ObjDec (warm-start, historical) | Local | 79 | 67.50 | 63.66 | 79.38 | 70.18 |
| ObjDec (2×2 + local) | Local | 75 | 68.72 | 65.59 | 79.38 | 71.23 |
| ObjDec (+ adapted anchors) | Local | 80 | 66.93 | 65.28 | 83.89 | 72.03 |
| L4DR | Local | 99 | 68.69 | 65.35 | 78.98 | 71.00 |
| InterFusion | Reported | — | 66.50 | 64.50 | 78.50 | 69.83 |
| L4DR | Reported | — | 69.10 | 66.20 | 82.80 | 72.70 |

**中文。** 所有方法输入均为L+R，无额外人工雾；官方VoD 11点3D AP，类别IoU为0.5/0.25/0.25。本地结果为1,296帧验证集；EAA与DC的同名行使用同一权重。两组近期ObjDec按EAA选模，训练及历史参照差异见G.4。Reported两行取自L4DR正式论文表3 [L4DR]，Mean为其公开类别值的算术平均；Local均值保留原评分输出。

**English.** All methods use L+R without added synthetic fog. Official VoD 11-point 3D AP uses class IoUs of 0.5/0.25/0.25. Local results use 1,296 validation frames, with the same checkpoint for each method across EAA and DC. The two recent ObjDec runs select checkpoints by EAA; training and historical-reference differences are detailed in G.4. Reported rows are from Table 3 of the published L4DR paper [L4DR], with means computed from its class values. Local means retain the evaluator output.

<a id="table-g3b"></a>
### Table G.3b. VoD驾驶走廊 / VoD Driving Corridor (DC)

| Method | Source | Epoch | Car | Pedestrian | Cyclist | Mean |
| --- | --- | --- | --- | --- | --- | --- |
| PP-Concat (historical) | Local | 80 | 90.77 | 71.09 | 89.53 | 83.80 |
| ObjDec (warm-start, historical) | Local | 79 | 90.59 | 71.02 | 89.76 | 83.79 |
| ObjDec (2×2 + local) | Local | 75 | 90.74 | 73.23 | 90.09 | 84.69 |
| ObjDec (+ adapted anchors) | Local | 80 | 89.44 | 73.02 | 88.83 | 83.76 |
| L4DR | Local | 99 | 90.51 | 75.13 | 88.90 | 84.84 |
| InterFusion | Reported | — | 90.70 | 72.00 | 88.70 | 83.80 |
| L4DR | Reported | — | 90.80 | 76.10 | 95.50 | 87.47 |

**中文。** 所有方法输入均为L+R，无额外人工雾；官方VoD 11点3D AP，类别IoU为0.5/0.25/0.25。本地结果为1,296帧验证集；EAA与DC的同名行使用同一权重。两组近期ObjDec按EAA选模，训练及历史参照差异见G.4。Reported两行取自L4DR正式论文表3 [L4DR]，Mean为其公开类别值的算术平均；Local均值保留原评分输出。

**English.** All methods use L+R without added synthetic fog. Official VoD 11-point 3D AP uses class IoUs of 0.5/0.25/0.25. Local results use 1,296 validation frames, with the same checkpoint for each method across EAA and DC. The two recent ObjDec runs select checkpoints by EAA; training and historical-reference differences are detailed in G.4. Reported rows are from Table 3 of the published L4DR paper [L4DR], with means computed from its class values. Local means retain the evaluator output.

<a id="table-g4"></a>
### Table G.4. VoD补充难度指标 / Supplementary KITTI difficulty metrics on VoD

| Configuration | Epoch | Metric | Easy mean | Moderate mean | Hard mean |
| --- | --- | --- | --- | --- | --- |
| ObjDec (2×2 + local) | 75 | 3D | 83.43 | 78.64 | 72.23 |
| ObjDec (+ adapted anchors) | 80 | 3D | 83.06 | 78.35 | 72.02 |
| ObjDec (2×2 + local) | 75 | BEV | 85.47 | 80.55 | 74.56 |
| ObjDec (+ adapted anchors) | 80 | BEV | 85.33 | 80.92 | 75.02 |

**中文。** 与表G.3相同的EAA选中权重，三类等权平均；3D/BEV的IoU均为0.5/0.25/0.25。此表使用KITTI难度过滤及AP_R40，与官方EAA/DC的区域过滤和11点AP不同，不混用两套数值。

**English.** Equal class means for the same EAA-selected checkpoints as Table G.3, using 3D/BEV IoUs of 0.5/0.25/0.25. KITTI difficulty filtering and AP_R40 differ from the region filtering and 11-point AP of official EAA/DC, so the two sets of scores are not interchangeable.

<a id="table-h1"></a>
### Table H.1. 延迟分布 / Latency distributions

| Model | Execution | Mean ms | Median ms | P95 ms | Std ms | 1000 / mean ms |
| --- | --- | --- | --- | --- | --- | --- |
| ASF | Eager | 84.00 | 82.63 | 93.26 | 5.34 | 11.91 |
| ASF | CUDA Graph | 59.30 | 59.10 | 64.82 | 2.83 | 16.86 |
| ObjDec | Eager | 84.69 | 84.50 | 89.98 | 3.01 | 11.81 |
| ObjDec | CUDA Graph | 59.57 | 59.23 | 65.93 | 2.92 | 16.79 |

**中文。** 每种模型/路径100个不同计时帧、重复两轮；最后一列为计时路径吞吐，不包含读盘。标准差描述计时变异，不是多种子检测误差。

**English.** Each model/path uses 100 distinct timed frames repeated twice. The final column is the reciprocal of measured latency, excluding disk loading. Standard deviations describe timing variation rather than multi-seed detection uncertainty.
