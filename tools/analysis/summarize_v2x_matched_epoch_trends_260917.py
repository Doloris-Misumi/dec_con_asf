#!/usr/bin/env python3
"""Read-only extraction of completed validation checkpoints; no training imports."""
import csv
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'analysis_exports/v2x_taskdec_260916'
PATHS = {'Concat': BASE/'controlled_80ep/concat',
         'ASF-style patch': BASE/'controlled_80ep/patch',
         'TaskDec 4x4': BASE/'controlled_80ep/taskdec',
         'TaskDec 2x2': BASE/'taskdec_patch2_80ep/taskdec',
         'L4DR': ROOT/'analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr'}
OUT = ROOT/'analysis_exports/v2x_matched_epoch_trends_260917'
OUT.mkdir(parents=True, exist_ok=True)
NOW = datetime.datetime.now().astimezone().isoformat()
DATA, SOURCES, rows = {}, {}, []
for name, directory in PATHS.items():
    DATA[name] = {}
    for path in sorted(directory.glob('val_epoch_*.json')):
        raw = path.read_bytes()
        d = json.loads(raw)
        assert d['frames'] == 1487
        assert 'AP_R40' in d['protocol'] and '0.7/0.5/0.5' in d['protocol']
        v = {c:d['metrics'][f'V2X/{c}_3D_moderate_strict'] for c in ['Vehicle','Pedestrian','Cyclist']}
        v['Mean'] = d['selection_metric']
        v['BEV_Mean'] = d['metrics']['V2X/Overall_BEV_moderate']
        assert abs(sum(v[c] for c in ['Vehicle','Pedestrian','Cyclist'])/3-v['Mean']) < 1e-8
        DATA[name][d['epoch']] = v
        row = dict(method=name, epoch=d['epoch'], frames=d['frames'], **v)
        rows.append(row)
        SOURCES[str(path.relative_to(ROOT))] = hashlib.sha256(raw).hexdigest()

def save_csv(name, content):
    with (OUT/name).open('w', newline='') as stream:
        w = csv.DictWriter(stream, fieldnames=list(content[0]))
        w.writeheader(); w.writerows(content)

save_csv('all_validation_metrics.csv', rows)
joint_t = sorted(DATA['TaskDec 2x2'].keys() & DATA['Concat'].keys())
joint_l = sorted(DATA['L4DR'].keys() & DATA['Concat'].keys() & DATA['TaskDec 2x2'].keys())
gap_t = {e:{k:DATA['TaskDec 2x2'][e][k]-DATA['Concat'][e][k]
            for k in ['Vehicle','Pedestrian','Cyclist','Mean']} for e in joint_t}
save_csv('taskdec2_minus_concat.csv', [dict(epoch=e, **gap_t[e]) for e in joint_t])
save_csv('l4dr_matched_epochs.csv', [dict(epoch=e, concat=DATA['Concat'][e]['Mean'],
         taskdec4=DATA['TaskDec 4x4'][e]['Mean'], taskdec2=DATA['TaskDec 2x2'][e]['Mean'],
         l4dr=DATA['L4DR'][e]['Mean'], l4dr_minus_concat=DATA['L4DR'][e]['Mean']-DATA['Concat'][e]['Mean'],
         l4dr_minus_taskdec2=DATA['L4DR'][e]['Mean']-DATA['TaskDec 2x2'][e]['Mean']) for e in joint_l])
(OUT/'sources.json').write_text(json.dumps(dict(updated_at=NOW, sha256=SOURCES),indent=2)+'\n')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,
                     'axes.spines.right':False,'pdf.fonttype':42})
fig, axes = plt.subplots(2,2,figsize=(11,7.4),constrained_layout=True)
colors = {'Concat':'#4c566a','TaskDec 4x4':'#94a3b8','TaskDec 2x2':'#2563eb','L4DR':'#d97706'}
ax = axes[0,0]
for name,color in colors.items():
    es = sorted(DATA[name]); ax.plot(es,[DATA[name][e]['Mean'] for e in es],'-o',lw=1.8,ms=3,label=name,color=color)
ax.set(title='Validation mean 3D AP',ylabel='Moderate AP_R40 (%)',xlabel='Completed epoch')
ax.legend(fontsize=8,loc='lower right')
ax = axes[0,1]
ax.axhline(0,color='#555555',lw=1,ls='--')
ax.plot(joint_t,[gap_t[e]['Mean'] for e in joint_t],'-o',color='#2563eb',lw=2,ms=4)
ax.set(title='TaskDec 2x2 minus Concat: mean AP',ylabel='AP difference (percentage points)',xlabel='Matched epoch')
for e in joint_t[-5:]:
    if e in gap_t: ax.annotate(f"{gap_t[e]['Mean']:+.2f}",(e,gap_t[e]['Mean']),xytext=(0,7),textcoords='offset points',ha='center',fontsize=8)
