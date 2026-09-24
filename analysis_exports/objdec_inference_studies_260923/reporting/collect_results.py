"""Collect completed, predeclared inference studies without changing results."""
import csv
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent.parent
ROOT=HERE.parents[1]
TARGET=ROOT/'results/objdec_inference_only_results_and_paper_value_260923.md'

def read(p): return json.loads(p.read_text())
def csvrows(p): return list(csv.DictReader(p.open()))
def table(header,rows):
    return '\n'.join(['| '+' | '.join(header)+' |','| '+' | '.join(['---']*len(header))+' |']+
                     ['| '+' | '.join(map(str,row))+' |' for row in rows])

status=read(HERE/'interventions/status.json')
assert status['phase']=='complete' and status['cases']==7
verification=read(HERE/'interventions/baseline_verification.json');assert verification['passed']
for part in ['cache_analysis','diagnostics']:assert read(HERE/part/'status.json')['phase']=='complete'
rows=csvrows(HERE/'interventions/comparison.csv')
for r in rows:
    for k in r:
        if k!='case':r[k]=float(r[k])
for r in rows:
    result=read(HERE/'interventions'/('result_'+r['case']+'.json'));assert result['frames']==1486
    for metric in ['3D','BEV']:
        expected=np.mean([result['metrics']['V2X/'+c+'_'+metric+'_moderate_strict'] for c in ['Vehicle','Pedestrian','Cyclist']])
        assert abs(expected-r['mean_'+metric])<1e-10
labels={'baseline':'完整ObjDec','gate_mean':'gate替换为每帧均值','gate_shuffle_260923':'打乱gate：260923',
        'gate_shuffle_260924':'打乱gate：260924','gate_shuffle_260925':'打乱gate：260925',
        'no_query':'关闭query注入','no_output':'关闭output注入'}
shuffle=[r for r in rows if 'shuffle' in r['case']]
average={k:float(np.mean([r[k] for r in shuffle])) for k in rows[0] if k!='case'}
average['case']='shuffle_mean';labels['shuffle_mean']='打乱gate：三个种子均值'
lines=['# ObjDec：推理补充实验完整结果及论文价值','',
       '2026-09-23。七组GPU评测于09:55:45（北京时间）全部结束，耗时约91.90分钟；两项CPU分析也已完成。新增产物约333.45 MiB，无新增训练。',
       '',f"基准复现通过：相对历史结果，逐类及均值3D/BEV指标最大偏差为{max(abs(v) for v in verification['differences'].values()):.8f}个百分点。每组评测均覆盖1,486帧，保留完整42项难度／IoU指标。",
       '', '## 1. V2X固定权重干预', '',
       'ObjDec CLR第70轮、相同0.16m网格／2×2 patch、相同输入和后处理。以下为AP_R40、Moderate，Vehicle/Pedestrian/Cyclist采用严格IoU 0.7/0.5/0.5；Mean为三类等权平均。Δ为相对本轮完整模型的百分点变化。']
for metric in ['3D','BEV']:
    lines += ['',f'### {metric} AP','',table(['设置','Vehicle','Pedestrian','Cyclist','Mean','ΔMean'],[
        [labels[r['case']]]+[f'{r[c+"_"+metric]:.2f}' for c in ['Vehicle','Pedestrian','Cyclist']]+
        [f'{r["mean_"+metric]:.2f}',f'{r["delta_"+metric]:+.4f}'] for r in rows+[average]])]
lines += ['', '三个shuffle种子是同一权重的随机干预重复，不是三个训练种子。3D mAP范围为79.2064–79.3519，BEV为85.3866–85.4310；不将其当作训练方差或统计显著性。', '',
    '**可用证据。** gate均值化保留当前帧的整体均值但移除空间差异，3D/BEV分别下降1.92/0.73点；空间打乱保留每帧gate边际分布却破坏其与局部特征的位置对应，三个种子平均下降2.12/0.86点。这支持当前已训练模型依赖gate的空间组织，且三类均受影响。', '',
    '**结论边界。** 打乱会改变空间平滑性及与其他控制量的关系；推理干预也引入训练／推理分布变化。该实验不等于去掉gate重新训练的消融，亦没有直接隔离shared/specific分支的贡献。', '',
    '**需要收紧的说法。** 单独关闭query注入后，3D/BEV变化为+0.0030/−0.0040点；单独关闭output注入后为+0.0005/−0.0033点。在这份V2X权重上，两条增量各自的直接推理影响极小。小测已确认开关生效、对应增量确实为零，不是只关了loss。不能写成“两条注入均带来明显收益”。但未测试二者同时关闭，不能排除冗余；没有重训，也不能推断它们对训练或K-Radar都无用。', '',
    'K-Radar既有w/o object context涉及相应监督和两条注入、采用另一训练与选模流程；与这里的V2X单路径推理干预不是同一个实验，分别报告。', '',
    '## 2. K-Radar全量空间gate统计', '',
    '10,065帧、51个序列；每帧FG/BG区域gate先取均值，再按帧等权统计。GT只用于事后划区，推理gate不使用GT。FG>BG占比指“帧内FG均值大于BG均值的帧比例”，不是前景分类准确率、AUROC或所有patch均大于背景。']
