"""Read existing V2X evaluations; no model loading, inference, or GPU use."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
RUNS = [
    ('Concat', 'C+L+R', 'v2x_grid016_260918/matched_80ep/concat'),
    ('ASF-style', 'C+L+R', 'v2x_grid016_controls_260919/asf_clr_80ep/patch'),
    ('ObjDec', 'C+L+R', 'v2x_grid016_260918/matched_80ep/taskdec'),
    ('L4DR', 'L+R', 'v2x_l4dr_260917/matched_80ep/l4dr'),
    ('ObjDec-LR', 'L+R', 'v2x_grid016_controls_260919/objdec_lr_80ep/taskdec'),
]
sources, records, rows = {}, {}, []


def read(p):
    raw = p.read_bytes()
    sources[str(p)] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


def metric_row(name, sensors, kind, epoch, split, d):
    assert d['frames'] == (1487 if split == 'val_deduplicated' else 1486)
    m = d['metrics']
    row = dict(method=name, sensors=sensors, checkpoint=kind, epoch=epoch,
               split=split, frames=d['frames'])
    for metric in ['3D', 'BEV']:
        for cls in ['Vehicle', 'Pedestrian', 'Cyclist']:
            row[f'{metric}_{cls}'] = m[f'V2X/{cls}_{metric}_moderate_strict']
        row[f'{metric}_mean'] = m[f'V2X/Overall_{metric}_moderate']
        mean = sum(row[f'{metric}_{c}'] for c in ['Vehicle', 'Pedestrian', 'Cyclist']) / 3
        assert abs(mean - row[f'{metric}_mean']) < 1e-7
    rows.append(row)
    return row


for name, sensors, path in RUNS:
    p = ROOT / 'analysis_exports' / path
    status = read(p / 'status.json')
    item = records[name] = dict(sensors=sensors, path=str(p), status=status)
    epoch = status['best_epoch']
    val = read(p / f'val_epoch_{epoch:03d}.json')
    assert abs(val['selection_metric'] - status['best_metric']) < 1e-7
    item['val'] = metric_row(name, sensors, 'training_val_best', epoch, 'val_deduplicated', val)
    for kind in ['best', 'last']:
        src = p / f'final_{kind}.json'
        if not src.exists():
            continue
        d = read(src)
        if kind == 'best':
            assert d['epoch'] == epoch
        item[kind] = metric_row(name, sensors, kind, d['epoch'], 'test_deduplicated',
                                d['results']['test_deduplicated'])
        item[f'{kind}_checkpoint_sha256'] = d['checkpoint_sha256']

stamp = datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')
with (OUT / 'metrics.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
(OUT / 'snapshot.json').write_text(json.dumps(dict(captured_at=stamp, records=records,
    sources_sha256=sources), ensure_ascii=False, indent=2) + '\n')
text = ['# V2X-Radar-V 当前总表与训练进度', '', f'核查时间：{stamp}。', '',
        '## 1. 完成情况', '',
        '| 方法 | 模态 | 训练进度 | 当前best轮次 | 最终best/last测试 |',
        '| --- | --- | --- | --- | --- |']
for name, sensors, _ in RUNS:
    r = records[name]; s = r['status']
    progress = '80/80，已完成' if s['status'] == 'complete' else f"第{s['epoch']}/80轮，{s['step']}/{s['steps_per_epoch']} step"
    text.append(f"| {name} | {sensors} | {progress} | {s['best_epoch']} | {'已完成' if 'best' in r and 'last' in r else '待完成'} |")
complete = all(r['status']['status'] == 'complete' and 'best' in r and 'last' in r for r in records.values())
text += ['', '上述五组训练及best/last最终评测均已完成。此汇表脚本不查询其他项目的实时GPU占用。' if complete else '表内进度来自各运行的status.json，最终评测以final_best/final_last.json为准。', '',
         '## 2. 统一协议与最终测试表', '',
         '以下均为0.16 m网格、80轮训练预算，按去重验证集平均strict Moderate 3D AP选择best，再在1,486帧去重test评测。AP_R40，Vehicle/Pedestrian/Cyclist的IoU依次为0.7/0.5/0.5，Mean为三类等权平均。训练集8,391帧、去重val 1,487帧，有效batch为8。数值为百分数，差值为百分点。', '',
         '前三行为共同编码器和检测头下的C+L+R融合比较；后两行为保留原生网络差异的L+R架构比较。ASF-style是本地no-SCL适配。本地划分与ROI不同于公开论文基准，不据此直接声称超过公开榜单。', '']
for metric in ['3D', 'BEV']:
    text += [f'### {metric} AP_R40（best，test）', '',
             '| 方法 | 模态 | 选中轮次 | Vehicle | Pedestrian | Cyclist | Mean |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for name, sensors, _ in RUNS:
        r = records[name].get('best')
        cells = [name, sensors] + ([str(r['epoch'])] + [f'{r[f"{metric}_{c}"]:.2f}' for c in ['Vehicle', 'Pedestrian', 'Cyclist', 'mean']] if r else ['Pending'] * 5)
        text.append('| ' + ' | '.join(cells) + ' |')
    text += ['']
text += ['## 3. 末轮补充（test，不用于重新选模）', '',
         '| 方法 | 轮次 | Mean 3D | Mean BEV |', '| --- | --- | --- | --- |']
for name, _, _ in RUNS:
    r = records[name].get('last')
    if r:
        text.append(f"| {name} | {r['epoch']} | {r['3D_mean']:.2f} | {r['BEV_mean']:.2f} |")
text += ['', '## 4. 当前验证集候选（val，不能填入上述test表）', '',
         '| 方法 | 当前best轮次 | Val mean 3D | Val mean BEV |',
         '| --- | --- | --- | --- |']
for name, _, _ in RUNS:
    r = records[name]['val']
    text.append(f"| {name} | {r['epoch']} | {r['3D_mean']:.2f} | {r['BEV_mean']:.2f} |")
text += ['', '验证分数来自训练期val_epoch文件。最终重评的最后几位可能有数值波动；选模仍以训练期记录为准。', '',
         '## 5. 目前可得出的结论', '']
obj, concat = records['ObjDec']['best'], records['Concat']['best']
text.append(f"- ObjDec三模态最终best为第{obj['epoch']}轮，test平均3D/BEV为{obj['3D_mean']:.2f}/{obj['BEV_mean']:.2f}；相对Concat第{concat['epoch']}轮分别为{obj['3D_mean']-concat['3D_mean']:+.2f}/{obj['BEV_mean']-concat['BEV_mean']:+.2f}点，整体尚未超过Concat。")
text.append(f"- 分类别看，ObjDec的Cyclist 3D为{obj['3D_Cyclist']-concat['3D_Cyclist']:+.2f}点，Pedestrian/Cyclist BEV分别为{obj['BEV_Pedestrian']-concat['BEV_Pedestrian']:+.2f}/{obj['BEV_Cyclist']-concat['BEV_Cyclist']:+.2f}点；主要差距在Vehicle，以及Pedestrian 3D。")
lr, l4dr = records['ObjDec-LR']['val'], records['L4DR']['val']
text.append(f"- 验证集best对比，ObjDec-LR比L4DR高{lr['3D_mean']-l4dr['3D_mean']:.2f}点3D、{lr['BEV_mean']-l4dr['BEV_mean']:.2f}点BEV。此行为val结果。")
for ours, baseline in [('ObjDec-LR', 'L4DR'), ('ObjDec', 'ASF-style')]:
    a, b = records[ours].get('best'), records[baseline].get('best')
    if a and b:
        text.append(f"- 最终test同模态比较：{ours}（第{a['epoch']}轮）为{a['3D_mean']:.2f}/{a['BEV_mean']:.2f}，相对{baseline}（第{b['epoch']}轮）分别为{a['3D_mean']-b['3D_mean']:+.2f}/{a['BEV_mean']-b['BEV_mean']:+.2f}点3D/BEV。")
    else:
        text.append(f'- {ours}与{baseline}的最终test对比待补。')
text += ['- 第80轮结果作为附录补充；不能因其test略高而替换预先按val选择的best。', '',
         '## 6. 来源与复查', '',
         '[原始精度CSV](../analysis_exports/objdec_v2x_table_snapshot_260923/metrics.csv)；[状态、结果与来源SHA-256快照](../analysis_exports/objdec_v2x_table_snapshot_260923/snapshot.json)。汇总仅读取已有JSON，未启动模型或修改训练。', '']
for name, _, _ in RUNS:
    p = Path(records[name]['path'])
    text.append(f'- {name}：[运行目录]({p})；[status]({p}/status.json)' + (f'；[final_best]({p}/final_best.json)' if 'best' in records[name] else ''))
report = ROOT / 'results/objdec_v2x_current_total_table_260923.md'
report.write_text('\n'.join(text) + '\n')
print(f'Wrote {report}; {len(rows)} verified metric rows; {len(sources)} source files.')
