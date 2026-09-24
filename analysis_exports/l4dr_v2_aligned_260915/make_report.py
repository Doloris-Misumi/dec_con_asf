"""Generate the comparison only from complete, verified full-test evaluations."""
import csv
import datetime
import io
import json
from collections import Counter
from pathlib import Path
from common import HERE, ROOT, STRONG, N, CONDITIONS, WEATHER, records, save, sha

result_dir=ROOT/'results'
stem='paper_kradar_v2_l4dr_asf_strong_aligned_260915'
report_path=result_dir/'taskdec_v2_l4dr_aligned_evaluation_260915.md'
strong=json.loads((HERE/'strong_evaluation.json').read_text())
l4dr=json.loads((HERE/'l4dr_evaluation.json').read_text())
verification=json.loads((HERE/'strong_archive_verification.json').read_text())
assert all(x['status']=='complete' for x in [strong,l4dr,verification])
assert verification['metrics_checked']==216 and verification['maximum_absolute_difference']<1e-8
assert l4dr['num_samples']==N and l4dr['failure_count']==0
asf_path=Path('/home/hongsheng/K-Radar-main/results/official_asf_v2_RLC/summary_conf0.3.json')
asf=json.loads(asf_path.read_text())['0.3']
rec=records()
gt_counts={g:Counter('sed' if c=='Sedan' else 'bus' for r in rec if g in r['groups']
    for c,box,track,av in r['meta']['label']) for g in CONDITIONS}
data={}
for model,source in [('L4DR local aligned',l4dr),('DecControlled Strong',strong)]:
    data[model]={}
    for group,v in source['metrics'].items():
        data[model][group]={}
        for c in v['classes']:
            data[model][group][c['cls']]={metric:{str(iou):c[key][j] for j,iou in enumerate(c['iou'])}
                for metric,key in [('3D','3d'),('BEV','bev')]}
data['ASF official archive']=asf
models=['L4DR local aligned','ASF official archive','DecControlled Strong']
def value(model,cls='mean',metric='3D',iou=.3,group='all'):
    if cls=='mean':return sum(value(model,c,metric,iou,group) for c in ['sed','bus'])/2
    return data[model][group][cls][metric][str(iou)]
def table(header,rows):
    return '\n'.join(['| '+' | '.join(header)+' |','| '+' | '.join(['---']*len(header))+' |']+
        ['| '+' | '.join(map(str,row))+' |' for row in rows])

csv_rows=[]
for group in CONDITIONS:
    for cls in ['sed','bus']:
        for metric in ['3D','BEV']:
            for iou in [.3,.5,.7]:
                lv=value(models[0],cls,metric,iou,group)
                av=value(models[1],cls,metric,iou,group)
                sv=value(models[2],cls,metric,iou,group)
                csv_rows.append(dict(condition=group,cls=cls,metric=metric,iou=iou,
                    gt_objects=gt_counts[group][cls],has_gt=gt_counts[group][cls]>0,
                    l4dr_local_aligned=lv,asf_official_archive=av,strong_rescored=sv,
                    strong_minus_l4dr=sv-lv,strong_minus_asf=sv-av,
                    local_gt_exact_match_l4dr_strong=True,asf_frame_gt_reverified=False))
buf=io.StringIO();writer=csv.DictWriter(buf,fieldnames=list(csv_rows[0]));writer.writeheader();writer.writerows(csv_rows)
(result_dir/(stem+'.csv')).write_text(buf.getvalue())

intro=(f"本次已完成 L4DR 双类别官方权重在 **v2.0、13,727 帧、与 Strong 完全相同 GT 和 revised evaluator** 下的全量评测。"
    f"两类平均 AP3D@0.3 / @0.5：L4DR 为 {value(models[0]):.2f} / {value(models[0],iou=.5):.2f}，"
    f"Strong 为 {value(models[2]):.2f} / {value(models[2],iou=.5):.2f}；"
    f"Strong 相对 L4DR 的差值为 **{value(models[2])-value(models[0]):+.2f} / {value(models[2],iou=.5)-value(models[0],iou=.5):+.2f} AP 点**。")