weather_names={'all':'全部','normal':'正常','overcast':'阴天','fog':'雾','rain':'雨','sleet':'雨夹雪','lightsnow':'小雪','heavysnow':'大雪'}
gates=csvrows(HERE/'cache_analysis/gate_by_weather.csv')
lines += ['',table(['天气','帧数','FG均值','BG均值','FG−BG','FG>BG帧占比'],[
    [weather_names[r['weather']],r['frames'],f'{float(r["fg_mean"]):.4f}',f'{float(r["bg_mean"]):.4f}',
     f'{float(r["fg_minus_bg_mean"]):.4f}',f'{float(r["fg_gt_bg_fraction"])*100:.2f}%'] for r in gates]),'',
    '全部天气均表现出更强的前景平均响应；整体99.06%的帧FG>BG，大雪为94.99%，并非每帧成立。按序列等权FG−BG为0.15037，接近按帧等权0.15246。适合补强Fig.4的代表性，但不能用不同天气之间的gate绝对值推断某天气更易检测。K-Radar的统计与V2X的干预可提供互补观察，不能写成同一模型上的直接因果链。', '',
    '## 3. V2X召回及定位诊断', '',
    '固定score≥0.1、1,486帧、11,854个有效Moderate GT，以native ego几何IoU做类别内一对一匹配。这是GT加权召回，不是官方AP，也不是三类召回等权平均。不同模型的分数标定会影响固定score下的召回；此分析不含precision/FP。']
diagnostic=read(HERE/'diagnostics/summary.json')
model_names={'l4dr':'L4DR (L+R)','objdec_lr':'ObjDec (L+R)','asf':'ASF-style (C+L+R)','objdec_clr':'ObjDec (C+L+R)'}
for metric in ['3D','BEV']:
    values=[]
    for model in ['l4dr','objdec_lr','asf','objdec_clr']:
        data={r['cls']:r for r in diagnostic['all_groups'] if r['model']==model}
        values.append([model_names[model]]+[f'{100*data[c]["recall_"+metric]:.2f}' for c in ['Vehicle','Pedestrian','Cyclist','all']])
    lines += ['',f'### {metric}召回（%）','',table(['方法','Vehicle','Pedestrian','Cyclist','全部GT'],values)]
lines += ['', 'ObjDec-LR比L4DR净多检出77个GT（新增442、丢失365），三类3D/BEV召回均有提高。三模态ObjDec相对ASF-style的整体3D召回稍低，BEV稍高，并非全维度领先。', '',
    '### 完整预定义分组差值', '', '下表是ObjDec减对应基线，单位为百分点。距离为xy径向距离；点数为标定后原始点云在GT 3D框内的数量。']
comparisons=csvrows(HERE/'diagnostics/paired_comparisons.csv')
groups=list(dict.fromkeys(r['group'] for r in comparisons if r['cls']=='all'))
table_rows=[]
for group in groups:
    a=next(r for r in comparisons if r['cls']=='all' and r['group']==group and r['method']=='objdec_lr')
    b=next(r for r in comparisons if r['cls']=='all' and r['group']==group and r['method']=='objdec_clr')
    table_rows.append([group,a['gt']]+[f'{100*float(r["recall_delta_"+m]):+.2f}' for r in [a,b] for m in ['3D','BEV']])
lines += ['',table(['分组','GT数','LR−L4DR 3D','LR−L4DR BEV','CLR−ASF 3D','CLR−ASF BEV'],table_rows),'',
    '**可用证据。** ObjDec-LR在三个距离段均提高召回，≥60m的3D增益约1.27点；三模态ObjDec在≥60m相对ASF-style的3D/BEV增益约1.39/2.47点。适合将远距离表现作为附录的细粒度补充。', '',
    '**不能泛化的例子。** LR在LiDAR 0–5点组的3D/BEV增益为10.59/16.47点，但只有170个GT，6–20点组3D却下降1.24点；三模态版本在0–5点组反而落后ASF-style。不能将它概括为“对任何稀疏目标都更鲁棒”。点数、距离与类别相关，当前统计没有控制混杂因素。', '',
    '### 共同TP定位误差', '', '只在双方都匹配成功的同一组GT上比较，仍需结合上述召回。朝向是模π的框轴差，不代表有向行驶方向准确率。']
error_rows=[]
for r in diagnostic['paired_all']:
    if r['cls']!='all': continue
    for model in [r['baseline'],r['method']]:
        error_rows.append([model_names[model],r['common_tp_3D'],f'{r["common_tp_"+model+"_xy_m"]:.5f}',
            f'{r["common_tp_"+model+"_z_m"]:.5f}',f'{r["common_tp_"+model+"_size_l1_m"]:.5f}',f'{r["common_tp_"+model+"_yaw_axis_deg"]:.3f}'])
