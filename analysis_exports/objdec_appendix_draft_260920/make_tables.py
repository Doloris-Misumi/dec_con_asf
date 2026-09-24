"""Build appendix tables from existing records; CPU-only, no inference."""
from pathlib import Path
import csv
import hashlib
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sources = {}
blocks = []


def read(path):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    raw = p.read_bytes()
    sources[str(p)] = hashlib.sha256(raw).hexdigest()
    return raw.decode('utf-8-sig')


def js(path):
    return json.loads(read(path))


def csvrows(path):
    return list(csv.DictReader(read(path).splitlines()))


def table(tag, title, headers, rows, note):
    blocks.extend([f'<a id="table-{tag.lower().replace(".", "")}"></a>',
                   f'### Table {tag}. {title}', '',
                   '| ' + ' | '.join(headers) + ' |',
                   '| ' + ' | '.join(['---'] * len(headers)) + ' |'])
    for row in rows:
        blocks.append('| ' + ' | '.join(str(x) for x in row) + ' |')
    blocks.extend(['', note, ''])


def f(v, digits=2):
    return f'{float(v):.{digits}f}'


weathers = ['normal', 'overcast', 'fog', 'rain', 'sleet', 'lightsnow', 'heavysnow']
wlabels = ['Normal', 'Overcast', 'Fog', 'Rain', 'Sleet', 'Light snow', 'Heavy snow']
v1dirs = {
    'ASF released archive': '/home/hongsheng/K-Radar-main/results/official_asf_v1_exp250303',
    'ASF local': str(ROOT / 'results/exp_260818_202519_ASF_v1_0_local_repro_model2_full'),
    'ObjDec': str(ROOT / 'results/exp_260812_232650_TaskDecControlRobust_v1_model0_full'),
}
v1 = {}
rows = []
for name, p in v1dirs.items():
    for conf in ['0.3', '0.0']:
        d = js(Path(p) / f'summary_conf{conf}.json')[conf]
        v1[name, conf] = d
        a = d['all']['sed']
        rows.append([name, conf] + [f(a[k][iou]) for k in ['3D', 'BEV'] for iou in ['0.3', '0.5', '0.7']])
table('C.1', 'v1完整指标与置信度 / Complete v1 metrics and confidence settings',
      ['Method', 'conf', '3D@0.3', '3D@0.5', '3D@0.7', 'BEV@0.3', 'BEV@0.5', 'BEV@0.7'], rows,
      '**中文。** 同一方法两行使用同一权重；conf表示检测头预过滤之外的导出阈值。官方ASF行为权重对应归档。部分主指标为便于核对保留，新增严格IoU与阈值设置构成补充。\n\n**English.** Each pair uses the same checkpoint and changes the export confidence filter, in addition to the detector prefilter. Released ASF results are checkpoint-associated archives. Main metrics are retained as anchors for the additional IoU and threshold results.')

v2 = csvrows('analysis_exports/v2_matched_training_260915/reporting_strategy_260916/five_sources_full_metrics.csv')
lookup = {(r['method'], r['condition'], r['cls'], r['metric'], r['iou']): r for r in v2}
methods = ['ASF_official', 'L4DR_official', 'ASF_local', 'L4DR_local', 'Strong']
labels = {'ASF_official': 'ASF released archive', 'L4DR_official': 'L4DR released, aligned',
          'ASF_local': 'ASF local', 'L4DR_local': 'L4DR local', 'Strong': 'DecControlled Strong'}


def v2ap(method, condition, cls, metric, iou):
    x = lookup[method, condition, cls, metric, iou]
    return '—' if x['has_gt'].lower() == 'false' else f(x['ap'])


rows = [[labels[m], 'Sedan' if c == 'sed' else 'Bus/Truck'] +
        [v2ap(m, 'all', c, k, i) for k in ['3d', 'bev'] for i in ['0.3', '0.5', '0.7']]
        for m in methods for c in ['sed', 'bus']]
