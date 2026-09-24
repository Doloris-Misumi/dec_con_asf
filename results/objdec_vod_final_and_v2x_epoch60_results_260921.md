# VoD最终结果与V2X最新第60轮比较

核查时间：2026-09-21T22:12:15+08:00。本轮只收集结果、保存汇总，没有新开或修改训练。

## 结论

VoD的2×2 patch＋局部编码＋token规范化实验已完成80轮。按官方EAA在每5轮评估的候选中选出第75轮：71.23 EAA /84.69 DC，优于旧warm版70.18/83.79；相对本地L4DR EAA+0.23、DC−0.15，尚未超过论文L4DR72.70/87.47。

V2X三模态ObjDec正在第63轮，最新完整验证为第60轮；第55/60轮3D均值80.442806/80.436877（两位小数均80.44），基本持平。第60轮对同轮Concat为+0.18 3D /+0.42 BEV，当前没有持续拉大优势。

## VoD官方EAA/DC

1,296帧原生验证集；官方区域/类别过滤，EAA与DC均对应同一权重。所有方法为L+R。

| 方法 | EAA mAP | DC mAP |
| --- | --- | --- |
| PP-Concat，历史80轮 | 69.88 | 83.80 |
| 旧ObjDec warm，第79轮 | 70.18 | 83.79 |
| 新ObjDec，第75轮（按EAA选） | 71.23 | 84.69 |
| 新ObjDec，第80轮（末轮） | 70.83 | 84.66 |
| 本地L4DR，第99轮 | 71.00 | 84.84 |
| L4DR论文 | 72.70 | 87.47 |

新ObjDec第75轮相对历史Concat：+1.35/+0.89；相对旧warm版：+1.05/+0.90；相对本地L4DR：+0.23/−0.15；相对论文L4DR：−1.47/−2.78。本地L4DR第99轮为历史已评估末期候选中较优，并非宣称扫描100个权重后的全局最优。

### 逐类改善

| 区域 | 版本 | Car | Pedestrian | Cyclist |
| --- | --- | --- | --- | --- |
| EAA | 旧warm，第79轮 | 67.50 | 63.66 | 79.38 |
| EAA | 新版本，第75轮 | 68.72 | 65.59 | 79.38 |
| EAA | 变化 | +1.22 | +1.93 | +0.00 |
| DC | 旧warm，第79轮 | 90.59 | 71.02 | 89.76 |
| DC | 新版本，第75轮 | 90.74 | 73.23 | 90.09 |
| DC | 变化 | +0.15 | +2.21 | +0.33 |

EAA主要改善车辆和行人，骑行者与旧版相同；DC主要改善行人。多个改动联合、BatchNorm微批次也从16变为8，且旧版本为warm-start，不能把所有变化归因于patch大小单一因素。此次从头训练、没有Concat预训练，后续同设置Concat才是局部编码条件下的直接架构对照。

### 后半程趋势

| 轮次 | EAA | DC |
| --- | --- | --- |
| 40 | 64.75 | 78.83 |
| 45 | 67.21 | 82.88 |
| 50 | 66.07 | 79.6 |
| 55 | 68.01 | 84.33 |
| 60 | 70.5 | 84.43 |
| 65 | 70.76 | 84.19 |
| 70 | 69.34 | 84.51 |
| 75 | 71.23 | 84.69 |
| 80 | 70.83 | 84.66 |

### 同一第75轮的KITTI 3D/BEV补充指标

宽松IoU0.5/0.25/0.25，AP_R40；与上面的官方EAA/DC不同。从kitti.txt显式选择宽松IoU段；metrics.json内KITTI标量默认为严格IoU，不能直接混用。

| 指标 | 类别 | Easy | Moderate | Hard |
| --- | --- | --- | --- | --- |
| 3d | Car | 83.23 | 74.84 | 67.69 |
| 3d | Pedestrian | 73.80 | 72.31 | 66.00 |
| 3d | Cyclist | 93.26 | 88.77 | 83.00 |
| bev | Car | 89.14 | 79.96 | 72.83 |
| bev | Pedestrian | 74.00 | 72.84 | 67.62 |
| bev | Cyclist | 93.29 | 88.83 | 83.21 |
| 3d | Mean | 83.43 | 78.64 | 72.23 |
| bev | Mean | 85.47 | 80.55 | 74.56 |

