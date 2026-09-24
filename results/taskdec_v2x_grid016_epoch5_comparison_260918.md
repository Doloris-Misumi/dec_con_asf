# ObjDec：0.16m实验进度与第5轮同轮次对照

采集时间：2026-09-18T21:35:46+08:00。本次只读取运行状态及已完成验证，不修改训练配置、进程或权重。工程目录仍使用TaskDec，文中方法名已定为ObjDec。

## 当前进度

| GPU | 实验 | 状态 | 已完成轮数 | 当前轮／总轮数 | batch进度 | 最新已完成验证 | 历史最佳val |
|---|---|---|---:|---|---|---|---|
| 1 | L4DR L+R / 0.16m | training | 76 | 77/80 | 700/4196 | epoch 75: 77.15 | epoch 70: 77.16 |
| 2 | Concat 0.16m | training | 19 | 20/80 | 900/4196 | epoch 15: 64.74 | epoch 15: 64.74 |
| 3 | ObjDec 2×2 / 0.16m | training | 9 | 10/80 | 2900/4196 | epoch 5: 44.22 | epoch 5: 44.22 |

上述三个训练的failure_count均为0，宿主机GPU利用率和PID确认仍在运行。GPU0为原常驻服务，GPU1另有原常驻服务；此前0.4m四组80轮均已完成。K-Radar v2十组合退化评测已完成，GPU2已接续0.16m Concat。

## 同第5轮：完整去重验证集

统一为V2X-Radar-V去重val 1,487帧，严格IoU=0.7/0.5/0.5（Vehicle/Pedestrian/Cyclist），Moderate，AP_R40。不是test，也不是宽松IoU。所有组训练集8,391帧，计划80轮、有效batch8、seed260916；第5轮均已完成5,245次优化器更新。

| 方法 | Vehicle | Pedestrian | Cyclist | 平均3D AP | 平均BEV AP |
|---|---:|---:|---:|---:|---:|
| Concat 0.4m | 29.52 | 20.95 | 49.25 | 33.24 | 51.20 |
| ASF-style patch 0.4m | 36.32 | 10.93 | 33.16 | 26.80 | 40.77 |
| ObjDec 4×4 / 0.4m | 42.34 | 12.88 | 42.11 | 32.44 | 44.58 |
| ObjDec 2×2 / 0.4m | 28.31 | 14.33 | 40.46 | 27.70 | 47.21 |
| L4DR L+R / 0.16m | 37.66 | 40.67 | 55.89 | 44.74 | 60.10 |
| Concat 0.16m | 53.48 | 39.63 | 51.56 | 48.23 | 62.93 |
| ObjDec 2×2 / 0.16m | 50.41 | 35.93 | 46.31 | 44.22 | 60.21 |

## 第5轮的变化量

| 比较（前者−后者） | Vehicle | Pedestrian | Cyclist | 平均3D | 平均BEV |
|---|---:|---:|---:|---:|---:|
| ObjDec 2×2 / 0.16m − ObjDec 2×2 / 0.4m | +22.11 | +21.60 | +5.85 | +16.52 | +13.00 |
| ObjDec 2×2 / 0.16m − L4DR L+R / 0.16m | +12.76 | -4.74 | -9.58 | -0.52 | +0.10 |
| ObjDec 2×2 / 0.16m − Concat 0.16m | -3.07 | -3.70 | -5.25 | -4.01 | -2.72 |
| Concat 0.16m − Concat 0.4m | +23.96 | +18.68 | +2.31 | +14.99 | +11.72 |
| Concat 0.16m − L4DR L+R / 0.16m | +15.83 | -1.04 | -4.33 | +3.49 | +2.82 |

## 0.16m已完成的早期验证趋势

| 轮次 | Concat平均3D | ObjDec平均3D | L4DR平均3D | Concat−L4DR | ObjDec−L4DR |
|---|---:|---:|---:|---:|---:|
| 1 | 7.07 | 5.89 | 17.74 | -10.67 | -11.85 |
| 5 | 48.23 | 44.22 | 44.74 | +3.49 | -0.52 |
| 10 | 59.07 | 待完成 | 56.72 | +2.35 | — |
| 15 | 64.74 | 待完成 | 60.40 | +4.34 | — |

