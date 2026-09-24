#!/usr/bin/env python3
"""Arrange existing AP values like L4DR Table 10; no model execution."""
import csv
from collections import Counter
from pathlib import Path

from audit_taskdec_v2_results_260912 import table
from export_decstrong_v2_comparison_260912 import ROOT, LOG, RAW, BASE, parse

OUT = ROOT / 'results/paper_kradar_v2_weather_l4dr_table10_260912'
CONDITIONS = ['all', 'normal', 'lightsnow', 'heavysnow', 'rain', 'sleet', 'overcast', 'fog']
CN = ['Total', '正常', '小雪', '大雪', '雨', '雨夹雪', '阴天', '雾']
EN = ['Total', 'Normal', 'Li. Snow', 'He. Snow', 'Rain', 'Sleet', 'Overcast', 'Fog']
SOURCE = 'https://arxiv.org/html/2408.03677v6'
AUDIT = 'taskdec_v2_l4dr_weather_total_and_eval_protocol_audit_260912.md'
# Published values only; do not relabel these as a local, aligned re-evaluation.
L4DR = {
    'sed': dict(zip(CONDITIONS, [75.8, 74.6, 87.5, 58.4, 77.8, 61.4, 79.2, 89.3])),
    'bus': dict(zip(CONDITIONS, [59.7, 59.4, 84.4, 51.9, 8.1, 66.1, 86.4, None])),
}