第75轮KITTI Moderate均值3D/BEV为78.64/80.55。3D对历史Concat77.05为+1.59，对旧mild从头版本最佳76.21为+2.43，对本地L4DR78.16为+0.48；仍低于论文L4DR79.77约1.13。不同版本的选模和训练设置需披露。

### 完成状态

训练于2026-09-21 14:37结束，总训练循环含验证约14小时32分。累计训练墙钟13.44小时、验证1.10小时。GPU2当前空闲（26MiB）；最优与末轮权重均存在。每5轮验证，共16个候选，未声称扫描每一轮。

- [最优权重，第75轮](../vod_taskdec_native/L4DR_taskdec/output/VoD_models/ObjDec_PP_Patch2_Local_Mild_260920/objdec_p2_local_mild_b8a2_fp32_ep80_260920_gpu2/ckpt/best_eaa.pth)
- [末轮权重，第80轮](../vod_taskdec_native/L4DR_taskdec/output/VoD_models/ObjDec_PP_Patch2_Local_Mild_260920/objdec_p2_local_mild_b8a2_fp32_ep80_260920_gpu2/ckpt/checkpoint_epoch_80.pth)

## V2X-Radar-V最新完整验证：第60轮

0.16m；同一去重val1,487帧，AP_R40 Moderate，严格IoU0.7/0.5/0.5。最新训练轮63没有独立验证结果，不能称作“第63轮AP”。

### 3D

| 方法 | Vehicle | Pedestrian | Cyclist | Mean |
| --- | --- | --- | --- | --- |
| ObjDec C+L+R | 83.74 | 73.70 | 83.88 | 80.44 |
| Concat C+L+R | 83.96 | 74.19 | 82.63 | 80.26 |
| L4DR L+R | 82.84 | 70.35 | 77.48 | 76.89 |
| ObjDec−Concat C+L+R | -0.22 | -0.49 | +1.25 | +0.18 |
| ObjDec−L4DR L+R | +0.90 | +3.35 | +6.39 | +3.55 |

### BEV

| 方法 | Vehicle | Pedestrian | Cyclist | Mean |
| --- | --- | --- | --- | --- |
| ObjDec C+L+R | 90.84 | 78.46 | 85.93 | 85.08 |
| Concat C+L+R | 90.63 | 78.09 | 85.25 | 84.66 |
| L4DR L+R | 90.05 | 73.51 | 80.33 | 81.29 |
| ObjDec−Concat C+L+R | +0.21 | +0.37 | +0.68 | +0.42 |
| ObjDec−L4DR L+R | +0.79 | +4.96 | +5.60 | +3.78 |

### 同轮趋势

| 轮次 | ObjDec3D | Concat3D | 差值 | ObjDecBEV | ConcatBEV | 差值 |
| --- | --- | --- | --- | --- | --- | --- |
| 45 | 77.48 | 76.22 | +1.26 | 83.58 | 82.93 | +0.65 |
| 50 | 78.38 | 77.90 | +0.48 | 84.11 | 83.69 | +0.42 |
| 55 | 80.44 | 79.09 | +1.36 | 85.12 | 84.46 | +0.66 |
| 60 | 80.44 | 80.26 | +0.18 | 85.08 | 84.66 | +0.42 |

第50→55轮ObjDec均值3D/BEV增加2.06/1.01；第55→60轮3D仅−0.005929、BEV−0.038027。车辆3D−0.18、行人−0.26、骑行者+0.42，呈局部涨跌而均值持平。

第60轮对Concat：车辆3D低0.22、行人低0.49、骑行者高1.25，因此主要3D优势来自骑行者；BEV三类分别高0.21/0.37/0.68。第55轮3D领先1.36，至第60轮缩到0.18，Concat同期追近。

