# 第50轮V2X结果与VoD训练进度

核查时间：2026-09-21T07:55:28+08:00。本轮只读收集训练结果并整理报告，没有启动、停止或修改实验。

## V2X-Radar-V第50轮

固定去重val1,487帧，0.16m网格；AP_R40、Moderate、Vehicle/Pedestrian/Cyclist严格IoU=0.7/0.5/0.5。下列均为本地训练与同一验证口径，模态仍需区分。

### 3D

| 方法 | Vehicle | Pedestrian | Cyclist | Mean |
| --- | --- | --- | --- | --- |
| ObjDec C+L+R | 81.12 | 72.20 | 81.83 | 78.38 |
| Concat C+L+R | 81.24 | 71.63 | 80.83 | 77.90 |
| L4DR L+R | 80.38 | 67.99 | 77.13 | 75.17 |
| ObjDec−Concat C+L+R | -0.12 | +0.57 | +1.00 | +0.48 |
| ObjDec−L4DR L+R | +0.75 | +4.20 | +4.69 | +3.21 |

### BEV

| 方法 | Vehicle | Pedestrian | Cyclist | Mean |
| --- | --- | --- | --- | --- |
| ObjDec C+L+R | 90.59 | 76.87 | 84.87 | 84.11 |
| Concat C+L+R | 90.73 | 76.57 | 83.78 | 83.69 |
| L4DR L+R | 89.63 | 72.28 | 79.64 | 80.52 |
| ObjDec−Concat C+L+R | -0.14 | +0.30 | +1.09 | +0.42 |
| ObjDec−L4DR L+R | +0.96 | +4.59 | +5.23 | +3.59 |

### ObjDec第45→50轮

| 指标 | 类别 | 45轮 | 50轮 | 变化 |
| --- | --- | --- | --- | --- |
| 3D | Vehicle | 80.94 | 81.12 | +0.19 |
| 3D | Pedestrian | 69.98 | 72.20 | +2.21 |
| 3D | Cyclist | 81.53 | 81.83 | +0.30 |
| 3D | Mean | 77.48 | 78.38 | +0.90 |
| BEV | Vehicle | 90.60 | 90.59 | -0.01 |
| BEV | Pedestrian | 74.94 | 76.87 | +1.92 |
| BEV | Cyclist | 85.20 | 84.87 | -0.33 |
| BEV | Mean | 83.58 | 84.11 | +0.53 |

### 同轮趋势

| 轮次 | ObjDec 3D | Concat 3D | 差值 | ObjDec BEV | Concat BEV | 差值 |
| --- | --- | --- | --- | --- | --- | --- |
| 30 | 69.92 | 69.30 | +0.61 | 78.38 | 79.77 | -1.40 |
| 35 | 73.80 | 74.27 | -0.47 | 80.90 | 80.99 | -0.09 |
| 40 | 76.55 | 74.67 | +1.89 | 82.63 | 82.00 | +0.63 |
| 45 | 77.48 | 76.22 | +1.26 | 83.58 | 82.93 | +0.65 |
| 50 | 78.38 | 77.90 | +0.48 | 84.11 | 83.69 | +0.42 |

第50轮更新ObjDec的已评估最佳3D均值至78.38，BEV均值84.11；较第45轮分别+0.90/+0.53。行人贡献最大，3D+2.21、BEV+1.92；车辆BEV基本持平，骑行者BEV回落0.33点。

对Concat仍有整体优势，但3D领先从第45轮1.26缩到0.48，BEV从0.65缩到0.42；行人3D由低0.38变为高0.57，车辆3D则低0.12。不能表述为优势逐轮扩大。对同轮L4DR均值高3.21/3.59，但C+L+R与L+R不是相同模态。

Concat已完成80轮，其按3D选出的第75轮为81.46/85.75；ObjDec第50轮距离该权重为−3.08/−1.64。这是不同轮次的收敛目标参考，不与同轮差值混用。

