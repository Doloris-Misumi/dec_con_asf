# VoD ObjDec：训练集适配锚框对照启动记录

2026-09-21 22:48:26（北京时间）启动。用户授权使用GPU2，训练PID **450891**，独立后台会话。

## 本轮比较什么

以已完成的ObjDec 2×2 patch＋局部编码版本为基准，唯一配置变化为三类锚框的长宽高与底部高度。重新从头训练80轮，验证这些数据集先验是否有帮助；不加载旧权重。参照原版最佳epoch75 EAA/DC=71.23/84.69，同时保留新版本所有周期验证，后续可比较同轮次及同选模规则结果。

| 类别 | 原长/宽/高(m) | 新长/宽/高(m) | 原底部z(m) | 新底部z(m) | 训练ROI内框数 |
|---|---|---|---:|---:|---:|
| Car | 3.90 /1.60 /1.56 | 4.19 /1.81 /1.52 | −1.78 | −1.65 | 15,264 |
| Pedestrian | 0.80 /0.60 /1.73 | 0.65 /0.63 /1.69 | −0.60 | −1.62 | 15,441 |
| Cyclist | 1.76 /0.60 /1.73 | 1.94 /0.78 /1.76 | −0.60 | −1.68 | 6,450 |

尺寸与高度同时属于本轮“锚框先验”这一组变化；不能将结果进一步归因为只有长宽、或只有高度的独立效果。

## 先验如何得到

从全部5,139个训练帧的原始标注计算，不使用验证集拟合：按原 `__getitem__` 的float32相机框＋逐帧标定转换到LiDAR坐标，去除DontCare，选择三类目标，再调用原生训练范围过滤，取长宽高及底部z的逐维中位数，四舍五入到0.01米。

已核对本地实际实现：范围过滤默认为**框中心在三维ROI内**（`USE_CENTER_TO_FILTER=True`），不走角点过滤；FOV只过滤点云，不另外过滤GT框。因此此前“还需核对是否角点过滤”的不确定性已解除。原生训练中的DB采样、翻转、旋转和缩放仍保留；先验统计使用增强前原始标签，不按一次随机增强结果拟合。

来源校验和、标定集合哈希、分位数和六处配置差异保存在[anchor_statistics.json](../analysis_exports/objdec_vod_adapted_anchors_260921/anchor_statistics.json)。准备脚本断言除三类的 `anchor_sizes`、`anchor_bottom_heights` 外，配置与上一版完全一致。

## 训练和评测

| 项目 | 设置 |
|---|---|
| 设备 | 物理GPU2，RTX A6000 48GB，UUID GPU-a669257e-8165-eea0-ffa3-c7016159e401 |
| 数据 | VoD 5,139 train /1,296 val，L+R，单帧LiDAR＋5帧Radar |
| 初始化/训练 | 从头80轮，seed666，FP32，Adam OneCycle，峰值LR0.003 |
| Batch | 微批次8×累积2，有效batch16，322次更新/轮；末组按实际样本数归一化 |
| 架构 | 原0.16m网格、320×320，patch2/query4，各模态两层3×3局部卷积、token LayerNorm |
| 损失及后处理 | 原mild损失；score=0.1，NMS=0.01 |
| 检测头 | 锚框数量、旋转、匹配阈值、head通道及框编码器保持原设置 |
| 参数量 | 18,605,583，与原版相同 |
| 验证 | 每5轮完整验证；官方EAA/DC及KITTI 3D/BEV分别记录；推理前移除GT |
| 选模 | 官方VoD EAA mAP严格提高才更新best，同权重记录DC |
| 保存 | 每5轮权重，最多16个，另保留best及必要恢复点；预计约4 GiB，无稠密特征导出 |

训练、梯度累积、学习率、验证和存储复用上一版已完成80轮的入口逻辑。本轮入口仅重定向新配置与输出目录；启动前对上次运行记录中的训练/模型/数据源文件校验，全部一致，未修改共享源码。

## 启动检查

- GPU2启动前空闲，约26 MiB占用。
- 3次真实训练数据优化更新通过，loss/梯度有限；这部分临时更新已丢弃，正式训练重置随机种子、重新初始化。
- 烟雾检查中的三类正样本锚框累计Car3,039、Pedestrian1,356、Cyclist1,483；每类生成51,200个锚框，实际尺寸和底部高度与新配置一致。
- 检查了适配锚框的残差编码/解码，测试框最大往返误差为0；无GT推理及框格式转换通过。
- 8帧功能预检跑通官方EAA/DC及KITTI 3D/BEV；epoch000为未训练模型检查，不计入性能或选模。
- 预检峰值allocated20.61 GiB/reserved22.18 GiB。正式首个更新22:48:43完成，loss2.8422、均值2.8683、LR0.0003；随后确认GPU2训练进程存活，显存占用约24.4 GiB。

`status.json`按整轮及验证阶段更新，因此第一轮进行中仍可能显示starting；逐步进度以训练日志为准。

## 查看与文件

```bash
tail -n 30 -F /home/hongsheng/dec_con_asf/vod_taskdec_native/logs/objdec_vod_adapted_anchors_gpu2_260921.log
```

- [启动清单](../analysis_exports/objdec_vod_adapted_anchors_260921/launch.json)
- [状态](../analysis_exports/objdec_vod_adapted_anchors_260921/status.json)
- [配置](../vod_taskdec_native/L4DR_taskdec/tools/cfgs/VoD_models/ObjDec_PP_Patch2_Local_Anchors_260921.yaml)
- [训练入口](../scripts/run_objdec_vod_adapted_anchors_260921.py)
- [锚框检查](../analysis_exports/objdec_vod_adapted_anchors_260921/anchor_smoke_checks.json)
- [评测目录](../analysis_exports/objdec_vod_adapted_anchors_260921/validation/)
- 权重目录：`vod_taskdec_native/L4DR_taskdec/output/VoD_models/ObjDec_PP_Patch2_Local_Anchors_260921/objdec_p2_local_anchors_b8a2_fp32_ep80_260921_gpu2/ckpt/`。

是否有提升需要正式验证；这次启动检查只证明训练链路可运行。