table('C.2', 'v2逐类完整指标 / Complete class-wise v2 metrics',
      ['Method', 'Class', '3D@0.3', '3D@0.5', '3D@0.7', 'BEV@0.3', 'BEV@0.5', 'BEV@0.7'], rows,
      '**中文。** conf=0.3。补充正文以两类Mean为主的比较。Strong不含object context；本地训练组匹配训练集、11轮与有效batch，初始化和模态差异见B。\n\n**English.** Confidence is 0.3. These class-wise results complement the class means in the main text. Strong omits object context. Local runs match the training split, 11 epochs, and effective batch size; initialization and modality differences are specified in Appendix B.')
rows = []
for iou in ['0.3', '0.5']:
    for m in v1dirs:
        rows.append([m, iou] + [f(v1[m, '0.3'][w]['sed']['3D'][iou]) for w in ['all'] + weathers])
table('C.3', 'v1天气分组 / Weather-wise v1 3D AP',
      ['Method', 'IoU', 'Total'] + wlabels, rows,
      '**中文。** Sedan，conf=0.3。Total在整个评测集合上重新计算，不是天气AP均值。\n\n**English.** Sedan at confidence 0.3. Total is evaluated over the combined set and is not an average of weather APs.')
for suffix, iou in [('a', '0.3'), ('b', '0.5')]:
    rows = [[labels[m], 'Sedan' if c == 'sed' else 'Bus/Truck'] +
            [v2ap(m, w, c, '3d', iou) for w in ['all'] + weathers]
            for c in ['sed', 'bus'] for m in methods]
    table('C.4' + suffix, f'v2天气分组 AP3D@{iou} / Weather-wise v2 3D AP',
          ['Method', 'Class', 'Total'] + wlabels, rows,
          '**中文。** conf=0.3；“—”表示该天气无此类别GT，不能作为零分参与平均。\n\n**English.** Confidence is 0.3. A dash indicates no GT objects of the class in that weather group and is excluded from any class–weather comparison.')

abl = read('results/taskdec_v1_component_ablation_conf0_3_260901.md')
ablrows = [line.split('|')[1:-1] for line in abl.splitlines()
           if line.startswith('| w/o ') and len(line.split('|')[1:-1]) == 10]
assert len(ablrows) == 4
rows = [['Full ObjDec'] + [f(v1['ObjDec', '0.3']['all']['sed'][k][i]) for k, i in [('3D', '0.7'), ('BEV', '0.7'), ('BEV', '0.3')]]]
abl_labels = ['w/o modality contribution control', 'w/o object context', 'w/o decoupling supervision', 'w/o foreground gate']
for label, r in zip(abl_labels, ablrows):
    rows.append([label] + [f(r[i].strip()) for i in [6, 3, 5]])
table('D.1', '正文消融的补充指标 / Additional ablation metrics',
      ['Variant', '3D@0.7', 'BEV@0.7', 'BEV@0.3'], rows,
      '**中文。** v1，conf=0.3；正文已展示的3D@0.3/@0.5及BEV@0.5不再重复。完整模型取与C.1一致的原始JSON，移除项来自对应结果归档。\n\n**English.** v1 at confidence 0.3. The 3D@0.3/@0.5 and BEV@0.5 columns already shown in the main ablation table are omitted. The full-model row follows the same JSON as Table C.1; ablated rows follow their experiment records.')

stats = csvrows('analysis_exports/objdec_fulltest_weather_260919/weather_statistics.csv')
st = {(x['weather'], x['feature']): x for x in stats}
assert sum(int(st[w, 'common']['frames']) for w in weathers) == 10065
rows = []
for w, label in zip(weathers, wlabels):
    s = st[w, 'common']; rows.append([label, s['frames'], s['sequences'], s['foreground_patches']] +
        [f(st[w, feat][pair], 4) for feat in ['common', 'unique'] for pair in ['cosine_CL', 'cosine_CR', 'cosine_LR']])
table('E.1', '按模态对拆分的全量高维相似度 / Full-set similarity by modality pair',
      ['Weather', 'Frames', 'Sequences', 'FG patches', 'Shared C–L', 'Shared C–R', 'Shared L–R', 'Specific C–L', 'Specific C–R', 'Specific L–R'], rows,
      '**中文。** 原始256维空间；先对帧内匹配前景位置求平均，再对天气内各帧等权平均。\n\n**English.** Cosines in the original 256-dimensional space are averaged over matched foreground locations within each frame, then equally over frames within a weather group.')