### 其他新结果：第40轮同轮比较

| 方法 | 3D Mean | BEV Mean |
| --- | --- | --- |
| ObjDec C+L+R | 76.55 | 82.63 |
| Concat C+L+R | 74.67 | 82.00 |
| L4DR L+R | 73.33 | 79.20 |
| ASF-style C+L+R | 75.71 | 81.68 |
| ObjDec L+R | 71.48 | 79.53 |

ASF-style和ObjDec-LR的最新完整验证均为第40轮，不混入第50轮表。第40轮ObjDec CLR对ASF-style的3D/BEV为+0.84/+0.96；ObjDec LR对L4DR LR为−1.85/+0.33。

## VoD新实验

配置为2×2 patch＋两层局部编码＋token归一化，0.16m，FP32，batch8×累积2；从头80轮，5轮一评。启动见[objdec_vod_patch2_local_launch_260921.md](objdec_vod_patch2_local_launch_260921.md)。
| 轮次 | EAA Car | EAA Ped. | EAA Cyc. | EAA mean | DC mean |
| --- | --- | --- | --- | --- | --- |
| 5 | 45.62 | 52.23 | 77.23 | 58.36 | 72.97 |
| 10 | 48.86 | 58.6 | 77.5 | 61.65 | 74.94 |
| 15 | 51.82 | 57.36 | 80.05 | 63.08 | 80.36 |
| 20 | 51.17 | 60.36 | 77.95 | 63.16 | 78.36 |
| 25 | 52.92 | 60.05 | 77.9 | 63.62 | 79.31 |
| 30 | 52.04 | 59.56 | 77.47 | 63.03 | 78.57 |
| 35 | 52.98 | 59.74 | 77.84 | 63.52 | 79.49 |
| 40 | 56.89 | 60.34 | 77.01 | 64.75 | 78.83 |

按EAA选出的当前best是第40轮64.75，其对应DC为78.83；DC单独最高是第15轮80.36，不能拼成一行最佳权重。第35→40轮EAA+1.23、DC−0.66，车辆EAA+3.91，行人+0.60，骑行者−0.83；改善主要来自车辆，尚未体现整体小目标优势。

旧warm版最终EAA/DC70.18/83.79，当前第40轮差−5.43/−4.96；本地L4DR最终71.00/84.84，差−6.25/−6.01。训练阶段与warm-start预算不同，暂不能据此判断新结构最终优劣；也没有依据提前承诺超过旧版或L4DR。

### VoD第40轮KITTI补充口径

宽松IoU0.5/0.25/0.25，AP_R40 Moderate；与上述官方EAA/DC不是同一个指标。metrics.json中的KITTI标量字段默认严格IoU，以下宽松结果从kitti.txt对应AP_R40段落读取。

| 类别 | 3D | BEV |
| --- | --- | --- |
| Car | 63.90 | 73.13 |
| Pedestrian | 65.80 | 66.97 |
| Cyclist | 85.85 | 85.85 |

## 当前进度

| 组别 | 状态 | GPU | 轮次 | batch | best轮 | best选模指标 |
| --- | --- | --- | --- | --- | --- | --- |
| ObjDec C+L+R | training | 3 | 53 | 1400/4196 | 50 | 78.38 |
| Concat C+L+R | complete | 2 | 80 | 4196/4196 | 75 | 81.46 |
| L4DR L+R | complete | 1 | 80 | 4196/4196 | 80 | 77.19 |
| ASF-style C+L+R | training | 0 | 41 | 3300/4196 | 40 | 75.71 |
| ObjDec L+R | training | 1 | 41 | 4100/4196 | 40 | 71.48 |
| VoD ObjDec | training | 2 | 43（日志） | 232/643（07:52） | 40 | 64.75 |

