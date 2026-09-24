# ObjDec训练进度与同轮比较


核查时间：2026-09-20T19:52:10+08:00。只读检查训练和评测记录；没有改变任何运行任务。


当前组均为V2X-Radar-V、0.16m网格、80轮预算。结果采用去重val 1,487帧、Moderate AP_R40、严格IoU=0.7/0.5/0.5；不与最终test混排。


## 当前进度

| GPU | 方法 | 状态 | 最新验证轮 | 最新val Mean 3D | 当前best val | failure_count |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | ObjDec C+L+R | 第44/80轮，2400/4196 batch | 40 | 76.55 | 76.55 (ep40) | 0 |
| 已释放 | Concat C+L+R | 80轮及最终复评完成 | 80 | 81.31 | 81.46 (ep75) | 0 |
| 0 | ASF-style C+L+R | 第30/80轮，2700/4196 batch | 25 | 67.39 | 67.39 (ep25) | 0 |
| 1 | ObjDec L+R | 第30/80轮，3300/4196 batch | 25 | 63.01 | 64.21 (ep20) | 0 |
| 已释放 | L4DR L+R | 80轮及最终复评完成 | 80 | 77.19 | 77.19 (ep80) | 0 |


GPU实测（约19:50）：GPU0利用率84%、显存29,867MiB；GPU1为100%、33,331MiB；GPU3为95%、30,700MiB。GPU0/1各包含约8.5GiB原驻留进程。GPU2无计算进程，显存仅26MiB。三组日志新鲜且未发现Traceback/OOM等错误记录。


## 第40轮同轮比较

| 方法 | Vehicle | Pedestrian | Cyclist | Mean 3D | Mean BEV |
| --- | --- | --- | --- | --- | --- |
| ObjDec C+L+R | 81.24 | 68.50 | 79.92 | 76.55 | 82.63 |
| Concat C+L+R | 76.85 | 68.75 | 78.41 | 74.67 | 82.00 |
| L4DR L+R | 79.39 | 66.11 | 74.49 | 73.33 | 79.20 |


ObjDec相对同轮Concat：Mean 3D +1.89、Mean BEV +0.63；车辆+4.40、行人−0.24、骑行者+1.51。相对同轮L4DR：Mean 3D +3.22，三类均更高；两者输入模态和网络结构不同。


## 最近验证趋势

| 轮次 | ObjDec CLR | Concat CLR | L4DR LR | ObjDec−Concat | ObjDec−L4DR |
| --- | --- | --- | --- | --- | --- |
| 20 | 67.37 | 68.95 | 63.09 | -1.58 | +4.28 |
| 25 | 66.80 | 68.04 | 62.97 | -1.24 | +3.83 |
| 30 | 69.92 | 69.30 | 68.42 | +0.61 | +1.50 |
| 35 | 73.80 | 74.27 | 71.09 | -0.47 | +2.71 |
| 40 | 76.55 | 74.67 | 73.33 | +1.89 | +3.22 |


ObjDec从第30轮69.92到第35轮73.80，再到第40轮76.55，连续两个验证节点提高；对Concat的领先仍有波动，并非每个节点单调扩大。第40轮是当前验证best，尚不能据此保证80轮终点领先。


## 新增对照：第25轮

| 方法 | Vehicle | Pedestrian | Cyclist | Mean 3D | Mean BEV |
| --- | --- | --- | --- | --- | --- |
| Concat C+L+R | 70.63 | 61.58 | 71.92 | 68.04 | 75.75 |
| ASF-style C+L+R | 71.35 | 59.39 | 71.44 | 67.39 | 75.55 |
| ObjDec C+L+R | 68.42 | 59.49 | 72.49 | 66.80 | 76.83 |
| ObjDec L+R | 66.47 | 54.27 | 68.29 | 63.01 | 72.46 |
| L4DR L+R | 64.63 | 57.22 | 67.06 | 62.97 | 73.87 |


第25轮ObjDec CLR相对ASF-style平均3D低0.59点、BEV高1.29点。ObjDec-LR与同轮L4DR平均3D接近（+0.04点），但行人低2.94点、平均BEV低1.41点；其当前best仍是第20轮64.21，第25轮回落至63.01。第30轮尚在训练，待验证后才能更新这组对比。


## 下次结果估计

- ObjDec C+L+R：最近每轮约79.2分钟；第45轮验证完成预计约131分钟后（09-20 22:02）。