## 最新L4DR验证及旧方法同轮对照

| 方法 | 轮次 | Vehicle | Pedestrian | Cyclist | 平均3D |
|---|---:|---:|---:|---:|---:|
| L4DR L+R / 0.16m | 75 | 81.76 | 71.13 | 78.56 | 77.15 |
| Concat 0.4m | 75 | 81.53 | 62.03 | 79.36 | 74.31 |
| ASF-style patch 0.4m | 75 | 80.39 | 58.91 | 78.97 | 72.76 |
| ObjDec 4×4 / 0.4m | 75 | 79.27 | 55.88 | 77.90 | 71.01 |
| ObjDec 2×2 / 0.4m | 75 | 81.13 | 62.07 | 78.86 | 74.02 |

## 解读与比较边界

1. 第5轮ObjDec由27.70提升至44.22，平均3D增加16.52点；行人由14.33提升至35.93，增加21.60点。新旧2×2配置除创建时间、内存上限外仅改变voxel_size，尚是单seed早期观察。
2. 同轮与L4DR的差距由17.04点缩小到0.52点；当前ObjDec的Vehicle高12.76点，但Pedestrian/Cyclist分别低4.74/9.58点。平均值接近不代表每类追平。
3. 细网格同样显著改善Concat：第5轮由33.24升至48.23，增加14.99点。0.16m下ObjDec仍落后Concat4.01点；0.4m下两者差5.54点，相对差距只收窄1.53点。因此当前证据首先支持细网格改善早期学习表现，尚不支持ObjDec融合优于同配置Concat。
4. Concat在第10/15轮平均3D为59.07/64.74，分别高于同轮L4DR2.35/4.34点。ObjDec尚未完成第10轮验证，不能将其第5轮结果与其它方法第15轮直接排名。
5. L4DR为L+R原生架构、约62.07M参数；新ObjDec/Concat为C+L+R、约33.65M/33.14M，且相机使用ImageNet预训练。虽然现在体素网格都为0.16m，模态、网络和初始化仍不同，不是同FLOPs消融。ASF-style patch是本地适配且没有SCL。
6. 0.4m到0.16m同时细化输入/BEV与检测网格；固定2×2 patch的物理范围从0.8m变为0.32m。不能将提升单独归因于gate、某一分支或某一种分辨率变化。
7. 同轮次不是同耗时；第五轮不是最终模型。继续按既定80轮、每5轮验证和val选模规则运行，最终看完整预算及选模后的test。

## 已记录的前5轮纯训练耗时

| 方法 | 前5轮训练GPU小时（不含验证） |
|---|---:|
| Concat 0.4m | 0.88 |
| ASF-style patch 0.4m | 1.06 |
| ObjDec 4×4 / 0.4m | 1.27 |
| ObjDec 2×2 / 0.4m | 1.53 |
| L4DR L+R / 0.16m | 2.74 |
| Concat 0.16m | 1.84 |
| ObjDec 2×2 / 0.16m | 6.62 |

时间来自各进程epochs.jsonl，运行时并发负载不同，不能当作隔离条件下的严格测速。

## 原始结果入口

- [Concat 0.4m 第5轮](/home/hongsheng/dec_con_asf/analysis_exports/v2x_taskdec_260916/controlled_80ep/concat/val_epoch_005.json)
- [ASF-style patch 0.4m 第5轮](/home/hongsheng/dec_con_asf/analysis_exports/v2x_taskdec_260916/controlled_80ep/patch/val_epoch_005.json)
- [ObjDec 4×4 / 0.4m 第5轮](/home/hongsheng/dec_con_asf/analysis_exports/v2x_taskdec_260916/controlled_80ep/taskdec/val_epoch_005.json)
- [ObjDec 2×2 / 0.4m 第5轮](/home/hongsheng/dec_con_asf/analysis_exports/v2x_taskdec_260916/taskdec_patch2_80ep/taskdec/val_epoch_005.json)
- [L4DR L+R / 0.16m 第5轮](/home/hongsheng/dec_con_asf/analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_005.json)
- [Concat 0.16m 第5轮](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_005.json)
- [ObjDec 2×2 / 0.16m 第5轮](/home/hongsheng/dec_con_asf/analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_005.json)