lines += ['',table(['方法','共同TP数','xy误差/m','z误差/m','尺寸L1/m','朝向轴差/°'],error_rows),'',
    'LR中心误差几乎不变，朝向轴差略低；其他误差并非一致更好。这批结果支持一定的召回收益，不支持“所有目标定位更精准”的泛化表述。', '',
    '## 4. Shared帧级对应性：需要调整原有解释', '',
    '下表是10个预定义错配种子的均值，同帧与错配使用同一批保留anchor，错配保持天气并剔除同序列。原始256维的帧均值余弦与逐patch余弦是两种统计，不应混用。']
correspondence=csvrows(HERE/'cache_analysis/frame_correspondence_summary.csv')
vals=[]
for pair in ['C-L','C-R','L-R']:
    aa=next(r for r in correspondence if r['feature']=='shared' and r['pair']==pair and r['centering']=='uncentered')
    bb=next(r for r in correspondence if r['feature']=='shared' and r['pair']==pair and r['centering']=='weather_centered')
    vals.append([pair]+[f'{float(r[k]):.6f}' for r in [aa,bb] for k in ['matched','mismatched']])
lines += ['',table(['模态对','同帧余弦','错配余弦','去天气均值后：同帧','去天气均值后：错配'],vals),'',
    '同帧与错配的原始shared余弦都很高，Camera相关两对几乎没有差异。因此，高余弦单独不能证明对象语义的对应；共同均值方向可能解释其中很大部分。去均值后L–R仍有一定对应性，Camera相关两对较弱。CKA没有显示shared普遍优于raw，完整CSV与图保留。', '',
    '这不是“整个shared分支无用”的证明：均值会丢失局部信息，尚无逐patch错配对照；也没有隔离shared分支的推理或重训效应。PCA可以保留为分布结构可视化，但不能作为“严格语义解耦已被证明”的主证据。', '',
    '## 5. 建议如何纳入论文', '',
    table(['证据','能支持的论点','建议位置'],[
        ['gate均值／打乱','已训练V2X模型依赖gate的空间组织','正文机制分析给一小表；附录D列全部七设置与随机重复'],
        ['全量FG/BG统计','Fig.4所示前景偏向具有总体代表性','正文给全量数字；附录E列全部天气及分布'],
        ['LR与远距离召回','本地对照下的细粒度检测覆盖收益','附录G，正文泛化段可引用一句'],
        ['query/output近零变化','该V2X模型对单独移除两条增量不敏感','附录D完整报告，收紧上下文“普遍必要”的说法'],
        ['shared匹配／错配','原始高相似度有共同均值方向的影响','附录E补控制，正文把PCA定位为描述性证据']]),'',
    '正文若篇幅有限，可将三个gate打乱种子汇总为一行均值和范围，但必须注明全部结果在附录。完整模型、gate均值、gate打乱、no query、no output五种设置可用极小表共同展示，不需要用筛掉近零结果来制造“每条路径都有效”的印象。', '',
    '**建议的主张重心：** 学习shared/specific表征并通过目标相关空间控制组织融合；这批新增结果直接加强后半句。解耦表征的检测价值仍应以既有训练消融为主，不能把gate干预的下降全部归因于解耦。query/output作为完整实现路径如实介绍，本轮没有证据把二者在V2X上的独立必要性列为卖点。', '',
    '### 可直接采用的正文观察（中文）', '',
    '在V2X-Radar-V上，我们固定训练完成的ObjDec权重，仅改变推理时的控制信号。将预测gate替换为帧内均值使3D/BEV mAP下降1.92/0.73个百分点；在每帧内随机置换gate、保持其数值分布时，三个固定随机种子的平均下降为2.12/0.86个百分点。这表明该模型对gate与局部特征的空间对应关系敏感。相比之下，分别移除query和输出上下文增量引起的mAP变化均小于0.004个百分点，说明其单独推理贡献在当前配置中有限。上述结果是固定权重干预，不替代重新训练的组件消融。', '',
    '### Suggested English observation', '',
    'On V2X-Radar-V, we keep the trained ObjDec weights fixed and intervene only on the inference-time control signals. Replacing each predicted gate map with its frame-wise mean reduces 3D/BEV mAP by 1.92/0.73 percentage points. Permuting gates within each frame while preserving their value distribution yields average decreases of 2.12/0.86 points across three fixed random seeds, indicating sensitivity to the spatial correspondence between gates and local features. In contrast, separately removing the query or output context increment changes mAP by less than 0.004 points in this configuration. These fixed-weight interventions complement, rather than replace, retrained component ablations.', '',
    '## 6. 结果来源', '',
    '- `analysis_exports/objdec_inference_studies_260923/interventions/`：status、baseline_verification、result_*.json、comparison.csv、smoke与protocol。',
    '- `analysis_exports/objdec_inference_studies_260923/cache_analysis/`：gate_by_weather、frame_correspondence_summary、linear_cka、centered_spectrum及三组PDF/PNG。',
    '- `analysis_exports/objdec_inference_studies_260923/diagnostics/`：逐GT预测匹配、全部分组、逐类召回和共同TP误差。首轮CSV字段并集导出问题已由finish_from_gt.py修复；原异常和恢复记录均保留。',
    '- 本文仅汇总已完成的实验，没有新增调参或选择更有利的test分组。']
TARGET.write_text('\n'.join(lines)+'\n')
print(TARGET)