- ASF-style C+L+R：最近每轮约61.5分钟；第30轮验证完成预计约37分钟后（09-20 20:28）。

- ObjDec L+R：最近每轮约61.4分钟；第30轮验证完成预计约30分钟后（09-20 20:22）。


估计依据最近三轮耗时与最近一次完整验证耗时，负载变化会影响实际完成时间，不作为固定承诺。


## 已完成组


Concat已完成80轮，按val选中epoch75，best val Mean 3D 81.46，best test Mean 3D 81.90。L4DR已完成80轮，best为epoch80，best val 77.19，best test 78.24。此处单独列最终test，不与上面的训练期val直接比较。


## 验证结果来源

- [taskdec/val_epoch_040.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_040.json)；SHA256 `c8031c54424d107e1f5b861fd2f1c9c7f0a201fcaf9c04becb7a804a2cdbb8cb`。

- [concat/val_epoch_080.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_080.json)；SHA256 `ac3bc3544b64c71e1dc37290a64d4d2f9dcc3283f776008c78659176dee92ee1`。

- [patch/val_epoch_025.json](../analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch/val_epoch_025.json)；SHA256 `a4fa8a8b41661d978b74a189659777b647b1c66231463fecf80eef058e37a623`。

- [taskdec/val_epoch_025.json](../analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec/val_epoch_025.json)；SHA256 `f866e90c371198c4cd0637e63733ae173c5f363ec4b1214c87e3057176249a63`。

- [l4dr/val_epoch_080.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_080.json)；SHA256 `5b09f09ba0d3b986d5f985cfeff41fa792f770bd031d865d7eabebf2fed33dc4`。

- [concat/val_epoch_040.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_040.json)；SHA256 `8633dc202ce4760fac7d4bb2a19856a982ae6ecea8469f2b24b4afe35eb833cb`。

- [l4dr/val_epoch_040.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_040.json)；SHA256 `f5f8c9908f73de5b5d8ac1f97b3b3ad7635184d63bea2aa9c22b710b8fabe2b1`。

- [taskdec/val_epoch_020.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_020.json)；SHA256 `d14ab368a526743681aeeb992f2bd7b63c8dfca6764dd0ea387d272b97b72beb`。

- [concat/val_epoch_020.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_020.json)；SHA256 `dd6b8a4930ac65222c6db56cc3821644d0becd2fe9a32e8104df6d6365c94897`。

- [l4dr/val_epoch_020.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_020.json)；SHA256 `08156d3d5e5fc0975a769903f3d59051ca1c14ff07ec6da7ab9a00a2b55b3bef`。

- [taskdec/val_epoch_025.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_025.json)；SHA256 `9a3788f8cac3361029535c8b54d0681ca81acb669e3702194d040e0bd5f330e0`。

- [concat/val_epoch_025.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_025.json)；SHA256 `39bd52e4150b0325212a7fe8d75a568d82cfd681b50b774f9094529424506511`。

- [l4dr/val_epoch_025.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_025.json)；SHA256 `5aa098d0e9def454b09f96ec4d99e85026718f0ab23039bff4de807519b32bfe`。

- [taskdec/val_epoch_030.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_030.json)；SHA256 `afb88697e07cf1ec6b9e75d7ba5299b4ddb7aa2e4e05e22e7a800c7bcf3fc1d4`。

- [concat/val_epoch_030.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_030.json)；SHA256 `6a676bc8554394324716343d1b2a9937a061716fc4c7ae7fba6a47d75e0f915c`。

- [l4dr/val_epoch_030.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_030.json)；SHA256 `a1ebcfec0ad2f665f4e800f8842472744827f8db8cfd7808caf5063ce63a9ecd`。

- [taskdec/val_epoch_035.json](../analysis_exports/v2x_grid016_260918/matched_80ep/taskdec/val_epoch_035.json)；SHA256 `e00987bf520a119828cfcfdfed2aa4b5664ddccdd43af814ab217251633bb12b`。

- [concat/val_epoch_035.json](../analysis_exports/v2x_grid016_260918/matched_80ep/concat/val_epoch_035.json)；SHA256 `6ed53d8f82034ac2d8280c6c06b53e340dc9b3adc45e80d1da3225dcc7ac4404`。

- [l4dr/val_epoch_035.json](../analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr/val_epoch_035.json)；SHA256 `6ac75ed778faccd6e6e18e1a720080d05be6d3b1dd04fa4c43692a81d3359c71`。