def main():
    base, ours = parse(BASE), parse(RAW)
    lookup = {(r['condition'], r['class'], r['iou']): r for r in csv.DictReader(
        (ROOT / 'results/paper_kradar_v2_decstrong_asf_comparison_260912.csv').open()) if r['metric'] == '3D'}
    gt = {}
    for cond in CONDITIONS[1:]:
        files = sorted((LOG / 'test_kitti/none/0.3' / cond / 'gts').glob('*.txt'))
        assert files, cond
        counts = Counter(line.split()[0] for f in files for line in f.read_text().splitlines() if line.strip())
        gt[cond] = {'frames':len(files), 'sed':counts['sed'], 'bus':counts['bus']}
    assert gt['fog']['frames'] == 1445 and gt['fog']['bus'] == 0
    def cell(data, cond, cls, iou):
        if cond == 'fog' and cls == 'bus':
            assert data[cond][cls]['3D'][iou] == 0
            return '—'
        return f"{data[cond][cls]['3D'][iou]:.2f}"
    md = ['# K-Radar v2：参照 L4DR Table 10 的全天气表', '',
          '日期：2026-09-12。按作者最新建议，附录天气表直接纳入 L4DR 论文行，与官方 ASF 及 DecControlled Strong 并列展示；文献结果用 † 区分。', '',
          f'布局参照 [L4DR arXiv v6 Table 10]({SOURCE})：Class / Method / Modality / Total / Normal / Light snow / Heavy snow / Rain / Sleet / Overcast / Fog。原表使用 AP3D@0.3；这里另提供同样版式的 AP3D@0.5。', '',
          '本地对比协议：label v2_0，宽 ROI [0,−16,−2,72,16,7.6]，C+L+R，conf_thr=0.3，使用 ASF revised evaluator（41 个 precision 采样值平均、z_center=0.5）。Strong 指 DecControlled Strong 08-06，是不含 task-context 分支的 Dec 方法家族变体。', '',
          f'† L4DR 来自论文 Table 10，输入 L+R。其公开代码使用旧评测器（41 点网格取 11 个 precision 值平均、z_center=1.0），当前公开配置使用 label v2_1；尚未确认该论文表的完整运行协议。数值可并列对照，但不能视为已统一评测器的排名。详见 [本轮协议与 Total 审计]({AUDIT})。', '',
          'Total 是整个评测集直接计算的 AP，不是七种天气 AP 的平均。Fog 的 Bus/Truck 记为“—”：本轮检查该运行 1,445 个 Fog GT 文件，没有该类 GT；原日志中的 0.00 在 CSV 中保留。表内不对无 GT 单元格计算收益。', '']
    tex, export_rows = [], []
    for iou in ('0.3','0.5'):
        md += [f'## AP3D@{iou}', '']
        rows = []
        for cls, label in [('sed','Sedan'),('bus','Bus/Truck')]:
            if iou == '0.3':
                rows.append([label,'L4DR (paper) †','L+R']+[
                    '—' if L4DR[cls][c] is None else f'{L4DR[cls][c]:.1f}' for c in CONDITIONS])
            for name, data in [('ASF official',base),('DecControlled Strong (ours)',ours)]:
                rows.append([label,name,'C+L+R']+[cell(data,c,cls,iou) for c in CONDITIONS])
        md += table(['类别','方法','模态']+CN,rows)+['']
        delta_rows = []
        for cls,label in [('sed','Sedan'),('bus','Bus/Truck')]:
            values = []
            for cond in CONDITIONS:
                a,b = base[cond][cls]['3D'][iou],ours[cond][cls]['3D'][iou]
                old = lookup[(cond,cls,iou)]
                assert float(old['asf_ap']) == a and float(old['decstrong_ap']) == b
                values.append('—' if cond=='fog' and cls=='bus' else f'{b-a:+.2f}')
                export_rows.append([cond,cls,'3D',iou,a,b,b-a,not(cond=='fog' and cls=='bus')])
            delta_rows.append([label]+values)
        md += ['Strong − ASF（AP 点，按原始精度计算）：','']+table(['类别']+CN,delta_rows)+['']
        if iou == '0.3':
            literature_delta = [[label]+[
                '—' if L4DR[cls][c] is None else f"{ours[c][cls]['3D'][iou]-L4DR[cls][c]:+.2f}"
                for c in CONDITIONS] for cls,label in [('sed','Sedan'),('bus','Bus/Truck')]]
            md += ['Strong − L4DR 论文值（仅数值差，尚未统一评测器；L4DR 原表精度为一位小数）：','']
            md += table(['类别']+CN,literature_delta)+['']
        literature_note = (r' L4DR$^{\dagger}$ is quoted from Table 10 of the L4DR paper (arXiv:2408.03677v6), with L+R inputs. Its public code uses 11 selected precision samples and z\_center=1.0, whereas our ASF-based evaluation uses all 41 samples and z\_center=0.5. The published row is not an aligned re-evaluation.' if iou == '0.3' else '')
        dash_note = ' A dash denotes no evaluated Bus/Truck ground truth in fog for our setting.'
        if iou == '0.3':
            dash_note += ' The L4DR dash is retained as published.'
        tex += [r'\begin{table*}[t]',r'\centering',r'\small',r'\setlength{\tabcolsep}{3pt}',
                r'\caption{Weather-wise results on K-Radar benchmark v2.0. AP$_{\rm 3D}$ at IoU='+iou+r' is reported. ASF and DecControlled Strong use C+L+R inputs, score threshold 0.3, and the revised evaluator. Strong is a Dec-family variant without task-context modulation. Total is evaluated on the full evaluation set.'+dash_note+literature_note+r'}',
                r'\label{tab:kradar_v2_weather_'+iou.replace('.','')+r'}',
                r'\resizebox{\linewidth}{!}{%',
                r'\begin{tabular}{lllrrrrrrrr}',r'\toprule',
                'Class & Method & Mod. & '+' & '.join(EN)+r' \\',r'\midrule']
        for cls,label in [('sed','Sedan'),('bus','Bus/Truck')]:
            if cls=='bus':
                tex.append(r'\midrule')
            if iou == '0.3':
                vals = ['--' if L4DR[cls][c] is None else f'{L4DR[cls][c]:.1f}' for c in CONDITIONS]
                tex.append(' & '.join([label,r'L4DR (paper)$^{\dagger}$','LR']+vals)+r' \\')
            for name,data in [('ASF (official)',base),('DecControlled Strong (ours)',ours)]:
                vals=[cell(data,c,cls,iou).replace('—','--') for c in CONDITIONS]
                tex.append(' & '.join([label,name,'CLR']+vals)+r' \\')
        tex += [r'\bottomrule',r'\end{tabular}',r'}',r'\end{table*}','']
    md += ['## 天气等权平均与 Total 的区别', '',
           '以下均为 AP3D@0.3。天气均值是复算的诊断统计，不替代基准 Total；Bus/Truck 排除无 GT 的 Fog。跨方法数字仍受上述协议差异限制。', '']
    mean_rows = []
    for cls,label in [('sed','Sedan'),('bus','Bus/Truck')]:
        valid = [c for c in CONDITIONS[1:] if L4DR[cls][c] is not None]
        a = sum(L4DR[cls][c] for c in valid)/len(valid)
        b = sum(ours[c][cls]['3D']['0.3'] for c in valid)/len(valid)
        mean_rows.append([label,f'天气等权平均（{len(valid)} 类天气）',f'{a:.2f}',f'{b:.2f}',f'{b-a:+.2f}'])
        a,b = L4DR[cls]['all'],ours['all'][cls]['3D']['0.3']
        mean_rows.append([label,'全评测集 Total',f'{a:.2f}',f'{b:.2f}',f'{b-a:+.2f}'])
    md += table(['类别','统计','L4DR 论文','Strong','数值差'],mean_rows)+['',
           'Total 合并全部帧的检测和 GT、汇总阈值下的 TP/FP/FN 后计算 PR/AP，既不是天气 AP 的等权平均，也不能用天气 AP 按帧数或 GT 数加权精确还原。当前 Sedan GT 的 53.99% 在 Normal、20.19% 在 Rain；Strong 在这两组分别比论文值低 1.09、9.69 点，有助于理解为何多数天气更高不等于 Total 更高，但不能据此量化协议影响。', '',
           f'来源：[L4DR Table 10]({SOURCE})；[官方 v2.1 配置](https://github.com/ylwhxht/L4DR/blob/main/K-Radar-main-repo/configs/cfg_PP_L4DR.yml)。其他方法及其协议见 [v2 文献清单](kradar_v2_literature_candidates_260912.md)。', '',
           '## 读表与附录安排', '',
           '- @0.3：相对 ASF，Strong 的 Bus/Truck 在雨、小雪、大雪下分别提高 2.19、1.30、4.14 点；正常、阴天、雨夹雪下降。Sedan 在阴天、雾、雨、雨夹雪、小雪下提高，正常与大雪略降。',
           '- @0.5 给出更严格定位结果：Bus/Truck 在雨、小雪、大雪下分别提高 2.57、4.28、6.82 点；Sedan 在阴天和雨夹雪下提高 6.25、5.08 点，但正常与雾略降，Bus/Truck 的雨夹雪也略降。',
           '- 根据最新讨论，完整天气表作为附表：@0.3 面板含 L4DR、ASF、Strong，共 6 个方法行；@0.5 面板保留 ASF、Strong，共 4 行。L4DR Table 10 没有 @0.5 天气值，不从其他表或论文拼接补齐。正文可保留 Total 紧凑表。',
           '- 相对 L4DR 论文，Strong 的 Sedan 在 5/7 种天气数值更高，但 Total 低 1.22 点；Bus/Truck 在 3/6 种有效天气更高，Total 低 0.46 点。不能概括成各项均优，也不按不同评测器的数字标统一最优。',
           '- v2 的结论仍是宽 ROI / 双类别设置下的扩展有效性，天气列进一步展示收益出现在哪些条件中。缺模态鲁棒性仍由 v1 的独立实验承担。', '',
           '## 本轮 GT 计数核验', '',
           '计数来自 Strong 运行各天气 gts 目录中导出的评测 GT，表示当前过滤设置下的目标数，不是数据集未经筛选的全部标注。', '']
    md += table(['天气','帧数','Sedan GT','Bus/Truck GT'],[[c,gt[c]['frames'],gt[c]['sed'],gt[c]['bus']] for c in CONDITIONS[1:]])
    md += ['',f'- [Strong 原始结果]({RAW})',f'- [ASF 原始结果]({BASE})',
           '- [完整 18 条件、两类、六项指标](paper_kradar_v2_decstrong_asf_comparison_260912.md)',
           '- [本表 CSV](paper_kradar_v2_weather_l4dr_table10_260912.csv)',
           '- [L4DR 文献数值对照 CSV](paper_kradar_v2_weather_l4dr_table10_260912.l4dr_reference.csv)',
           f'- [Total 与评测协议审计]({AUDIT})',
           '- [两个 IoU 版本的 LaTeX](paper_kradar_v2_weather_l4dr_table10_260912.tex)',
           '- [生成脚本](../tools/analysis/export_v2_weather_l4dr_table10_260912.py)', '',
           '本轮只整理已有结果及读取 GT，没有运行训练或 GPU 推理。','']
    assert len(export_rows)==32
    OUT.with_suffix('.md').write_text('\n'.join(md))
    OUT.with_suffix('.tex').write_text('\n'.join(tex))
    with OUT.with_suffix('.csv').open('w',newline='') as f:
        w=csv.writer(f)
        w.writerow(['condition','class','metric','iou','asf_ap','decstrong_ap','delta_pp','has_gt'])
        w.writerows(export_rows)
    with OUT.with_suffix('.l4dr_reference.csv').open('w',newline='') as f:
        w = csv.writer(f)
        w.writerow(['condition','class','metric','iou','l4dr_paper_ap','decstrong_ap','numerical_delta_pp','aligned_evaluator','source'])
        for cls in ('sed','bus'):
            for c in CONDITIONS:
                a,b = L4DR[cls][c],ours[c][cls]['3D']['0.3']
                w.writerow([c,cls,'3D','0.3',a,b,None if a is None else b-a,False,SOURCE])
    print(f'Exported {len(export_rows)} comparisons / 64 AP values; Fog Bus GT = {gt["fog"]["bus"]}.')
    print(OUT.with_suffix('.md'))


if __name__=='__main__':
    main()