distributions = csvrows('analysis_exports/objdec_fulltest_weather_260919/paper_visuals/direct_similarity_distribution_statistics.csv')
rows = [[x['weather'], x['feature'], x['pair'], f(x['median'], 4), f(x['p05'], 4), f(x['p95'], 4)]
        for x in distributions if x['weather'] in ['normal', 'heavysnow'] and x['feature'] in ['common', 'unique'] and x['pair'] == 'LiDAR–4D Radar']
table('E.2', 'L–R相似度分位数 / L–R similarity quantiles',
      ['Weather', 'Branch', 'Pair', 'Median', '5th percentile', '95th percentile'], rows,
      '**中文。** 每个观测值为一帧中匹配前景patch余弦的均值；分位范围描述帧间变异，不是置信区间。\n\n**English.** Each observation is a frame-level mean of matched-patch cosines. Quantiles describe variation across frames, not confidence intervals.')

gate_selection = js('analysis_exports/objdec_fig4_fig5_260919/fig4_selection.json')['frames']
assert len(gate_selection) == 7
rows = [[dict(zip(weathers, wlabels))[x['weather']], x['id'], x['num_gt'], x['foreground_patches'],
         f(x['gate_fg_mean'], 4), f(x['gate_bg_mean'], 4), f(x['gate_gap'], 4)] for x in gate_selection]
table('E.3', '正文gate选例的逐帧统计 / Frame-level statistics of the main gate examples',
      ['Weather', 'Frame ID', 'GT objects', 'FG patches', 'FG gate mean', 'BG gate mean', 'FG − BG'], rows,
      '**中文。** 每帧均为1,440个完整patch。前景依据0.7m扩张GT区域在预测后划分；这些是七个定性选例的帧内统计，不是七天气总体均值。\n\n**English.** Each frame has 1,440 complete patches. Foreground regions use GT footprints expanded by 0.7 m after prediction. Values summarize seven qualitative examples, not weather-wide means.')

v1avail = js('analysis_exports/taskdec_v1_availability_completion_260918/results.json')
v2avail = js('analysis_exports/taskdec_v2_availability_completion_260918/results.json')
case_names = [('clr', 'C+L+R'), ('lr', 'L+R'), ('cl', 'C+L'), ('cr', 'C+R'), ('l', 'L'), ('r', 'R'), ('c', 'C'), ('c_star', 'C*'), ('c_star_lr', 'C*+L+R'), ('cl_star_r', 'C+L*+R')]
v1cr = js('logs/exp_260902_075102_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/full_eval_summary.json')
v1cl = js('logs/exp_260902_203611_TaskDecControlRobust_v1_0_A2FUSION_rlc_l1d256_l2p2t32d256g_l2g_scl_mha16/full_eval_summary.json')
read('results/full_eval_metric_audit_260821.md')


def from_summary(d):
    return [d['3D']['0.3'], d['3D']['0.5'], d['BEV']['0.5']]


rows = []
for case, label in case_names:
    for conf in ['0.3', '0.0']:
        if case == 'clr':
            values = from_summary(v1['ObjDec', conf]['all']['sed'])
        elif case == 'lr':
            values = [88.06, 71.68, 85.45] if conf == '0.3' else None
        elif case in ['cl', 'cr']:
            d = {'cl': v1cl, 'cr': v1cr}[case]['0.3' if conf == '0.3' else '0']['all']['sed']
            values = from_summary(d)
        else:
            d = v1avail[case][conf]['all']; assert d['frames'] == 10065
            values = [d['AP3D'][2], d['AP3D'][1], d['BEV'][1]]
        base = v1['ObjDec', conf]['all']['sed']['3D']['0.3']
        rows.append([label, conf] + ([f(x) for x in values] + [f'{values[0]-base:+.2f}'] if values else ['NR'] * 4))
table('F.1', 'v1固定权重的输入可用性 / v1 input availability with fixed weights',
      ['Input', 'conf', '3D@0.3', '3D@0.5', 'BEV@0.5', 'Δ 3D@0.3 vs CLR'], rows,
      '**中文。** 10,065帧，正式v1 ObjDec。LR的conf=0.3行使用保存预测的已核查复算值（来源保留两位小数）；NR表示本稿尚无已核实的LR conf=0.0汇总，不是零分。所有其余行来自原始JSON。\n\n**English.** The same v1 ObjDec checkpoint is evaluated on 10,065 frames. The LR/conf=0.3 row uses the audited recomputation of saved predictions, reported to two decimals in its source. NR denotes an unverified summary for LR/conf=0.0, not zero performance. Other rows are read from their JSON records.')
