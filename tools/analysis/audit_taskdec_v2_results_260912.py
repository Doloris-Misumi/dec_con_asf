#!/usr/bin/env python3
"""Audit existing v2 results on CPU; no inference, checkpoints, or predictions copied."""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/taskdec_v2_existing_results_recheck_260912'
SUFFIX = '_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16'
RUNS = [
    ('DecControlled Gentle 08-06', 'exp_260806_000821_DecControlledASFGentle', 'none', 'exp_260806_000821_DecControlledASFGentle_final', False),
    ('DecControlled Strong 08-06', 'exp_260806_000825_DecControlledASFStrong', 'none', 'exp_260806_000825_DecControlledASFStrong_final', False),
    ('TaskDec Balanced 08-08', 'exp_260808_131759_TaskDecControlBalanced', 'none', 'exp_260808_131759_TaskDecControlBalanced_final', True),
    ('TaskDec Robust 08-08', 'exp_260808_131759_TaskDecControlRobust', 'none', 'exp_260808_131759_TaskDecControlRobust_final', True),
    ('TaskDec Robust 08-21 final', 'exp_260821_002150_TaskDecControlRobust_v2_0', 'none', 'exp_260821_002150_TaskDecControlRobust_v2_0_final', True),
    ('TaskDec Robust model_6', 'exp_260824_221613_TaskDecControlRobust_v2_0', 'epoch_6_total', None, True),
    ('TaskDec Robust model_8', 'exp_260824_221632_TaskDecControlRobust_v2_0', 'epoch_8_total', None, True),
    ('DecControlled Strong resume model_16', 'exp_260827_212019_DecControlledASFStrong_v2_0_resume20', 'epoch_16_total', None, False),
]
PAT = re.compile(r'Conf thr:\s*([\d.]+), Condition:\s*(\S+)\s*cls:\s*(\S+)\s*iou:\s*([^\n]+)\s*bev:\s*([^\n]+)\s*3d\s*:\s*([^\n]+)')
WEATHER = ['normal', 'overcast', 'fog', 'rain', 'sleet', 'lightsnow', 'heavysnow']
SELECTED = ['overcast', 'rain', 'lightsnow', 'heavysnow']


def parse(path):
    data = {}
    for conf, cond, cls, ious, bev, det in PAT.findall(path.read_text()):
        if conf != '0.3':
            continue
        assert cls not in data.setdefault(cond, {}), (path, cond, cls)
        data[cond][cls] = {'BEV': dict(zip(ious.split(), map(float, bev.split()))),
                           '3D': dict(zip(ious.split(), map(float, det.split())))}
    assert len(data) == 18 and all(set(v) == {'sed', 'bus'} for v in data.values()), path
    return data


def table(headers, rows):
    return ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] + [
        '| ' + ' | '.join(map(str, row)) + ' |' for row in rows]


def macro(data, metric, iou):
    return sum(data['all'][c][metric][iou] for c in ['sed', 'bus']) / 2