07:53 GPU2整卡27,664MiB，训练记录峰值allocated22.75GiB/reserved24.86GiB，PID325480，正常更新。最近一轮约605秒，验证通常4–7分钟；若速度保持，余下约7小时，约15:00前后结束，属于粗略估计。V2X ObjDec CLR正在第53轮，ASF-style及ObjDec-LR正在第41轮。各任务未在本轮更改。

## 来源

- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_050.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_050.json)；SHA256 `5761b241cfd9fdabb6334615cce6ca073cde30ea45093adbb7a71b5273a23416`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_050.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_050.json)；SHA256 `bb718d072304d66c7f2ee0fda9a95a6a3e1edfec929441c7d02596fd1a5f9951`。
- [analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_050.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_050.json)；SHA256 `ee01467daf09a9f5e1b43d2f8d578def55aa9ec759452f7eb4fb62279e52abf3`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_045.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_045.json)；SHA256 `31d1968e9252da5ed8b6e334fceaf57429e481bbfd5ef8ef214227224eb09279`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_030.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_030.json)；SHA256 `afb88697e07cf1ec6b9e75d7ba5299b4ddb7aa2e4e05e22e7a800c7bcf3fc1d4`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_030.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_030.json)；SHA256 `6a676bc8554394324716343d1b2a9937a061716fc4c7ae7fba6a47d75e0f915c`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_035.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_035.json)；SHA256 `e00987bf520a119828cfcfdfed2aa4b5664ddccdd43af814ab217251633bb12b`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_035.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_035.json)；SHA256 `6ed53d8f82034ac2d8280c6c06b53e340dc9b3adc45e80d1da3225dcc7ac4404`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_040.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_040.json)；SHA256 `c8031c54424d107e1f5b861fd2f1c9c7f0a201fcaf9c04becb7a804a2cdbb8cb`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_040.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_040.json)；SHA256 `8633dc202ce4760fac7d4bb2a19856a982ae6ecea8469f2b24b4afe35eb833cb`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_045.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_045.json)；SHA256 `9e5cffe74664b005a93b7053524e224f6b083bbfe2e132a9167fbf85d3660a0a`。
- [analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_040.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_040.json)；SHA256 `f5f8c9908f73de5b5d8ac1f97b3b3ad7635184d63bea2aa9c22b710b8fabe2b1`。
- [analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/val_epoch_040.json](../analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/val_epoch_040.json)；SHA256 `fdd4bba2e1bc410a17bbfe7f903cb33023a51e38ffbbf82555f7c90a45c3ccba`。
- [analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/val_epoch_040.json](../analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/val_epoch_040.json)；SHA256 `5b70750c02d0d74cdbbcd0cbda7840b7839d5620f49aebc9bcabdb55c2ceb0ef`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_005/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_005/metrics.json)；SHA256 `707a5a74a33f0fd8f61986474b2f72e97482f188e349ab58a0e83aaf18e81322`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_010/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_010/metrics.json)；SHA256 `2fa1d816ed1898fff34b6eafe1e2607c78806217a45b89612423584d98b56208`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_015/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_015/metrics.json)；SHA256 `96bad2c6a874f184f55499a933daed9ebee2ac3015454c85707a9124d4eefc77`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_020/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_020/metrics.json)；SHA256 `e5c12dbc386d3404479880b8cc9d200258c99f0caaf1a4d3bb85f05d725e98fd`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_025/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_025/metrics.json)；SHA256 `09f0aa83cf0faaee42e7f3c47b14277674dfa83ded10eea96fe966ba3bd81a9e`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_030/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_030/metrics.json)；SHA256 `7f787a9cf897c100ed7a360822a29eb0386f65515244b28ead69221980c8b1e0`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_035/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_035/metrics.json)；SHA256 `748242b05b438f4272a521adf9c2701f2931493c6ed47c8dabda080d590c2e6d`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_040/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_040/metrics.json)；SHA256 `989de85b799b6ec4c83c43831003ae82f3637a98ddd64b5a2c4df0d46bccc563`。