rows = []
for case, label in case_names:
    for conf in ['0.3', '0.0']:
        d = v2avail[case][conf]['all']; assert d['frames'] == 13727
        a = d['mean']; base = v2avail['clr'][conf]['all']['mean']['AP3D'][2]
        rows.append([label, conf, f(a['AP3D'][2]), f(a['AP3D'][1]), f(a['BEV'][1]), f'{a["AP3D"][2]-base:+.2f}'])
table('F.2', 'v2固定Strong权重的输入可用性 / v2 input availability with fixed Strong weights',
      ['Input', 'conf', 'Mean 3D@0.3', 'Mean 3D@0.5', 'Mean BEV@0.5', 'Δ mean 3D@0.3 vs CLR'], rows,
      '**中文。** 13,727帧，Sedan与Bus/Truck等权平均；每个conf的差值均对应该conf下的完整输入。星号表示F节定义的本地损坏输入。\n\n**English.** Equal class means over Sedan and Bus/Truck on 13,727 frames. Deltas use the full-input result at the same confidence filter. Stars denote the locally defined corruptions in Appendix F.')

groups = [
    ('Concat', 'C+L+R', '0.4', 'analysis_exports/v2x_taskdec_260916/controlled_80ep/concat'),
    ('ASF-style', 'C+L+R', '0.4', 'analysis_exports/v2x_taskdec_260916/controlled_80ep/patch'),
    ('ObjDec 4×4', 'C+L+R', '0.4', 'analysis_exports/v2x_taskdec_260916/controlled_80ep/taskdec'),
    ('ObjDec 2×2', 'C+L+R', '0.4', 'analysis_exports/v2x_taskdec_260916/taskdec_patch2_80ep/taskdec'),
    ('Concat', 'C+L+R', '0.16', 'analysis_exports/v2x_grid016_260918/matched_80ep/concat'),
    ('ASF-style', 'C+L+R', '0.16', 'analysis_exports/v2x_grid016_controls_260919/asf_clr_80ep/patch'),
    ('ObjDec 2×2', 'C+L+R', '0.16', 'analysis_exports/v2x_grid016_260918/matched_80ep/taskdec'),
    ('L4DR', 'L+R', '0.16', 'analysis_exports/v2x_l4dr_260917/matched_80ep/l4dr'),
    ('ObjDec-LR 2×2', 'L+R', '0.16', 'analysis_exports/v2x_grid016_controls_260919/objdec_lr_80ep/taskdec'),
]
rows = []
final_data = {}
for name, sensors, grid, path in groups:
    p = ROOT / path / 'final_best.json'
    if not p.exists():
        rows.append([name, sensors, grid] + ['Pending'] * 7); continue
    d = js(p); final_data[name, sensors, grid] = d
    val, test = [d['results'][k] for k in ['val_deduplicated', 'test_deduplicated']]
    assert val['frames'] == 1487 and test['frames'] == 1486
    vm, tm = val['metrics'], test['metrics']
    rows.append([name, sensors, grid, d['epoch'], f(vm['V2X/Overall_3D_moderate'])] +
                [f(tm[f'V2X/{c}_3D_moderate_strict']) for c in ['Vehicle', 'Pedestrian', 'Cyclist']] +
                [f(tm['V2X/Overall_3D_moderate']), f(tm['V2X/Overall_BEV_moderate'])])
table('G.1', '空间粒度与完整预算结果 / Spatial granularity and full-budget results',
      ['Method', 'Sensors', 'Grid (m)', 'Best epoch', 'Val mean 3D', 'Test Vehicle', 'Test Pedestrian', 'Test Cyclist', 'Test mean 3D', 'Test mean BEV'], rows,
      '**中文。** 均为80轮预算下按val选择的best，Moderate AP_R40；旧0.4m组补充正文0.16m表。Val与test分别列出，不用训练期val替代test。\n\n**English.** Best checkpoints are selected by validation under an 80-epoch budget, using Moderate AP_R40. The 0.4 m group supplements the main 0.16 m comparison. Validation and test results are reported separately.')