def main():
    base_dir = Path('/home/hongsheng/K-Radar-main/results/official_asf_v2_RLC')
    base_raw = base_dir / 'raw/complete_results_none_0.3.txt'
    base = parse(base_raw)
    assert base == json.loads((base_dir / 'summary_conf0.3.json').read_text())['0.3']
    data = {'ASF official RLC': base}
    provenance = [{'name': 'ASF official RLC', 'raw': str(base_raw), 'sha256': hashlib.sha256(base_raw.read_bytes()).hexdigest()}]
    counts = {}
    reference_names = None
    checked = 216
    for label, exp, epoch, archive, context in RUNS:
        log = ROOT / 'logs' / (exp + SUFFIX)
        folder = log / 'test_kitti' / epoch / '0.3'
        raw = folder / 'complete_results.txt'
        values = parse(raw)
        if archive:
            assert values == json.loads((ROOT / 'results' / archive / 'summary_conf0.3.json').read_text())['0.3'], label
            checked += 216
        cfg = (log / 'config.yml').read_text()
        assert ('NAME: TaskAwareDecControlledA2Fusion' in cfg) == context, label
        names = {p.name for p in (folder / 'all/preds').iterdir() if p.suffix == '.txt'}
        assert len(names) == 13727, (label, len(names))
        if reference_names is None:
            reference_names = names
        assert names == reference_names, label
        counts[label] = {w: len(list((folder / w / 'preds').glob('*.txt'))) for w in WEATHER}
        data[label] = values
        provenance.append({'name': label, 'raw': str(raw), 'config': str(log / 'config.yml'),
                           'has_task_context': context, 'prediction_files': len(names),
                           'sha256': hashlib.sha256(raw.read_bytes()).hexdigest()})
    assert all(v == next(iter(counts.values())) for v in counts.values())
    rows = []
    for name, values in data.items():
        for cond in values:
            for cls in ['sed', 'bus']:
                for metric in ['3D', 'BEV']:
                    for iou in ['0.3', '0.5', '0.7']:
                        val = values[cond][cls][metric][iou]
                        rows.append([name, cond, cls, metric, iou, val, base[cond][cls][metric][iou], val - base[cond][cls][metric][iou]])
    md = ['# TaskDec：现有 K-Radar v2.0 结果复核（2026-09-12）', '',
          '依据作者讨论后的新方向：可能撤下 VoD 表，先复核 v2.0 数据；本记录不将该倾向视为已确定删除 VoD 材料。', '',
          '本轮读取原始结果文本、归档 JSON 和配置，重新计算差值；没有运行 GPU 推理或训练。比较对象为现有官方 ASF v2 RLC 结果，不是所有文献方法的排名。', '',
          '**核心发现：早期 DecControlled Strong 的两类平均 AP3D@0.3 / @0.5 分别比 ASF 高 0.36 / 1.48 点。另有此前推荐表未列出的 TaskDec Robust 08-08：含 task context，AP3D@0.5 高 1.76 点，但 AP3D@0.3 低 1.95 点。08-21 final 及 model_6/model_8 也纳入核对，不能仅用 final 一次结果概括整个 TaskDec v2 系列。**', '',
          '口径：C+L+R、label v2_0、宽 ROI [0,-16,-2,72,16,7.6]、Sedan 与 Bus/Truck、conf_thr=0.3。下文平均值均为两类 AP 的算术平均，单位为 AP 百分点；先用原始精度计算，最后保留两位小数。', '',
          '## 1. 所有已找到的 DecControlled / TaskDec 全量比较', '']
    total_rows = []
    for name, v in data.items():
        a, b = macro(v, '3D', '0.3'), macro(v, '3D', '0.5')
        total_rows.append([name, f'{a:.2f}', f'{a-macro(base,"3D","0.3"):+.2f}', f'{b:.2f}', f'{b-macro(base,"3D","0.5"):+.2f}'])
    md += table(['运行', '两类平均 3D@0.3', 'Δ ASF', '两类平均 3D@0.5', 'Δ ASF'], total_rows)
    focus = ['ASF official RLC', 'DecControlled Strong 08-06', 'TaskDec Robust 08-08', 'TaskDec Robust 08-21 final']
    md += ['', '## 2. 重点版本的全量分类别指标', '']
    detailed = []
    for name in focus:
        for c in ['sed', 'bus']:
            vals = []
            for metric, iou in [('3D','0.3'),('3D','0.5'),('3D','0.7'),('BEV','0.3'),('BEV','0.5'),('BEV','0.7')]:
                v = data[name]['all'][c][metric][iou]
                delta = v - base['all'][c][metric][iou]
                vals.append(f'{v:.2f} ({delta:+.2f})' if name != focus[0] else f'{v:.2f}')
            detailed.append([name, c] + vals)
    md += table(['运行','类别','3D@0.3','3D@0.5','3D@0.7','BEV@0.3','BEV@0.5','BEV@0.7'], detailed)
    md += ['', '## 3. 全天气 AP3D@0.5：保留正负结果', '',
           '格式为 AP（相对 ASF 的差值）。天气帧数是我们各运行目录的预测文件数，不是该类 GT 目标数。Fog 的 Bus/Truck AP 在这些结果中均为 0；本轮没有据此推断该天气没有该类 GT，也不把 0→0 算作收益。', '']
    weather_counts = next(iter(counts.values()))
    for c in ['sed','bus']:
        md += [f'### {c}', '']
        weather_rows = []
        for w in WEATHER:
            vals = [w, weather_counts[w], f'{base[w][c]["3D"]["0.5"]:.2f}']
            for name in focus[1:]:
                v = data[name][w][c]['3D']['0.5']
                vals.append(f'{v:.2f} ({v-base[w][c]["3D"]["0.5"]:+.2f})')
            weather_rows.append(vals)
        md += table(['天气','帧数','ASF','DecControlled Strong','TaskDec Robust 08-08','TaskDec Robust 08-21'],weather_rows) + ['']
    md += ['原推荐表 selected-weather 仅包含 Overcast、Rain、Light snow、Heavy snow，不能称为全部恶劣天气，也不等于 Total AP。该四项平均的精确复算如下：', '']
    selected_rows = []
    for name in focus:
        vals = []
        for c in ['sed','bus']:
            v = sum(data[name][w][c]['3D']['0.5'] for w in SELECTED) / 4
            b = sum(base[w][c]['3D']['0.5'] for w in SELECTED) / 4
            vals.append(f'{v:.2f} ({v-b:+.2f})')
        selected_rows.append([name] + vals)
    md += table(['运行','Sedan 四天气平均','Bus/Truck 四天气平均'],selected_rows)
    md += ['', '## 4. 模型身份、可比性与写作判断', '',
           '- DecControlled Gentle / Strong / resume 使用 DecControlledA2Fusion，没有 task-context 分支。TaskDec Balanced / Robust 使用 TaskAwareDecControlledA2Fusion，包含任务上下文；不能将所有早期运行都称为“没有 task context”。',
           '- 08-08 Robust 与 08-21 Robust 的配置不完全相同，例如 DEC_CONTROL_CLASS_POS_WEIGHT_MAX 分别为 12 和 4，且基础配置不同。这些跨运行差异不能解释为单一组件的因果效应。',
           '- 本轮找到的 8 份全量条件评测，每份 all/preds 均为 13,727 个文件，文件名集合一致，全天气帧数也一致；这核查了目录覆盖范围，未逐文件比较 GT 内容。1000 样本的 subset 扫描未混入全量表。',
           f'- 原始文本与 5 份已有运行 JSON 及 ASF JSON 完全相符，共核对 {checked} 个 AP 值。ASF 数值来自现有官方结果归档，本轮未重跑 ASF 或另行核验其逐帧预测。',
           '- 如果撤下 VoD，v2 可提供同数据集内更宽 ROI、修订标签与额外类别的扩展证据，但不承担跨数据集泛化结论。',
           '- 若使用完整任务控制架构的 v2 结果，应同时报告其 AP3D@0.3 与 BEV 退化；不能把不同运行按列拼成一条 Ours。若沿用 DecControlled Strong，保留 early variant 表注。',
           '- 建议以全量两类结果为主，全天气结果为补充。原推荐表四天气均值有正收益，但不能用它代替全量表现。现有数据支持严格 IoU 下的部分 3D 收益，不支持 v2 全指标领先。', '',
           '## 5. 源文件与复现', '']
    for p in provenance:
        md += [f'- **{p["name"]}**：[原始结果]({p["raw"]})' + (f'；[配置]({p["config"]})' if 'config' in p else '')]
    md += ['', '复现脚本：[audit_taskdec_v2_results_260912.py](../tools/analysis/audit_taskdec_v2_results_260912.py)。同名 CSV 保存全部 18 个条件、两类、六个指标的原始数值及差值；sources.json 保存输入路径和摘要。', '']
    OUT.with_suffix('.md').write_text('\n'.join(md))
    with OUT.with_suffix('.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['run','condition','class','metric','iou','ap','asf_ap','delta_pp'])
        writer.writerows(rows)
    OUT.with_suffix('.sources.json').write_text(json.dumps({'sources':provenance,'summary_values_checked':checked,'weather_frame_counts':weather_counts,'csv_rows':len(rows)},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'report':str(OUT.with_suffix('.md')),'runs_including_asf':len(data),'csv_rows':len(rows),'summary_values_checked':checked,'bytes':sum(p.stat().st_size for p in OUT.parent.glob(OUT.name+'.*'))},ensure_ascii=False))


if __name__ == '__main__':
    main()
