"""Summarize saved Strong inference and ASF Table 3; no inference or model changes."""
import csv
import json
from pathlib import Path

ROOT = Path('/home/hongsheng/dec_con_asf')
BASE = ROOT / 'analysis_exports/taskdec_v2_availability_completion_260918'
OUT = ROOT / 'results/taskdec_v2_availability_vs_asf_table3_260918.md'
SOURCE = 'https://arxiv.org/html/2503.07029v2#S4.T3'
LABEL = dict(r='R', l='L', c='C', c_star='C*', lr='L+R', cr='C+R', cl='C+L',
             clr='C+L+R', c_star_lr='C*+L+R', cl_star_r='C+L*+R')
WEATHER = ['all', 'normal', 'overcast', 'sleet', 'heavysnow']
# Verbatim numeric facts from Table 3, not the partly inconsistent Appendix Table 9.
PAPER = {
    'sed': [
        [47.3,40.7,58.8,45.9,56.5], [73.0,73.0,86.1,64.9,54.5],
        [14.8,14.9,7.71,None,None], [3.71,3.72,3.17,None,None],
        [77.3,77.7,87.3,74.4,65.4], [52.7,49.1,62.4,46.0,57.2],
        [76.4,78.3,86.5,64.2,57.1], [79.3,78.8,87.6,74.2,65.8],
        [77.6,78.2,87.7,74.4,65.4], [58.9,58.8,66.6,52.3,58.2]],
    'bus': [
        [34.2,22.9,40.9,21.1,51.2], [54.9,53.7,74.8,69.1,37.8],
        [9.59,9.02,17.2,None,None], [3.65,3.66,0.0,None,None],
        [59.9,52.5,71.6,68.2,68.9], [36.2,24.4,41.4,23.4,56.5],
        [53.0,49.1,60.1,72.1,39.6], [60.4,52.7,77.4,69.2,68.9],
        [60.1,52.1,72.0,70.9,69.1], [40.0,31.5,38.2,28.9,54.8]]}


