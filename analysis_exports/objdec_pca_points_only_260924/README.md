# ObjDec：架构图用纯散点PCA素材

沿用正常天气的局部前景patch PCA坐标与原有固定抽样，未重新拟合或移动点。
点面积由18增至54 pt²（3倍），不透明度由0.72增至0.95。
Camera蓝圆点、LiDAR绿三角、4D Radar紫方块；无坐标轴、文字、边框或图例。
每张提供600 dpi透明PNG及矢量SVG/PDF；PPT优先使用SVG。

- Shared：`objdec_shared_pca_normal_points_only.*`
- Specific：`objdec_specific_pca_normal_points_only.*`

两分支沿用各自的PCA基及显示范围，不据跨图视觉距离计算对齐幅度。
重跑：用rl_3dod环境Python执行本目录export_points_only.py，仅CPU绘图。