text=['# K-Radar v2：L4DR 统一评测与 Strong / ASF 对照','',
    '完成时间：'+datetime.datetime.now().astimezone().isoformat(),'',intro,'',
    '本次结果不支持“统一评测后 Strong 的 Total 领先 L4DR”。Strong 相对官方 ASF 归档的均值收益仍是 '
    '+0.36 / +1.48 点（AP3D@0.3 / @0.5）；v2 写作可继续聚焦 Dec 家族在宽 ROI、双类别设置下相对 ASF 的扩展收益，'
    '同时保留 L4DR 的更高 Total 和天气上的完整正负结果。','',
    '**来源边界：** L4DR 为本次本地推理，Strong 为原有预测的本次复算；ASF 保留官方结果归档，本次没有其逐帧预测可供重新评分。'
    'L4DR 与 Strong 已核实逐帧 GT 完全相同，ASF 的配置口径一致但本轮未逐帧核验。表中三行均明确来源，不能把 ASF 行写成“三方法本次同时复测”。','',
    '## 1. 对齐了哪些项目','',
    table(['项目','本次设置 / 核验'],[
        ['评测标签','K-Radar v2_0；Sedan + Bus or Truck；onlyR=False'],
        ['ROI','[0, −16, −2, 72, 16, 7.6]；标定 z_offset=0.7'],
        ['测试帧','13,727 帧；与 Strong 保存的 GT 和天气元数据逐帧、逐行完全一致'],
        ['GT 数量','Sedan 29,613；Bus/Truck 5,843'],
        ['前处理置信度','NMS 前 SCORE_THRESH=0.1；最终导出 score > 0.3'],
        ['NMS','原生 class-agnostic rotated NMS；IoU=0.01；pre=4096 / post=500；两仓库 NMS 源码相同'],
        ['KITTI 导出','直接调用 TaskDec 原始导出函数；GT 四舍五入到 2 位，坐标/尺寸顺序一致'],
        ['评测器','TaskDec revised evaluator：41 个 precision 值平均、z_center=0.5；不是标准 KITTI R40'],
        ['Strong 归档复核','全部 18 条件 × 2 类 × 6 指标 = 216 项；与原归档差值全部为 0'],
        ['L4DR 输入与结构','原生 LiDAR + 正式恢复的稀疏雷达张量；MGF backbone；DENOISE_T=0.1'],
        ['权重加载','双类别 572 项参数 strict=True；无 missing/unexpected keys，无舍弃权重'],
    ]),'',
    '未统一训练过程、模态或模型自身输入编码：L4DR 使用 L+R，Strong/ASF 使用 C+L+R。'
    '本次统一测试协议，不声称三者经过相同训练。L4DR 当前公开配置的有效 `MODEL.POST_PROCESSING.NMS_CONFIG.NMS_THRESH` 是 0.7，'
    '另一个 `DENSE_HEAD.POST_PROCESSING` 中的 0.01 不被其最终后处理读取。本次明确将有效阈值对齐到 Strong/ASF 的 0.01；'
    '该设置在推理前确定，未依据测试 AP 调参。因此本次是包括后处理在内的统一协议实验，不能当成仅替换 evaluator 的原生 L4DR 结果。','',
    '## 2. Total：完整六项指标','',
    'AP 单位为百分数；Mean 为两类 AP 的等权平均。Total 直接汇总全测试集计算，不是天气 AP 的平均。','']
total_rows=[]
for model in models:
    for cls,label in [('sed','Sedan'),('bus','Bus/Truck'),('mean','Mean')]:
        total_rows.append([model,label]+[f'{value(model,cls,m,t):.2f}' for m in ['3D','BEV'] for t in [.3,.5,.7]])
text += [table(['方法','类别','3D@0.3','3D@0.5','3D@0.7','BEV@0.3','BEV@0.5','BEV@0.7'],total_rows),'',
    '## 3. 天气表（参考 L4DR Table 10 的组织）','',
    '天气仅改变评测分组，不改变模型或阈值。Fog 的 Bus/Truck GT 数为 0，显示“—”；CSV 保留 evaluator 原始 0 并设置 has_gt=False，不能将它算作有效收益。','']
