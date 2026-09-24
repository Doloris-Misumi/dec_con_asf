#!/usr/bin/env python3
"""Export all archived Strong-vs-ASF AP values; CPU only, no prediction copies."""
import csv
import hashlib
import json
from pathlib import Path

from audit_taskdec_v2_results_260912 import parse, table

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/paper_kradar_v2_decstrong_asf_comparison_260912'
NAME = 'DecControlled Strong 08-06'
BASE = Path('/home/hongsheng/K-Radar-main/results/official_asf_v2_RLC/raw/complete_results_none_0.3.txt')
LOG = ROOT / 'logs/exp_260806_000825_DecControlledASFStrong_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16'
RAW = LOG / 'test_kitti/none/0.3/complete_results.txt'
METRICS = [(m, i) for m in ('3D', 'BEV') for i in ('0.3', '0.5', '0.7')]
COND = ['all', 'normal', 'overcast', 'fog', 'rain', 'sleet', 'lightsnow', 'heavysnow',
        'day', 'night', 'urban', 'highway', 'countryside', 'alleyway', 'parkinglots',
        'shoulder', 'mountain', 'university']


def main():
    base, ours = parse(BASE), parse(RAW)
    assert set(base) == set(ours) == set(COND)
    assert 'NAME: DecControlledA2Fusion' in (LOG / 'config.yml').read_text()
    archive = ROOT / 'results/exp_260806_000825_DecControlledASFStrong_final/summary_conf0.3.json'
    assert ours == json.loads(archive.read_text())['0.3']
    prior = list(csv.DictReader((ROOT / 'results/taskdec_v2_existing_results_recheck_260912.csv').open()))
    checks = [r for r in prior if r['run'] in (NAME, 'ASF official RLC')]
    assert len(checks) == 432
    for r in checks:
        source = ours if r['run'] == NAME else base
        assert float(r['ap']) == source[r['condition']][r['class']][r['metric']][r['iou']]
    def val(data, cond, cls, metric, iou):
        if cls == 'mean':
            return sum(data[cond][c][metric][iou] for c in ('sed', 'bus')) / 2
        return data[cond][cls][metric][iou]
    rows = []
    for cond in COND:
        for cls in ('sed', 'bus'):
            for metric, iou in METRICS:
                a, b = val(base, cond, cls, metric, iou), val(ours, cond, cls, metric, iou)
                rows.append([cond, cls, metric, iou, a, b, b-a])
    assert len(rows) == 216
    with OUT.with_suffix('.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['condition', 'class', 'metric', 'iou', 'asf_ap', 'decstrong_ap', 'delta_pp'])
        writer.writerows(rows)
    md = ['# DecControlled Strong：K-Radar v2 完整结果与 ASF 对照', '',
          '日期：2026-09-12。依据作者本轮决定，v2 表采用 DecControlled Strong 08-06 的现有全量结果；v2 用于跨设置扩展，缺模态分析保留 v1。', '',
          '表名建议：**DecControlled Strong (ours)**。正文可称“我们提出的 Dec 方法家族”，表注说明 Strong 不含 task-context 分支。这不是完整 TaskDec 架构未经修改迁移到 v2 的结果。', '',
          '协议：C+L+R、label v2_0、ROI [0,−16,−2,72,16,7.6]、Sedan 与 Bus/Truck、conf_thr=0.3。ASF 使用现有官方 checkpoint 的结果归档。Strong 的 all/preds 有 13,727 个预测文件（此前已核验）；该帧数是过滤后的现有评测输出，不能直接与文献的原始 split 帧数互换。', '',
          '本轮重新读取两份原始文本，对照既有审计 CSV 核验 432 个 AP；没有运行 GPU 推理或训练。AP 以百分数表示，差值单位为 AP 点，先按原始精度计算再舍入。', '',
          '## 1. 全量 Total：六项指标', '',
          'Strong 单元格格式为 AP（相对 ASF 的差值）。两类均值是类别 AP 的算术平均，不是天气均值或按样本数加权值。', '']
    overall = []
    for cls, label in [('sed', 'Sedan'), ('bus', 'Bus/Truck'), ('mean', '两类均值')]:
        for name, data in [('ASF official', base), ('DecControlled Strong', ours)]:
            vals = []
            for metric, iou in METRICS:
                b = val(data, 'all', cls, metric, iou)
                a = val(base, 'all', cls, metric, iou)
                vals.append(f'{b:.2f}' if data is base else f'{b:.2f} ({b-a:+.2f})')
            overall.append([name, label] + vals)
    md += table(['方法', '类别'] + [f'{m}@{i}' for m,i in METRICS], overall)
    md += ['', '结果含义：两类平均 3D@0.3 / @0.5 / @0.7 分别提高 0.36 / 1.48 / 1.22 点；BEV@0.3 / @0.5 分别降低 1.62 / 1.53 点，BEV@0.7 提高 1.66 点。现有结果支持部分 3D 指标收益，不支持全指标领先。', '',
           '## 2. 正文紧凑表草案', '',
           '该表直接对应“宽 ROI / 双类别设置扩展”。其他论文的数字与协议见[文献候选与对照表](kradar_v2_literature_candidates_260912.md)，不能用 ASF 论文公开值替换以下同阈值基线。', '']
    compact = []
    for name, data in [('ASF official, conf=0.3',base), ('DecControlled Strong (ours), conf=0.3',ours)]:
        compact.append([name, 'C+L+R'] + [f'{val(data,"all",c,"3D",i):.2f}' for i in ('0.3','0.5') for c in ('sed','bus','mean')])
    md += table(['方法','输入','3D@0.3 Sedan','Bus/Truck','均值','3D@0.5 Sedan','Bus/Truck','均值'],compact)
    md += ['', '英文表注：Results on K-Radar benchmark v2.0 with C+L+R inputs and a score threshold of 0.3. DecControlled Strong is a variant of our Dec family without task-context modulation. Mean denotes the arithmetic mean of the two class APs. The ASF row uses archived results from its released official checkpoint.', '',
           '可用中文描述：在 K-Radar v2.0 的宽 ROI 和双类别设置下，Dec 家族的 DecControlled Strong 变体相对官方 ASF 在两类平均 AP3D@0.3 和 AP3D@0.5 上分别提高 0.36 和 1.48 点，表明解耦控制机制在扩展设置下仍可带来检测收益。该实验使用不含 task-context 分支的变体，BEV 指标与完整条件结果见附录。', '',
           '## 3. 全部 18 个条件、两类、六项指标', '',
           '以下保留所有正负结果。all 是整个评测集直接计算的 AP；道路、昼夜、天气属于不同划分，不能相加或跨组求平均替代 Total。0.00 按日志原值保留，未据此推断没有 GT 或评测失败。', '']
    for metric, iou in METRICS:
        md += [f'### {metric}@{iou}', '']
        full = []
        for cond in COND:
            vals = []
            for c in ('sed','bus'):
                a,b = val(base,cond,c,metric,iou),val(ours,cond,c,metric,iou)
                vals.extend([f'{a:.2f}',f'{b:.2f}',f'{b-a:+.2f}'])
            full.append([cond]+vals)
        md += table(['条件','ASF Sedan','Strong Sedan','Δ Sedan','ASF Bus/Truck','Strong Bus/Truck','Δ Bus/Truck'],full) + ['']
    md += ['## 4. 文献扩展与来源', '',
           '已整理 ASF、WRCFormer、REL 及其 InterFusion/3D-LRF/L4DR 基线、L4DR 原论文、V2X-R 的 MDD，以及 DPFT、SRF、DinoRADE/RADE-Net。文献表包含可获取的分类别数字、精确来源和入表限制：[完整文献表](kradar_v2_literature_candidates_260912.md)。', '',
           '特别注意：REL 报告的 3D@0.5 两类均值为 46.50，REL with L4DR 为 47.00，数值高于本表 Strong 的 43.05。由于仍有协议细节未对齐，不据此声称严格同协议排名；但本表也不能宣称全面超越已有 v2 方法。', '',
           f'- [Strong 原始完整结果]({RAW})', f'- [Strong 配置]({LOG / "config.yml"})',
           f'- [ASF 原始完整结果]({BASE})',
           '- [全部 8 个已有 v2 运行的审计](taskdec_v2_existing_results_recheck_260912.md)',
           '- [216 组原始精度比较 CSV](paper_kradar_v2_decstrong_asf_comparison_260912.csv)',
           '- [紧凑表 LaTeX](paper_kradar_v2_decstrong_asf_comparison_260912.tex)',
           '- [生成脚本](../tools/analysis/export_decstrong_v2_comparison_260912.py)', '']
    OUT.with_suffix('.md').write_text('\n'.join(md))
    tex = [r'\begin{table}[t]',r'\centering',r'\small',
           r'\caption{Extension to K-Radar benchmark v2.0 with C+L+R inputs and score threshold 0.3. Strong is a Dec-family variant without task-context modulation. Mean is the arithmetic mean of the two class APs. ASF uses archived results from the released official checkpoint.}',
           r'\label{tab:kradar_v2_decstrong}',r'\begin{tabular}{lrrrrrr}',r'\toprule',
           r'& \multicolumn{3}{c}{AP$_{\rm 3D}$@0.3} & \multicolumn{3}{c}{AP$_{\rm 3D}$@0.5} \\',
           r'Method & Sedan & Bus/Truck & Mean & Sedan & Bus/Truck & Mean \\',r'\midrule']
    for name,data in [('ASF (official)',base),('DecControlled Strong (ours)',ours)]:
        values=[f'{val(data,"all",c,"3D",i):.2f}' for i in ('0.3','0.5') for c in ('sed','bus','mean')]
        tex.append(name+' & '+' & '.join(values)+r' \\')
    tex += [r'\bottomrule',r'\end{tabular}',r'\end{table}','']
    OUT.with_suffix('.tex').write_text('\n'.join(tex))
    provenance = {'compared_values':432,'comparison_rows':216,'conditions':COND,
                  'sources':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (RAW,BASE,LOG/'config.yml',archive)],
                  'model':'DecControlledA2Fusion','task_context':False,'confidence_threshold':0.3}
    OUT.with_suffix('.sources.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'report':str(OUT.with_suffix('.md')),'comparison_rows':len(rows),'checked_values':len(checks),'output_bytes':sum(p.stat().st_size for p in OUT.parent.glob(OUT.name+'.*'))},ensure_ascii=False))


if __name__ == '__main__':
    main()