ObjDec当前按3D选的第55轮80.44/85.12，距离Concat按3D选的第75轮81.46/85.75还差1.02/0.64。差距比第50轮时缩小，但轮次不同，不构成同轮胜负；还需等待65–80轮。对第60轮本地L4DR领先3.55/3.78，但模态C+L+R与L+R不同。

### ASF-style与双模态组：最新共同第50轮

| 方法 | 3D Mean | BEV Mean |
| --- | --- | --- |
| ObjDec C+L+R | 78.38 | 84.11 |
| Concat C+L+R | 77.90 | 83.69 |
| L4DR L+R | 75.17 | 80.52 |
| ASF-style C+L+R | 77.17 | 83.12 |
| ObjDec L+R | 75.54 | 81.08 |

同模态下，ObjDec CLR比ASF-style CLR高1.22/0.99；ObjDec LR比L4DR LR高0.37/0.56。双模态第50轮已小幅反超本地L4DR，是积极变化，但不能用CLR第60轮与ASF第50轮当同轮比较。

### 运行快照

| 组别 | 状态 | GPU | 当前轮 | batch | best轮 | best 3D |
| --- | --- | --- | --- | --- | --- | --- |
| ObjDec C+L+R | training | 3 | 63 | 3200/4196 | 55 | 80.44 |
| Concat C+L+R | complete | 2 | 80 | 4196/4196 | 75 | 81.46 |
| L4DR L+R | complete | 1 | 80 | 4196/4196 | 80 | 77.19 |
| ASF-style C+L+R | training | 0 | 55 | 1100/4196 | 50 | 77.17 |
| ObjDec L+R | training | 1 | 55 | 2100/4196 | 50 | 75.54 |

ASF-style与ObjDec-LR都在第55轮训练；最新验证仍是第50轮。GPU0、1上另外两个既有python进程仍在运行，本轮没有更改。

## 既有对照来源

- [历史VoD表](paper_vod_main_table_draft_260909.md)
- [本地L4DR复现](l4dr_vod_local_repro_results_260910.md)
- [新VoD启动设置](objdec_vod_patch2_local_launch_260921.md)

## 本轮结果来源（含SHA256）

