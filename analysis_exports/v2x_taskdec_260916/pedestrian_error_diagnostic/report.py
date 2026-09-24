"""Small report/figure from completed diagnostic measurements."""
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
d=json.loads((OUT/'analysis.json').read_text())
assert d['status']=='complete'
g=d['geometry_common_gt']['0.1'];o=d['oracle_common_gt_score_01']
rows=list(csv.DictReader((OUT/'paired_errors.csv').open()))
assert len(rows)==d['geometry_matching']['0.1']['common_matches']==892
labels={'taskdec':'TaskDec ep50','concat':'Concat ep75'}
colors={'taskdec':'#d66b2f','concat':'#3478b8'}
fig,axes=plt.subplots(1,3,figsize=(14,4.4),gridspec_kw={'width_ratios':[1,1.2,1.1]})
for n in labels:
    x=np.sort([float(r[n+'_xy_m']) for r in rows])
    axes[0].plot(x,np.arange(1,len(x)+1)/len(x),label=labels[n],color=colors[n],lw=2)
axes[0].set(xlim=(0,.6),ylim=(0,1),xlabel='XY center error (m)',ylabel='Cumulative fraction',
            title='Center error: same 892 GT matches')
axes[0].grid(alpha=.2);axes[0].legend(fontsize=8)
axes[0].text(.98,.3,'Curve continues beyond 0.6 m',transform=axes[0].transAxes,ha='right',fontsize=8)
modes=['original','xy','length_width','yaw','z_height']
xx=np.arange(len(modes))
for j,n in enumerate(labels):
    vals=[100*o[n][k]['strict_fraction'] for k in modes]
    axes[1].bar(xx+(j-.5)*.36,vals,width=.36,color=colors[n],label=labels[n])
axes[1].set(xticks=xx,xticklabels=['Original','GT XY','GT L/W','GT yaw','GT Z/H'],ylim=(0,105),
            ylabel='Matched boxes with 3D IoU >= 0.5 (%)',title='Oracle geometry replacement (not AP)')
axes[1].tick_params(axis='x',labelrotation=25)
axes[1].grid(axis='y',alpha=.2)
categories=['range_0_20','range_20_40','range_40_plus','points_6_20','points_101_plus','crowded','isolated']
pretty=['0-20 m','20-40 m','40+ m','6-20 LiDAR pts','101+ LiDAR pts','Crowded (<2 m)','Isolated']
diff=[100*(d['subgroups_at_score_01']['taskdec'][k]['recall_05']-
           d['subgroups_at_score_01']['concat'][k]['recall_05']) for k in categories]
axes[2].barh(pretty,diff,color=colors['taskdec']);axes[2].invert_yaxis()
axes[2].set(xlabel='TaskDec - Concat recall (percentage points)',title='Strict recall gap, score >= 0.1')
axes[2].axvline(0,color='gray',lw=.8);axes[2].grid(axis='x',alpha=.2)
fig.suptitle('512 fixed validation frames | 1,052 Moderate pedestrians | Different training epochs',fontsize=11)
fig.tight_layout(rect=[0,0,1,.94])
fig.savefig(OUT/'diagnostic_summary.png',dpi=160)
fig.savefig(OUT/'diagnostic_summary.pdf')
plt.close(fig)

lines=['# V2X-Radar-V 行人几何诊断与 2×2 patch 决策','',
'日期：2026-09-16。用户要求先诊断中心、尺寸、朝向和漏检，再判断是否值得缩小 patch。','',
'**结论：建议开展独立 2×2 patch 对照。当前最明确的误差是水平中心定位；尺寸和朝向不是这组框匹配失败的主要来源。已有结果没有证明 4×4 patch 是唯一原因，也没有证明 2×2 一定提高正式 AP。**','',
'**实验身份与范围。** TaskDec 使用 epoch50 best，Concat 使用 epoch75 best；第50轮 Concat 权重已不保留。现有同轮50验证指标已显示严格IoU差距，本次不同轮次诊断用于定位当前误差类型，不能当作同轮次架构因果消融。','',
'从1487帧去重val中按ID顺序均匀抽取512帧，先固定样本再推理。共有1079个ROI内行人，1052个符合Moderate GT标准。checkpoint用同一文件句柄计算SHA并读取，避免训练原子替换导致身份不一致；两组分别记录真实epoch和SHA。','',
'诊断使用原生ego坐标3D框、一对一匹配；不是KITTI AP重评，预测未采用图像框高度过滤。下述召回为固定阈值诊断召回，几何修正命中率是条件比例，均不可当论文AP。','',
'**1. 发现目标与框定位的差距。**','',
'score≥0.1，以IoU门限进行最大匹配数的一对一分配；忽略GT上的匹配不计误检。','',
'| IoU | TaskDec 召回 | Concat 召回 | 差值 |','|---|---:|---:|---:|']
for i in ['0.25','0.5']:
    a=d['performance']['taskdec']['0.10'][i]['recall']*100
    b=d['performance']['concat']['0.10'][i]['recall']*100
    lines.append(f'| {i} | {a:.2f}% | {b:.2f}% | {a-b:+.2f} pp |')