rows = []
for name, sensors, grid, path in groups:
    if (name, sensors, grid) not in final_data or grid != '0.16': continue
    for ckpt in ['best', 'last']:
        d = js(ROOT / path / f'final_{ckpt}.json')
        m = d['results']['test_deduplicated']['metrics']
        rows.append([name, ckpt, d['epoch']] + [f(m[f'V2X/{c}_BEV_moderate_strict']) for c in ['Vehicle', 'Pedestrian', 'Cyclist']] +
                    [f(m['V2X/Overall_BEV_moderate']), f(m['V2X/Overall_3D_moderate'])])
table('G.2', '已完成0.16m组的BEV及末轮补充 / BEV and last-checkpoint results for completed 0.16 m runs',
      ['Method', 'Checkpoint', 'Epoch', 'BEV Vehicle', 'BEV Pedestrian', 'BEV Cyclist', 'Mean BEV', 'Mean 3D'], rows,
      '**中文。** 去重test。best按val选择；last为第80轮，报告其结果不改变选模规则。五组0.16m实验的best/last均已完成。\n\n**English.** Deduplicated test results. Best is selected by validation, whereas last is epoch 80. Reporting last does not change the selection rule. Best/last evaluations are complete for all five 0.16 m runs.')

# VoD: historical/reported rows use the audited source table; recent rows are
# checked against their checkpoint-specific official metric JSONs.
vod_report = read('results/objdec_vod_current_tables_260922.md')
vod_names = {
    'PP-Concat，历史本地基线': ('PP-Concat (historical)', 'Local'),
    '旧ObjDec，warm-start＋mild': ('ObjDec (warm-start, historical)', 'Local'),
    'ObjDec，2×2 patch＋局部编码': ('ObjDec (2×2 + local)', 'Local'),
    'ObjDec，上述配置＋适配锚框': ('ObjDec (+ adapted anchors)', 'Local'),
    'L4DR，本地复现': ('L4DR', 'Local'),
    'InterFusion，论文报告': ('InterFusion', 'Reported'),
    'L4DR，论文报告': ('L4DR', 'Reported'),
}
vod_runs = [
    ('ObjDec，2×2 patch＋局部编码', 'analysis_exports/objdec_vod_patch2_local_260920/validation/epoch_075'),
    ('ObjDec，上述配置＋适配锚框', 'analysis_exports/objdec_vod_adapted_anchors_260921/validation/epoch_080'),
]
vod_metrics = {name: js(Path(path) / 'metrics.json') for name, path in vod_runs}
for tag, heading, region, title in [
    ('G.3a', '### EAA：', 'entire_area', 'VoD整体标注区域 / VoD Entire Annotated Area (EAA)'),
    ('G.3b', '### DC：', 'roi', 'VoD驾驶走廊 / VoD Driving Corridor (DC)'),
]:
    section = vod_report.split(heading, 1)[1].split('\n##', 1)[0]
    rows = []
    for line in section.splitlines():
        if not line.startswith('| '):
            continue
        cells = [x.strip() for x in line.strip('|').split('|')]
        if cells[0] not in vod_names:
            continue
        name = cells[0]
        if name in vod_metrics:
            d = vod_metrics[name]
            assert d['frames'] == 1296 and int(cells[1]) == d['epoch']
            expected = [f(d['official'][region][k]) for k in
                        ['Car_3d_all', 'Pedestrian_3d_all', 'Cyclist_3d_all', '3d_all']]
            assert cells[2:] == expected, (name, region, cells, expected)
        label, source = vod_names[name]
        rows.append([label, source] + cells[1:])
    assert len(rows) == 7
    table(tag, title, ['Method', 'Source', 'Epoch', 'Car', 'Pedestrian', 'Cyclist', 'Mean'], rows,
          '**中文。** 所有方法输入均为L+R，无额外人工雾；官方VoD 11点3D AP，类别IoU为0.5/0.25/0.25。本地结果为1,296帧验证集；EAA与DC的同名行使用同一权重。两组近期ObjDec按EAA选模，训练及历史参照差异见G.4。Reported两行取自L4DR正式论文表3 [L4DR]，Mean为其公开类别值的算术平均；Local均值保留原评分输出。\n\n**English.** All methods use L+R without added synthetic fog. Official VoD 11-point 3D AP uses class IoUs of 0.5/0.25/0.25. Local results use 1,296 validation frames, with the same checkpoint for each method across EAA and DC. The two recent ObjDec runs select checkpoints by EAA; training and historical-reference differences are detailed in G.4. Reported rows are from Table 3 of the published L4DR paper [L4DR], with means computed from its class values. Local means retain the evaluator output.')