def main():
    d = json.loads((BASE / 'results.json').read_text())
    status = json.loads((BASE / 'status.json').read_text())
    audit = json.loads((BASE / 'clr_archive_check.json').read_text())
    assert status['phase'] == 'complete' and status['failure_count'] == 0
    assert set(d) == set(LABEL) and audit['max_absolute_ap_delta'] == 0
    for case in d.values():
        for conf in ['0.0', '0.3']:
            assert len(case[conf]) == 8 and case[conf]['all']['frames'] == 13727
            assert sum(v['frames'] for k, v in case[conf].items() if k != 'all') == 13727

    def ap(k, cls, weather='all', conf='0.0', iou=0.3):
        v = d[k][conf][weather]['classes'][cls]
        return v['AP3D'][v['iou'].index(iou)]

    def mean(k, conf='0.0'):
        return sum(ap(k, c, conf=conf) for c in ['sed', 'bus']) / 2

    lines = [
        '# K-Radar v2.0 退化评测：DecControlled Strong 与 ASF 表3对照', '',
        '2026-09-18 整理。13:50:52（北京时间）全部完成：13,727帧、10种输入设置、2个置信度阈值、Total及7种天气，无失败。完整输入在conf=0.3下与旧归档逐项AP差值均为0。', '',
        '## 模型与比较边界', '',
        '- 本次模型是 DecControlled Strong 08-06 的 model_10；十行使用同一权重，不重训、不按组合换模型。该版本没有完整 TaskDec 的 task-context 分支。',
        '- v2_0标签，ROI `[0,-16,-2,72,16,7.6]`，revised evaluator，z_center=0.5，NMS=0.01。',
        '- ASF表3的总体完整输入79.3/60.4，与本地官方权重conf=0.0归档79.2558/60.3794相符。因此这里以Strong的conf=0.0作为论文数值对照；阈值对应关系来自本地归档核对，不声称论文明确写了此阈值。',
        '- 本地conf=0.0仍保留检测头score prefilter=0.1。conf=0.3是原有项目主评测设置，两档均保留，不能混用。',
        '- ASF列为论文报告值，不是本轮对ASF十种输入重新评测。部分天气格存在正文表3与附录表9差异；本报告统一锁定正文表3，不逐格混用。',
        '- C*为原始RGB全黑、经原归一化与相机编码器；L*为无回波的空输入约定：零高度压缩稀疏特征再过原LiDAR稠密backbone，保留分支。ASF精确损坏规则未完全确认，所有带*行只能参考比较。',
        '- 本地C/C*覆盖13,727帧。ASF表3相机单路行仅列Normal/Overcast，表8另注明相机评测使用序列1–20；不能据此直接断言表3也是同一子集，但其相机单路样本范围尚需核实。', '',
        f'论文来源：[ASF Table 3]({SOURCE})；相机范围和附录差异参见同文Appendix D。', '',
        '## Total：AP3D@0.3', '',
        'Strong使用conf=0.0。Δ为Strong减ASF，单位为百分点；相机单路和星号行受上述协议边界限制。ASF原值仅一至两位小数，这里的差值也受其舍入精度限制。', '',
        '| 输入 | ASF Sedan | Strong Sedan | Δ | ASF Bus/Truck | Strong Bus/Truck | Δ |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for i, (k, label) in enumerate(LABEL.items()):
        a, b = PAPER['sed'][i][0], PAPER['bus'][i][0]
        x, y = ap(k, 'sed'), ap(k, 'bus')
        lines.append(f'| {label} | {a:.2f} | {x:.2f} | {x-a:+.2f} | {b:.2f} | {y:.2f} | {y-b:+.2f} |')
    lines += ['', '## 自身退化幅度及阈值敏感性', '',
              '两类AP取算术平均。保持率是退化组合的平均AP除以同阈值完整输入平均AP，不是目标召回率。', '',
              '| 输入 | conf=0.0 平均AP | 相对完整输入Δ | AP保持率 | conf=0.3 平均AP |',
              '|---|---:|---:|---:|---:|']
    for k, label in LABEL.items():
        m = mean(k)
        lines.append(f'| {label} | {m:.2f} | {m-mean("clr"):+.2f} | {m/mean("clr")*100:.2f}% | {mean(k,"0.3"):.2f} |')
    lines += ['', '## 分天气：严格按ASF正文表3布局', '',
              '每格为“ASF / Strong（Strong−ASF）”，Strong使用conf=0.0；—表示ASF未报告，不能视为0。', '']
    rows = []
    for cls, title in [('sed', 'Sedan'), ('bus', 'Bus or Truck')]:
        lines += [f'### {title}', '', '| 输入 | Total | Normal | Overcast | Sleet | Heavy snow |', '|---|---:|---:|---:|---:|---:|']
        for i, (k, label) in enumerate(LABEL.items()):
            cells = []
            for j, w in enumerate(WEATHER):
                ref, val = PAPER[cls][i][j], ap(k, cls, w)
                cells.append(f'— / {val:.2f}' if ref is None else f'{ref:.2f} / {val:.2f} ({val-ref:+.2f})')
                rows.append([k, cls, w, ref, val, None if ref is None else val-ref])
            lines.append(f'| {label} | ' + ' | '.join(cells) + ' |')
        lines += ['']
    lines += ['## 完整输入：两档阈值与更高IoU复核', '',
              '这里ASF改用本地官方权重归档的未舍入值计算，区别于上方论文表3列。', '',
              '| conf | AP3D IoU | ASF 两类平均 | Strong 两类平均 | Δ |', '|---|---|---:|---:|---:|']
    for conf in ['0.0', '0.3']:
        archive = Path(f'/home/hongsheng/K-Radar-main/results/official_asf_v2_RLC/summary_conf{conf}.json')
        official = json.loads(archive.read_text())[conf]['all']
        for iou in [0.3, 0.5]:
            ref = sum(official[c]['3D'][str(iou)] for c in ['sed', 'bus']) / 2
            val = sum(ap('clr', c, conf=conf, iou=iou) for c in ['sed', 'bus']) / 2
            lines.append(f'| {conf} | {iou} | {ref:.2f} | {val:.2f} | {val-ref:+.2f} |')
    lines += ['', '## 结果解读与论文表述', '',
        '1. **去相机稳定。** L+R平均AP为68.96，比自身完整输入69.41低0.46点，保持99.34%。L+R的Sedan/Bus为77.55/60.36，略高于ASF表3的77.3/59.9；这是数值上的小幅优势，不是统计显著性结论。',
        '2. **去雷达尚可，但不是无损。** C+L平均65.13，较完整输入下降4.28点；Sedan低于ASF0.91点，Bus高1.78点。仅LiDAR的平均AP为62.33，低于完整输入7.08点。',
        '3. **无LiDAR仍是明显短板。** C+R平均34.73，只保留完整输入约50.03%的AP；R单独为31.63。C+R的Sedan/Bus分别低于ASF13.13/6.31点。不能将这组结果概括为全面优于ASF的缺模态鲁棒性。',
        '4. **黑帧不掉点有多种解释。** C*+L+R平均69.40，仅低0.01点，但C单独近0，同时去掉相机损失也很小。证据只能支持“此模型对黑帧不敏感”；还可能与相机贡献较弱有关，不能据此证明可靠性识别机制更强。相机分支及其训练覆盖值得后续专项核查，本轮未确定原因。',
        '5. **缺失与损坏不能合并。** C+L*+R在conf=0.0下为38.32/31.08，平均34.70；与C+R平均接近但类别不同。conf=0.3时该组合平均只有27.99，低于C+R的34.25，表明其对分数过滤较敏感，不能只保留有利阈值。',
        '6. **分天气有局部优势，也有回退。** 完整输入Heavy snow比ASF表3高1.37/3.95点；L+R的Heavy snow高0.78/2.18点。但完整输入Normal两类均偏低，Sleet下Sedan高1.64、Bus低2.67点。应连同完整表报告。',
        '7. **阈值解释前后差异。** 完整输入AP3D@0.3在原conf=0.3口径较官方ASF高0.36点；改为对应论文总体值的conf=0.0后低0.40点。AP3D@0.5在两档下分别高约1.48/1.50点。全输入精度优势和退化鲁棒性是不同结论。',
        '8. **写作建议。** 可将十种设置作为“固定权重下的传感器可用性分析”，强调去相机后的性能保持，同时说明对LiDAR的依赖。若正文仅展示少量组合，附录仍保留全部组合及两档阈值，不把这组Strong结果标作完整TaskDec，也不以未对齐的星号结果宣称超过ASF。', '',
        '## 完整结果与可追溯文件', '',
        f'- [完整机器结果：全部天气、两类、AP3D/APBEV、三种IoU、两档conf]({BASE / "results.json"})',
        f'- [本轮conf=0.3详细表]({BASE / "results.md"})',
        f'- [原始权重与协议清单]({BASE / "manifest.json"})',
        f'- [完整输入归档一致性检查]({BASE / "clr_archive_check.json"})',
        f'- [表3逐格对照CSV]({BASE / "asf_table3_comparison.csv"})',
        f'- [本报告生成脚本]({Path(__file__).resolve()})', '']
    OUT.write_text('\n'.join(lines))
    with (BASE / 'asf_table3_comparison.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['case', 'class', 'condition', 'asf_paper_table3', 'strong_conf0.0', 'delta'])
        writer.writerows(rows)
    assert len(rows) == 100
    print(OUT)
    print(f'Checked 10 cases × 2 confidence thresholds × 8 conditions; exported {len(rows)} comparison cells.')


if __name__ == '__main__':
    main()