lines += ['',
'score≥0.1、中心距离≤1m的一对一匹配下，两模型分别覆盖945/1052个Moderate行人，其中共同覆盖892个（各有53个仅自身覆盖）。以下几何比较限定在同一批892个GT上，避免用不同难度的匹配对象直接比较。','',
'**2. 几何误差：同一批892个GT。**','',
'| 误差 | TaskDec 中位数 | Concat 中位数 | TaskDec P90 | Concat P90 |','|---|---:|---:|---:|---:|']
for k,label,scale in [('xy_m','水平中心（cm）',100),('z_abs_m','高度中心（cm）',100),
                       ('length_abs_m','长度（cm）',100),('width_abs_m','宽度（cm）',100),
                       ('height_abs_m','高度尺寸（cm）',100),('yaw_deg','朝向（度，模π）',1)]:
    vals=[g[n][k][stat]*scale for stat in ['median','p90'] for n in ['taskdec','concat']]
    lines.append('| '+label+' | '+' | '.join(f'{v:.2f}' for v in vals)+' |')
lines += ['',
'水平中心误差的差异在score≥0.05、0.1、0.3的共同配对集合中方向一致；不是只在一个置信度阈值出现。中位差只有约1.4cm，但行人占地约0.65×0.68m，接近IoU边界的样本会对厘米级差异敏感。原有大小、方向、z误差也有贡献，故单看中心距离不能精确推导AP差值。','',
'**3. 固定配对后的几何替换。** 仅离线替换预测框某些坐标为对应GT，保留置信度、配对及其余参数；不是实际可用推理。','',
'| 替换项 | TaskDec IoU≥0.5 | Concat IoU≥0.5 | TaskDec 从失败转为通过 |','|---|---:|---:|---:|']
for mode,label in [('original','不替换'),('xy','只替换水平中心XY'),('length_width','只替换长宽'),
                    ('yaw','只替换朝向'),('z_height','只替换Z中心和高度')]:
    lines.append(f"| {label} | {100*o['taskdec'][mode]['strict_fraction']:.2f}% | {100*o['concat'][mode]['strict_fraction']:.2f}% | {o['taskdec'][mode]['rescued']} |")
lines += ['',
'原配对集合中TaskDec有196个框未过IoU0.5，XY校正使187个通过（其中187/196约95.4%）；同时两模型条件命中率差距由9.64缩至0.45个百分点。长宽校正仅救回17个、另有2个转差；朝向校正救回3个、另有2个转差。这个对比支持优先处理水平中心误差。',
'98.99%并非AP，不包含所有漏检、误检或排序问题，也不意味着中心误差优化就能达到接近99的检测成绩。','',
'**4. 分距离、点数与人群密度。** 点数为原始LiDAR落在GT框内的点数；拥挤定义为ROI内最近其他行人的中心距离<2m。','',
'| 分组 | Moderate GT | TaskDec严格召回 | Concat严格召回 | 差值 |','|---|---:|---:|---:|---:|']
group_names={'range_0_20':'0–20m','range_20_40':'20–40m','range_40_plus':'≥40m',
    'points_0_5':'0–5点（样本很少）','points_6_20':'6–20点','points_21_100':'21–100点','points_101_plus':'≥101点',
    'crowded':'拥挤（最近行人<2m）','isolated':'非拥挤'}
