"""Read-only collection of completed Concat validations and final evaluations."""
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
RUN = BASE / 'controlled_80ep/concat'
OUT = BASE / 'concat80_collection'
CLASSES = ['Vehicle', 'Pedestrian', 'Cyclist']


def read(path):
    return json.loads(path.read_text())


def main():
    OUT.mkdir(exist_ok=True)
    at = datetime.now().astimezone().isoformat()
    history = [read(p) for p in sorted(RUN.glob('val_epoch_*.json'))]
    best = max(history, key=lambda v: (v['selection_metric'], -v['epoch']))
    last = next(v for v in history if v['epoch'] == 80)
    finals = {tag: read(RUN / ('final_' + tag + '.json'))
              for tag in ['best', 'last'] if (RUN / ('final_' + tag + '.json')).exists()}
    sources = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(RUN.glob('val_epoch_*.json')) + sorted(RUN.glob('final_*.json'))}
    summary = dict(collected_at=at, status=read(RUN / 'status.json'),
                   best_validation=best, epoch80_validation=last,
                   validation_history=history, completed_final_evaluations=finals, source_sha256=sources)
    (OUT / 'results.json').write_text(json.dumps(summary, indent=2))
    with open(OUT / 'validation_trend.csv', 'w') as stream:
        writer = csv.writer(stream)
        writer.writerow(['epoch'] + CLASSES + ['mean_3d_strict_moderate', 'mean_bev_strict_moderate'])
        for v in history:
            m = v['metrics']
            writer.writerow([v['epoch']] + [m['V2X/' + c + '_3D_moderate_strict'] for c in CLASSES]
                            + [v['selection_metric'], m['V2X/Overall_BEV_moderate']])
    lines = ['# Concat 80 轮验证结果收集', '', '收集时间：' + at, '',
             '口径：本地 C+L+R，1487 帧去重 validation，AP_R40。严格 IoU 为 Vehicle 0.7 / Pedestrian 0.5 / Cyclist 0.5；宽松 IoU 为 0.5 / 0.25 / 0.25。沿用原训练的 ROI、Vehicle 合类及 KITTI 难度规则。', '',
             '**80轮训练及第80轮完整验证已完成；以完整验证结果选择的 best 仍为第%d轮。**' % best['epoch'], '',
             '| 轮次 | Vehicle | Pedestrian | Cyclist | 平均 3D | 平均 BEV |',
             '|---|---:|---:|---:|---:|---:|']
    for v in history:
        m = v['metrics']
        vals = [m['V2X/' + c + '_3D_moderate_strict'] for c in CLASSES] + [v['selection_metric'], m['V2X/Overall_BEV_moderate']]
        lines.append('| %d | %s |' % (v['epoch'], ' | '.join('%.2f' % x for x in vals)))
    delta = last['selection_metric'] - best['selection_metric']
    lines.extend(['', '以上为严格 IoU / Moderate。第80轮平均3D相对best变化 %.4f 个百分点，后期已趋于平台；报告best=%d和last=80，不能将80轮说成最佳。' % (delta, best['epoch']), '',
                  '## 第80轮完整分类结果', '', '| 类别 / IoU | 3D Easy | 3D Mod. | 3D Hard | BEV Easy | BEV Mod. | BEV Hard |',
                  '|---|---:|---:|---:|---:|---:|---:|'])
    for c in CLASSES:
        for threshold in ['strict', 'loose']:
            vals = [last['metrics']['V2X/' + c + '_' + metric + '_' + diff + '_' + threshold]
                    for metric in ['3D', 'BEV'] for diff in ['easy', 'moderate', 'hard']]
            lines.append('| %s / %s | %s |' % (c, threshold, ' | '.join('%.2f' % x for x in vals)))
    lines.extend(['', '## 最终 best / last 复评进度', '', '训练进程状态：`' + summary['status']['status'] + '`。'])
    for tag in ['best', 'last']:
        if tag not in finals:
            lines.append('- `%s`：完整最终报告尚未落盘，不把验证结果当作测试结果。' % tag)
            continue
        report = finals[tag]
        lines.extend(['', '**%s，epoch %d**' % (tag, report['epoch']), '',
                      '| 划分 | 帧数 | Vehicle | Pedestrian | Cyclist | 平均3D |',
                      '|---|---:|---:|---:|---:|---:|'])
        for split, result in report['results'].items():
            vals = [result['metrics']['V2X/' + c + '_3D_moderate_strict'] for c in CLASSES] + [result['selection_metric']]
            lines.append('| %s | %d | %s |' % (split, result['frames'], ' | '.join('%.2f' % x for x in vals)))
    lines.extend(['', '选模仅使用去重val严格IoU / Moderate平均3D，test不参与选择。原始val/test和去重val/test分开记录。', '',
                  '完整指标与来源SHA：`analysis_exports/v2x_taskdec_260916/concat80_collection/results.json`；',
                  '全部验证趋势：同目录 `validation_trend.csv`。', '',
                  '刷新本报告：`python3 analysis_exports/v2x_taskdec_260916/collect_concat80.py`。'])
    target = ROOT / 'results/taskdec_v2x_concat80_results_260917.md'
    target.write_text('\n'.join(lines) + '\n')
    print(json.dumps(dict(report=str(target), epoch80=last['selection_metric'],
                          best_epoch=best['epoch'], best_metric=best['selection_metric'],
                          final_completed=list(finals)), ensure_ascii=False))


if __name__ == '__main__':
    main()