ax = axes[1,0]
ax.axhline(0,color='#555555',lw=1,ls='--')
late = [e for e in joint_t if e>=30]
for k,color in [('Vehicle','#2563eb'),('Pedestrian','#d97706'),('Cyclist','#16a34a')]:
    ax.plot(late,[gap_t[e][k] for e in late],'-o',label=k,color=color,lw=1.7,ms=3)
ax.set(title='TaskDec 2x2 minus Concat: class differences',ylabel='AP difference (percentage points)',xlabel='Matched epoch')
ax.legend(fontsize=8,loc='lower right')
ax = axes[1,1]
ax.axhline(0,color='#555555',lw=1,ls='--')
for other,color in [('Concat','#4c566a'),('TaskDec 2x2','#2563eb')]:
    ax.plot(joint_l,[DATA['L4DR'][e]['Mean']-DATA[other][e]['Mean'] for e in joint_l],'-o',label=f'L4DR minus {other}',color=color,lw=1.8,ms=3)
ax.set(title='L4DR: comparison at matched epochs',ylabel='AP difference (percentage points)',xlabel='Matched epoch')
ax.legend(fontsize=8)
for ax in axes.flat: ax.grid(alpha=.18); ax.set_axisbelow(True)
fig.suptitle('V2X-Radar-V | 1,487 deduplicated validation frames | strict IoU 0.7 / 0.5 / 0.5',fontsize=11)
fig.savefig(OUT/'matched_epoch_trends.png',dpi=170)
fig.savefig(OUT/'matched_epoch_trends.pdf')
plt.close(fig)

latest, previous = joint_t[-2:][::-1]
current = DATA['TaskDec 2x2'][latest]
prior = DATA['TaskDec 2x2'][previous]
gap_change = gap_t[latest]['Mean'] - gap_t[previous]['Mean']
text = ['# V2X-Radar-V：TaskDec / Concat 差距与 L4DR 同轮对照','',f'更新时间：{NOW}','',
'仅比较已完成的完整去重 val：1487 帧，严格 IoU 0.7/0.5/0.5、Moderate、AP_R40。下面的差值先按原始精度相减，再显示两位小数。没有混入test，也没有插值未完成轮次。','',
'## 最新 TaskDec 同轮对照','',
f'第{latest}轮 TaskDec 2×2 平均3D为{current["Mean"]:.2f}，相对第{previous}轮变化{current["Mean"]-prior["Mean"]:+.2f}点。相对同轮Concat为{gap_t[latest]["Mean"]:+.2f}点；该相对差值比上一验证点变化{gap_change:+.2f}点。','',
'| 方法 | 轮次 | Vehicle | Pedestrian | Cyclist | 平均3D | 平均BEV |',
'|---|---:|---:|---:|---:|---:|---:|']
for name in ['Concat','ASF-style patch','TaskDec 4x4','TaskDec 2x2']:
    v=DATA[name][latest]
    text.append(f'| {name} | {latest} | '+' | '.join(f'{v[k]:.2f}' for k in ['Vehicle','Pedestrian','Cyclist','Mean','BEV_Mean'])+' |')
text += ['',
f'相对自身第{previous}轮，Vehicle / Pedestrian / Cyclist分别变化'+ ' / '.join(f'{current[k]-prior[k]:+.2f}' for k in ['Vehicle','Pedestrian','Cyclist'])+'点。',
f'相对同轮原4×4，平均3D {current["Mean"]-DATA["TaskDec 4x4"][latest]["Mean"]:+.2f}，行人 {current["Pedestrian"]-DATA["TaskDec 4x4"][latest]["Pedestrian"]:+.2f}；相对同轮ASF-style patch，平均3D {current["Mean"]-DATA["ASF-style patch"][latest]["Mean"]:+.2f}。',
'2×2配置同时改变了patch大小和query数量，不能把全部改善严格归因于单独一个因素；ASF-style patch未启用SCL。','',
'## TaskDec 2×2 相对 Concat 的差距','',
'差距存在波动，不能将一个验证区间的改善解释为逐轮追平。下表列出所有已完成的共同验证轮次；最终结果仍需等待完整训练与val选模后的test。','',
'| 轮次 | Concat 均值 | TaskDec 2×2 均值 | Δ均值 | ΔVehicle | ΔPedestrian | ΔCyclist |',
'|---|---:|---:|---:|---:|---:|---:|']
for e in joint_t:
    g=gap_t[e]
    text.append(f"| {e} | {DATA['Concat'][e]['Mean']:.2f} | {DATA['TaskDec 2x2'][e]['Mean']:.2f} | "+' | '.join(f'{g[k]:+.2f}' for k in ['Mean','Vehicle','Pedestrian','Cyclist'])+' |')