weather_order=['all','normal','lightsnow','heavysnow','rain','sleet','overcast','fog']
for iou in [.3,.5]:
    text += [f'### AP3D@{iou}','']
    wrows=[]
    for cls,label in [('sed','Sedan'),('bus','Bus/Truck')]:
        for model in models:
            wrows.append([label,model]+[f'{value(model,cls,"3D",iou,g):.2f}' if gt_counts[g][cls] else '—' for g in weather_order])
    text += [table(['类别','方法','Total','Normal','Light snow','Heavy snow','Rain','Sleet','Overcast','Fog'],wrows),'']
text += ['所有 18 条件、两类、3D/BEV 三个 IoU 阈值及正负差值见 ['+stem+'.csv]('+stem+'.csv)。','',
    '## 4. 固定预测后的评测协议交叉检查','',
    '下表只改变 AP 的 11/41 点汇总方式和 IoU 的高度中心；GT、预测、NMS 与置信度固定。'
    '这能量化 evaluator 的影响，不能把本次本地结果与论文 Table 10 的差值全部归因于 evaluator。','']
diag_rows=[]
for model,label in [('strong','Strong'),('l4dr','L4DR')]:
    diag=json.loads((HERE/(model+'_protocol_diagnostic.json')).read_text())
    assert diag['status']=='complete' and diag['legacy_api_verified'] and diag['revised_api_verified']
    for setting in sorted(diag['settings'],key=lambda x:(x['ap_samples'], -x['z_center'])):
        vals=[]
        for iou in [.3,.5]:
            vals.append(sum(c['3d'][c['iou'].index(iou)] for c in setting['classes'])/2)
        diag_rows.append([label,setting['ap_samples'],setting['z_center']]+[f'{v:.2f}' for v in vals])
text += [table(['方法','AP 汇总点数','z_center','Mean AP3D@0.3','Mean AP3D@0.5'],diag_rows),'',
    '11 点 + z_center=1.0 与原始 legacy API 数值一致；41 点 + z_center=0.5 与本次 revised 全量结果一致。'
    '改变高度中心不影响 BEV 的几何 IoU；更换 AP 汇总点数仍会改变 BEV AP。','',
    '## 5. 权重身份、论文引用与写作建议','',
    '原本地 `L4DR-KRadar-v1.1-model_34.pt` 是 Sedan 单类别，不能装成双类别用。'
    '本次采用作者发布的 [L4DR_KRadar2.1 双类别权重](https://huggingface.co/hx24/L4DR_KRadar2.1)，'
    '固定 revision `4f65460867a61a704a2290ff0ca2e8d05b463312` 的 `model_30.pt`。'
    '同目录 `model.pt` 的 LFS SHA 相同，只下载一份，没有比较多个 checkpoint 后挑选最优。','',
    'checkpoint SHA-256：`ccdc151a0c16185be8ab1801affed1f71fd6f63ae6f3c2fbf94c30346a0d8180`。'
    '发布名称为 v2.1；本次评测强制使用并核验 v2.0 标签。不能据此宣称重现了论文 Table 10 的 checkpoint、训练标签和完整运行环境。','',
    '表行建议写 `L4DR (official checkpoint, locally evaluated)`；Strong 继续写 `DecControlled Strong (ours)`，'
    '并说明它不含 task-context 分支。ASF 继续写 `ASF (official archived results)`。'
    '如需保留 Table 10 原始引用，另列 `L4DR (paper)` 并指向旧表，不用新数值覆盖文献原值。','',
    'English table note: L4DR is evaluated locally from the author-released dual-class checkpoint on the exact v2.0 frames and ground-truth boxes used by DecControlled Strong. '
    'Both local rows use the revised evaluator, a score threshold of 0.3, and class-agnostic rotated NMS at 0.01. '
    'The ASF row contains archived official results under the corresponding configuration and is not rescored in this run. '
    'L4DR uses L+R; ASF and Strong use C+L+R. Strong is a Dec-family variant without task-context modulation.','',
    '## 6. 文件与复现','',
    '- [本次运行目录与命令](../analysis_exports/l4dr_v2_aligned_260915/README.md)',
    '- [逐帧核验与协议](../analysis_exports/l4dr_v2_aligned_260915/preflight.json)',
    '- [L4DR 原始全量指标](../analysis_exports/l4dr_v2_aligned_260915/l4dr_evaluation.json)',
    '- [Strong 复算全量指标](../analysis_exports/l4dr_v2_aligned_260915/strong_evaluation.json)',
    '- [Strong 归档 216 项核验](../analysis_exports/l4dr_v2_aligned_260915/strong_archive_verification.json)',
    '- [原论文天气对照与历史协议审计](taskdec_v2_l4dr_weather_total_and_eval_protocol_audit_260912.md)',
    '- [LaTeX 紧凑 Total + 天气表]('+stem+'.tex)','',
    '只保存一份预测文本，天气/道路/昼夜按索引分组评测，不复制 GT、点云或完整特征。'
    '下载权重约 237 MiB；原始雷达输入复用此前 WCBR 已完成的恢复目录。'
    '原生 Dataset 会累计缓存已读点云，本次仅在独立 runner 中修正其内存保留行为；'
    '修正前的短暂未完成运行另存为 partial，未纳入 AP。','']