for key,label in group_names.items():
    a=d['subgroups_at_score_01']['taskdec'][key];b=d['subgroups_at_score_01']['concat'][key]
    lines.append(f"| {label} | {a['gt']} | {100*a['recall_05']:.2f}% | {100*b['recall_05']:.2f}% | {100*(a['recall_05']-b['recall_05']):+.2f} pp |")
lines += ['',
'拥挤组差12.80点，非拥挤组差5.08点，符合进一步检查局部空间区分能力的方向。近距离和点数充分组也有差距，因此不能只归因于远处点太少。分组是同一批对象的不同划分，不可累加样本数或称为独立实验。0–5点仅13个GT，不作稳定结论。','',
'**5. 是否只是分数阈值不合适？** 预先采用0.01步长扫描，选择不超过给定FP/帧预算的最高召回。','',
'| 严格IoU误检预算 | TaskDec阈值 / 实际FP每帧 / 召回 | Concat阈值 / 实际FP每帧 / 召回 |','|---|---:|---:|']
for budget in ['0.25','0.5','1.0']:
    vals=[]
    for n in ['taskdec','concat']:
        row=d['fp_budget_comparisons'][n]['0.5'][budget]
        vals.append(f"{row['score_threshold']:.2f} / {row['fp_per_frame']:.3f} / {100*row['recall']:.2f}%")
    lines.append('| '+budget+' | '+' | '.join(vals)+' |')
lines += ['',
'在恰好0.25 FP/帧时两模型仍相差14.92个召回百分点。调整score阈值没有消除差距；TaskDec在score0.1时误检也更多（3.07 vs 2.05 FP/帧），所以除定位外，分数排序/误检质量也不能忽略。这里没有修改正式推理阈值。','',
'**6. 是否做2：建议做独立小patch对照，先验证再决定完整追加训练。**','',
'- 目标假设：减轻1.6m空间patch压缩，让行人和相邻目标保留更细的位置线索。不能将当前诊断写成4×4粒度导致误差的已证实因果。',
'- 唯一主要结构变化：PATCH_SIZE 4×4→2×2；N_QUERY 16→4作为保持融合输出128通道的必要配套。BEV单元仍0.4m，物理patch改为0.8m；编码器、neck/head、数据、增强、损失权重、训练日程和选模规则保持对应一致。',
'- 先测显存与吞吐；patch数增为4倍，但每patch query减少，不能直接说显存或总算力恰好4倍。记录实际成本。',
'- 使用独立目录、相同编码器/head初始化与训练预算做4×4 / 2×2对照；原有TaskDec、Concat和patch继续原定80轮。尺寸不同的融合投影不能直接沿用原参数；若采用warm-start，则两组都应计入并对齐这部分成本。',
'- 判断信号：行人中心误差和P90下降、拥挤组严格召回及完整val行人AP@0.5提高，同时检查车辆/骑行者和总体AP，不用宽松IoU单项代替目标。短期试验只用于探索，不当作80轮最终架构比较。',
'- 原始patch后续表现与TaskDec80轮结果仍有价值，可帮助区分共同patch压缩与解耦/任务控制、训练收敛等解释。本轮仅完成步骤1和步骤2的判断，未启动2×2训练。','',
'**产物与资源。** 推理数据处理约34.25秒，GPU分配峰值0.708GiB、缓存峰值1.988GiB。只保存压缩行人预测、GT统计、小CSV和图；没有复制checkpoint或保存大特征。',
'[诊断图](../analysis_exports/v2x_taskdec_260916/pedestrian_error_diagnostic/diagnostic_summary.png) · '
'[完整JSON](../analysis_exports/v2x_taskdec_260916/pedestrian_error_diagnostic/analysis.json) · '
'[逐对象配对误差](../analysis_exports/v2x_taskdec_260916/pedestrian_error_diagnostic/paired_errors.csv) · '
'[固定样本与checkpoint SHA](../analysis_exports/v2x_taskdec_260916/pedestrian_error_diagnostic/protocol.json)','']
path=ROOT/'results/taskdec_v2x_pedestrian_error_diagnostic_and_patch_decision_260916.md'
path.write_text('\n'.join(lines))
print(path)
print('Artifacts MiB:',sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())/2**20)