- [analysis_exports/objdec_vod_patch2_local_260920/best_metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/best_metrics.json)；`47e8dd9cbd922938dce350c6253bf8b4b8f93db1986629fb4e53dc492666fbcc`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_080/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_080/metrics.json)；`3bc828c2b7a69570c370b3796fc5ba57a91a7083e497224205a92f7f3094ea74`。
- [analysis_exports/objdec_vod_patch2_local_260920/status.json](../analysis_exports/objdec_vod_patch2_local_260920/status.json)；`641c0693c2adbde5f5abd1fd12f8ae52dd7029d8df714353732acf37ddedcd24`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_000/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_000/metrics.json)；`d1d042ac60a96c3506afc92b75a673ce912388a9f0a2329d43c160e6b1d54e9d`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_005/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_005/metrics.json)；`707a5a74a33f0fd8f61986474b2f72e97482f188e349ab58a0e83aaf18e81322`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_010/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_010/metrics.json)；`2fa1d816ed1898fff34b6eafe1e2607c78806217a45b89612423584d98b56208`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_015/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_015/metrics.json)；`96bad2c6a874f184f55499a933daed9ebee2ac3015454c85707a9124d4eefc77`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_020/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_020/metrics.json)；`e5c12dbc386d3404479880b8cc9d200258c99f0caaf1a4d3bb85f05d725e98fd`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_025/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_025/metrics.json)；`09f0aa83cf0faaee42e7f3c47b14277674dfa83ded10eea96fe966ba3bd81a9e`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_030/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_030/metrics.json)；`7f787a9cf897c100ed7a360822a29eb0386f65515244b28ead69221980c8b1e0`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_035/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_035/metrics.json)；`748242b05b438f4272a521adf9c2701f2931493c6ed47c8dabda080d590c2e6d`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_040/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_040/metrics.json)；`989de85b799b6ec4c83c43831003ae82f3637a98ddd64b5a2c4df0d46bccc563`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_045/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_045/metrics.json)；`9a625e4c211578e98d70b72d6ada8ce5ab4c5cc6c3624763a7ed1f32393ca80f`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_050/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_050/metrics.json)；`43ba9cd568803aebb090790dc7993ed00d4ce7b0bef74f53178a56b52ed03554`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_055/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_055/metrics.json)；`8ee2a420c4151eebe0c9a3b974bc5bb53c4b7cf66095a327f27cc1793ea10b49`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_060/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_060/metrics.json)；`a7a3d285944ed1b1df8386180c376f3f2aed8781407177bffe33ad31256c9191`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_065/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_065/metrics.json)；`5c3a71aa4ec4a5e0543396a64e5a8a2ae2a47bd25e33983cb7020df656871195`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_070/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_070/metrics.json)；`482ae9094188fff47afb9faa9c343ea2b9b55897fe0e2755fcb5d3dbda363624`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_075/metrics.json](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_075/metrics.json)；`47e8dd9cbd922938dce350c6253bf8b4b8f93db1986629fb4e53dc492666fbcc`。
- [analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_075/kitti.txt](../analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_075/kitti.txt)；`3bd599f4d0a799702951296111a528a55b50ec894286da9b1f350936b3aec5f1`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_060.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_060.json)；`c3e85ebd7d04cbad418689e24ea9bdb241ef2c171dc9f21463f8f7aedd58b25c`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_060.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_060.json)；`208c5f1d448faa05fdf940e7532c5998bd17f7d9bf2916b480079cdcf52824ba`。
- [analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_060.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_060.json)；`275d3ca69eaa2e8b598d4d1c03e8399fd51fcd059478362b6c87bd487030ad48`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_045.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_045.json)；`31d1968e9252da5ed8b6e334fceaf57429e481bbfd5ef8ef214227224eb09279`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_045.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_045.json)；`9e5cffe74664b005a93b7053524e224f6b083bbfe2e132a9167fbf85d3660a0a`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_050.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_050.json)；`5761b241cfd9fdabb6334615cce6ca073cde30ea45093adbb7a71b5273a23416`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_050.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_050.json)；`bb718d072304d66c7f2ee0fda9a95a6a3e1edfec929441c7d02596fd1a5f9951`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_055.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_055.json)；`ed1d8e10e6ae0ba136fa60ff5a4f2b56af22a7cf7b189ce03b6cd1d36ef0ab29`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_055.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_055.json)；`ac3e77374f9b91305383c45c106fa88c7c4f5c0984afaa36e23488c8ed3a81f9`。
- [analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_050.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_050.json)；`ee01467daf09a9f5e1b43d2f8d578def55aa9ec759452f7eb4fb62279e52abf3`。
- [analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/val_epoch_050.json](../analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/val_epoch_050.json)；`5d3d25e5572f5063fb0fb66a38d53bf2cefce8f27b18e1e5ecf690bca5f42c47`。
- [analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/val_epoch_050.json](../analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/val_epoch_050.json)；`029383d22805e882ae00835a1ceaf1101022699af94c7c542448732b73fb14ee`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/status.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/status.json)；`e28e94ad1b6b3d162f02c760225f86f761b7fc2e935de6b601fa5329d4b2fbc4`。
- [analysis_exports/v2x_grid016_260918/matched_80ep/concat/status.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/status.json)；`cebdb6218f381408fed8615aac5b70cda1f303ec34e124f7aec579966c1dbf04`。
- [analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/status.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/status.json)；`90b44bae0e2b6bf066e846fa33b5ec99c205c405164230ab148165ac1b932147`。
- [analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/status.json](../analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/status.json)；`81bc81f9726cfd24c2723ec7102d5c0e94b92f9a85baa17dc892805f6ee8a37d`。
- [analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/status.json](../analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/status.json)；`40df2b4efc40c1e46101fa6e9638ba016bcd1dec5de7777c9493947ce1ddb2a6`。