# The JSON's generic KITTI keys use stricter IoUs; parse explicitly labelled
# 0.50/0.25/0.25 3D/BEV blocks from kitti.txt for this supplementary comparison.
vod_kitti = {name: read(Path(path) / 'kitti.txt') for name, path in vod_runs}
rows = []
for metric, label in [('3d', '3D'), ('bev', 'BEV')]:
    for name, _ in vod_runs:
        class_values = []
        for cls, header_iou, box_iou in [('Car', '0.70', '0.50'),
                                       ('Pedestrian', '0.50', '0.25'),
                                       ('Cyclist', '0.50', '0.25')]:
            header = f'{cls} AP_R40@{header_iou}, {box_iou}, {box_iou}:\n'
            block = vod_kitti[name].split(header, 1)[1].splitlines()[:4]
            matches = [line for line in block if re.match(rf'^{metric}\s+AP:', line)]
            assert len(matches) == 1
            class_values.append([float(v) for v in matches[0].split(':', 1)[1].split(',')])
        means = [sum(c[i] for c in class_values) / 3 for i in range(3)]
        rows.append([vod_names[name][0], vod_metrics[name]['epoch'], label] + [f(v) for v in means])
table('G.4', 'VoD补充难度指标 / Supplementary KITTI difficulty metrics on VoD',
      ['Configuration', 'Epoch', 'Metric', 'Easy mean', 'Moderate mean', 'Hard mean'], rows,
      '**中文。** 与表G.3相同的EAA选中权重，三类等权平均；3D/BEV的IoU均为0.5/0.25/0.25。此表使用KITTI难度过滤及AP_R40，与官方EAA/DC的区域过滤和11点AP不同，不混用两套数值。\n\n**English.** Equal class means for the same EAA-selected checkpoints as Table G.3, using 3D/BEV IoUs of 0.5/0.25/0.25. KITTI difficulty filtering and AP_R40 differ from the region filtering and 11-point AP of official EAA/DC, so the two sets of scores are not interchangeable.')

speed = js('analysis_exports/inference_optimization_260917/comparison_summary.json')
rows = []
for model, label in [('asf', 'ASF'), ('taskdec', 'ObjDec')]:
    for mode in ['eager', 'optimized']:
        a = speed[model]['wall'][mode]
        rows.append([label, 'Eager' if mode == 'eager' else 'CUDA Graph'] +
                    [f(a[k]) for k in ['mean', 'median', 'p95', 'std']] + [f(1000 / a['mean'])])
table('H.1', '延迟分布 / Latency distributions',
      ['Model', 'Execution', 'Mean ms', 'Median ms', 'P95 ms', 'Std ms', '1000 / mean ms'], rows,
      '**中文。** 每种模型/路径100个不同计时帧、重复两轮；最后一列为计时路径吞吐，不包含读盘。标准差描述计时变异，不是多种子检测误差。\n\n**English.** Each model/path uses 100 distinct timed frames repeated twice. The final column is the reciprocal of measured latency, excluding disk loading. Standard deviations describe timing variation rather than multi-seed detection uncertainty.')

out = OUT / 'generated_tables.md'
out.write_text('\n'.join(blocks))
(OUT / 'sources.json').write_text(json.dumps({'generated_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
    'scope': 'Existing records only; no training or inference; v1 LR/conf0.3 transcribed from audited two-decimal source; unverified LR/conf0.0 marked NR.',
    'sources_sha256': sources, 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, ensure_ascii=False, indent=2) + '\n')
print('Wrote', out, 'sources', len(sources), 'tables', sum(x.startswith('### Table') for x in blocks))