text += ['',
'Δ=TaskDec 2×2−Concat；正值表示TaskDec领先。', '',
f'{previous}→{latest}轮：TaskDec均值{prior["Mean"]:.2f}→{current["Mean"]:.2f}；Concat均值{DATA["Concat"][previous]["Mean"]:.2f}→{DATA["Concat"][latest]["Mean"]:.2f}。',
'分类别相对差值（前一验证点→最新验证点）：'+ '；'.join(f'{k} {gap_t[previous][k]:+.2f}→{gap_t[latest][k]:+.2f}' for k in ['Vehicle','Pedestrian','Cyclist'])+'。',
'TaskDec 2×2近期行人AP：'+ '、'.join(f'{e}轮 {DATA["TaskDec 2x2"][e]["Pedestrian"]:.2f}' for e in joint_t[-5:])+'。','',
'## L4DR 与其它架构的同轮均值','',
'| 轮次 | Concat | TaskDec 4×4 | TaskDec 2×2 | L4DR | L4DR−Concat | L4DR−2×2 |','|---|---:|---:|---:|---:|---:|---:|']
for e in joint_l:
    c,o,t,l=[DATA[name][e]['Mean'] for name in ['Concat','TaskDec 4x4','TaskDec 2x2','L4DR']]
    text.append(f'| {e} | {c:.2f} | {o:.2f} | {t:.2f} | {l:.2f} | {l-c:+.2f} | {l-t:+.2f} |')
e=joint_l[-1]
text += ['',f'## 最新共同第{e}轮：分类别对照','',
'| 方法 | Vehicle | Pedestrian | Cyclist | 均值 |','|---|---:|---:|---:|---:|']
for name in ['Concat','TaskDec 4x4','TaskDec 2x2','L4DR']:
    text.append('| '+name+' | '+' | '.join(f'{DATA[name][e][k]:.2f}' for k in ['Vehicle','Pedestrian','Cyclist','Mean'])+' |')
text += ['',
f'最新共同第{e}轮，L4DR相对Concat和TaskDec 2×2分别为{DATA["L4DR"][e]["Mean"]-DATA["Concat"][e]["Mean"]:+.2f}和{DATA["L4DR"][e]["Mean"]-DATA["TaskDec 2x2"][e]["Mean"]:+.2f}点。相对2×2，Vehicle/Pedestrian/Cyclist分别为'+ '/'.join(f'{DATA["L4DR"][e][k]-DATA["TaskDec 2x2"][e][k]:+.2f}' for k in ['Vehicle','Pedestrian','Cyclist'])+'点。不同轮次的最新结果不能用于判断完整训练后的架构优劣。', '',
'解释边界：各组训练集、80轮计划、有效batch8和验证协议相同；L4DR使用L+R、0.16m体素及独立原生架构，其余为C+L+R、0.4m体素。同轮次比较不是同计算量比较，也不能单独用来归因融合设计。最终排名仍需看完整预算和val选模后的test。', '',
'## 趋势图与可核查数据','',
'![同轮验证趋势](../analysis_exports/v2x_matched_epoch_trends_260917/matched_epoch_trends.png)','',
'- [图 PDF](../analysis_exports/v2x_matched_epoch_trends_260917/matched_epoch_trends.pdf)',
'- [完整分类别验证 CSV](../analysis_exports/v2x_matched_epoch_trends_260917/all_validation_metrics.csv)',
'- [TaskDec 2×2 − Concat 差值 CSV](../analysis_exports/v2x_matched_epoch_trends_260917/taskdec2_minus_concat.csv)',
'- [L4DR 同轮 CSV](../analysis_exports/v2x_matched_epoch_trends_260917/l4dr_matched_epochs.csv)',
'- [原始结果路径及 SHA256](../analysis_exports/v2x_matched_epoch_trends_260917/sources.json)','',
'本次只读取既有验证结果并生成汇总，不改变训练、验证频次、选模规则或任何权重。','']
report=ROOT/'results/taskdec_v2x_matched_epoch_trends_260917.md'
report.write_text('\n'.join(text))
print(report)
print('Latest jointly evaluated epochs:',joint_t[-1],joint_l[-1])