report_path.write_text('\n'.join(text))

tex=[r'\begin{table*}[t]',r'\centering',r'\small',
    r'\caption{K-Radar v2.0 comparison. L4DR is evaluated locally with the same frames, ground truth, postprocessing, and revised evaluator as Strong. ASF uses archived official results.}',
    r'\label{tab:kradar_v2_aligned}',r'\begin{tabular}{llrrrrrr}',r'\toprule',
    r'Method & Input & \multicolumn{3}{c}{AP$_{3D}$@0.3} & \multicolumn{3}{c}{AP$_{3D}$@0.5} \\',
    r' & & Sedan & Bus/Truck & Mean & Sedan & Bus/Truck & Mean \\',r'\midrule']
for model,short,modal in [(models[0],'L4DR (local)','L+R'),(models[1],'ASF (archive)','C+L+R'),(models[2],'DecControlled Strong (ours)','C+L+R')]:
    tex.append(' & '.join([short,modal]+[f'{value(model,c,"3D",iou):.2f}' for iou in [.3,.5] for c in ['sed','bus','mean']])+r' \\')
tex += [r'\bottomrule',r'\end{tabular}',r'\end{table*}','']
for iou in [.3,.5]:
    tex += [r'\begin{table*}[t]',r'\centering',r'\scriptsize',
        '\\caption{Weather breakdown of AP$_{3D}$@'+str(iou)+'. Source definitions follow Table~\\ref{tab:kradar_v2_aligned}. A dash denotes no ground-truth objects.}',
        r'\begin{tabular}{llrrrrrrrr}',r'\toprule',
        r'Class & Method & Total & Normal & Light snow & Heavy snow & Rain & Sleet & Overcast & Fog \\',r'\midrule']
    for cls,label in [('sed','Sedan'),('bus','Bus/Truck')]:
        for model,short in [(models[0],'L4DR (local)'),(models[1],'ASF (archive)'),(models[2],'Strong (ours)')]:
            vals=[f'{value(model,cls,"3D",iou,g):.2f}' if gt_counts[g][cls] else '--' for g in weather_order]
            tex.append(' & '.join([label,short]+vals)+r' \\')
    tex += [r'\bottomrule',r'\end{tabular}',r'\end{table*}','']
(result_dir/(stem+'.tex')).write_text('\n'.join(tex))
save(HERE/'completion.json',dict(status='complete',time=datetime.datetime.now().astimezone().isoformat(),
    num_samples=N,failure_count=0,report=str(report_path),csv=str(result_dir/(stem+'.csv')),
    asf_archive_sha256=sha(asf_path),intro=intro))
index=result_dir/'taskdec_iclr27_chinese_main_appendix_and_result_index_260909.md'
contents=index.read_text()
marker='2026-09-15 L4DR v2 统一评测：'
line=marker+intro+' 详见 [统一评测结果与天气对照](taskdec_v2_l4dr_aligned_evaluation_260915.md)。ASF 保留官方归档，本次未逐帧复算。'
lines=contents.splitlines()
existing=[i for i,x in enumerate(lines) if x.startswith(marker)]
if existing:lines[existing[0]]=line
else:lines[2:2]=[line,'']
index.write_text('\n'.join(lines)+'\n')
print(intro)
print('REPORT COMPLETE',report_path)
