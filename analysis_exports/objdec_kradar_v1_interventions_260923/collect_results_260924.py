"""Collect completed fixed-weight interventions and audit cached predictions on CPU."""
import collections
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'reporting_260924'
OUT.mkdir(exist_ok=True)
CASES=['baseline','gate_mean','gate_shuffle_260923','gate_shuffle_260924',
       'gate_shuffle_260925','no_query','no_output','no_query_output']
SHUFFLES=CASES[2:5]
NAMES=['完整ObjDec','gate帧内均值','gate打乱260923','gate打乱260924',
       'gate打乱260925','关闭query增量','关闭output增量','同时关闭两种增量']
WEATHERS=['normal','overcast','fog','rain','sleet','lightsnow','heavysnow']
WEATHER_NAMES=['正常','阴天','雾','雨','雨夹雪','小雪','大雪']
METRICS=[('AP3D',.3),('AP3D',.5),('AP3D',.7),('BEV',.3),('BEV',.5),('BEV',.7)]


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def csvwrite(p,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    r=read(HERE/'results.json');status=read(HERE/'status.json')
    check=read(HERE/'baseline_verification.json');manifest=read(HERE/'manifest.json')
    assert status['phase']=='complete' and status['completed_frames']==10065 and status['cases']==8
    assert not status['synthetic_metric_smoke_only'] and check['passed']
    assert set(r)==set(CASES)
    for rel,expected in manifest['source_sha256'].items():assert sha(ROOT/rel)==expected,rel
    assert sha(Path(manifest['checkpoint']))==manifest['checkpoint_sha256']

    def value(c,w,m,iou):
        z=r[c][w];return z[m][z['iou'].index(iou)]
    def summary(w,m,iou):return float(np.mean([value(c,w,m,iou) for c in SHUFFLES]))
    all_rows=[]
    for c in CASES:
        assert set(r[c])==set(['all']+WEATHERS)
        assert sum(r[c][w]['frames'] for w in WEATHERS)==10065
        for w in ['all']+WEATHERS:
            for m,iou in METRICS:
                v=value(c,w,m,iou);assert np.isfinite(v)
                all_rows.append(dict(case=c,condition=w,frames=r[c][w]['frames'],metric=m,iou=iou,
                                     AP=v,delta_pp=v-value('baseline',w,m,iou)))
    csvwrite(OUT/'all_conditions_metrics.csv',all_rows)

    scores=collections.defaultdict(list);counts=collections.defaultdict(list)
    indices=[];frame_weathers=[];gt_count=0;chunks=sorted((HERE/'chunks').glob('frames_*.jsonl.gz'))
    for p in chunks:
        with gzip.open(p,'rt') as f:
            for line in f:
                d=json.loads(line);indices.append(d['index']);frame_weathers.append(d['weather'])
                assert set(d['pred'])==set(CASES)
                gt_count+=sum(x.split()[0]=='sed' for x in d['gt'])
                for c,lines in d['pred'].items():
                    s=[]
                    for text in lines:
                        fields=text.split()
                        if fields[0]=='dummy':continue
                        assert fields[0]=='sed' and len(fields)==16
                        assert np.isfinite(np.asarray(fields[1:],dtype=float)).all()
                        s.append(float(fields[-1]))
                    s=np.asarray(s);scores[c].extend(s.tolist());counts[c].append(int((s>.3).sum()))
    assert indices==list(range(10065))
    assert collections.Counter(frame_weathers)=={w:r['baseline'][w]['frames'] for w in WEATHERS}
    diagnostic=[]
    for c in CASES:
        s=np.asarray(scores[c]);n=np.asarray(counts[c])
        diagnostic.append(dict(case=c,cached_post_nms_predictions=len(s),predictions_score_gt_03=int(n.sum()),
            predictions_score_gt_05=int((s>.5).sum()),frames_zero_predictions_gt_03=int((n==0).sum()),
            predictions_gt_03_per_frame=float(n.mean()),cached_score_median=float(np.median(s))))
    csvwrite(OUT/'prediction_count_and_score_diagnostics.csv',diagnostic)

    lines=['# K-Radar v1：八组固定权重推理干预结果与解释','',
        '2026-09-24收集。全部8组及各组的总体／七天气共64个评测单元已完成；每组10,065帧。完成时间为北京时间2026-09-24 00:08:23，总耗时162.00分钟。进程已退出，检查时GPU2为26 MiB。','',
        '**核心观察：** 正式主模型对gate空间组织高度敏感；query/output context增量单独或同时关闭，对总体AP影响很小。两者均应报告，不能将这批结果概括成所有控制分支都贡献显著。','',
        '## 1. 固定协议与核验','',
        '同一正式model_0、C+L+R、原始K-Radar v1 Sedan测试集、score>0.3、原始11-point评测器。每帧八种设置使用同一份编码特征，只改变推理控制量；GT不用于生成预测。source/模型/checkpoint哈希再次核对一致；10065个帧索引及八组预测完整。','',
        f"本次baseline与历史主表六项AP最大绝对差为{max(abs(x) for x in check['differences'].values()):.5f}个百分点，低于预先固定的0.05容差。历史AP3D@0.3/APBEV@0.5为88.3550/88.0953，本次为{value('baseline','all','AP3D',.3):.4f}/{value('baseline','all','BEV',.5):.4f}。下文所有差值以**本次配对baseline**为参照，不能交叉减历史值。原生独立编码存在输出波动，容差不是统计显著性阈值。",'',
        '## 2. 总体完整表','']
    headers=['设置']+[f'{m}@{iou:g}' for m,iou in METRICS]
    def table(w,delta=False):
        out=['| '+' | '.join(headers)+' |','|---|'+'---:|'*6]
        for c,name in zip(CASES,NAMES):
            vals=[value(c,w,m,i)-(value('baseline',w,m,i) if delta else 0) for m,i in METRICS]
            out.append('| '+name+' | '+' | '.join(f'{v:+.4f}' if delta else f'{v:.4f}' for v in vals)+' |')
        vals=[summary(w,m,i)-(value('baseline',w,m,i) if delta else 0) for m,i in METRICS]
        out.append('| 三次打乱均值 | '+' | '.join(f'{v:+.4f}' if delta else f'{v:.4f}' for v in vals)+' |')
        return out
    lines+=table('all')+['','### 相对本次baseline的变化（百分点）','']+table('all',True)
    lines+=['','AP3D@0.3的三次打乱结果范围21.2448–21.3775；AP3D@0.5为12.9107–17.5284。方向一致，但不能称所有IoU上的随机波动都很小。三个种子只是gate置换重复，不是独立训练。','',
        '## 3. 分天气：总体均值与打乱结果','',
        '| 天气 | 帧数 | 原始3D@0.3 | 均值gate | 打乱均值 | 原始BEV@0.5 | 均值gate | 打乱均值 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for w,name in zip(WEATHERS,WEATHER_NAMES):
        vals=[]
        for m,i in [('AP3D',.3),('BEV',.5)]:vals.extend([value('baseline',w,m,i),value('gate_mean',w,m,i),summary(w,m,i)])
        lines.append('| '+name+f" | {r['baseline'][w]['frames']} | "+' | '.join(f'{x:.2f}' for x in vals)+' |')
    lines+=['','七种天气均有明显退化，正常天气也成立，因此该结果支持一般的空间融合机制，不只支持恶劣天气叙事。天气组不是同场景受控天气变化，不能把组间差异解释成天气的独立因果效应。','',
        '总体context干预的六项AP绝对变化均低于0.08点，但少数天气的严格IoU指标稍大。例如no_query在阴天3D@0.7下降0.4546点；同时关闭两种增量在大雪3D@0.7上升0.3590点。保留混合方向，不能概括为每个天气都完全不变。','',
        '## 4. 大幅退化来自什么现象','',
        '以下直接统计已缓存的post-NMS预测，不再调用GPU模型。检测头原始SCORE_THRESH=0.1；“缓存框”不是全部原始候选框，分数中位数也受此预过滤影响。conf=0.3只用于本轮主表评分与计数。','',
        '| 设置 | 缓存框数 | score>0.3框数 | >0.3无框帧数 | 缓存分数中位数 |',
        '|---|---:|---:|---:|---:|']
    for d,name in zip(diagnostic,NAMES):
        lines.append(f"| {name} | {d['cached_post_nms_predictions']} | {d['predictions_score_gt_03']} | {d['frames_zero_predictions_gt_03']} | {d['cached_score_median']:.4f} |")
    lines+=['',f'缓存GT中Sedan框总数为{gt_count:,}。以上预测数不等于TP数；本次额外CPU诊断未进行逐GT匹配，不能直接称为官方precision/recall。','',
        '- **均值化**：保留帧内平均gate但移除位置差异；过0.3阈值的预测从19,237降到10,056，无框帧从382增到3,065，同时缓存分数分布明显降低。退化伴随预测减少与置信度变化。',
        '- **空间打乱**：过0.3阈值的预测反而增至42,496–42,804，同时AP大幅降低。因此不能把打乱的退化只解释为“分数低于阈值、输出框少了”；结果与错误位置响应增加相符，但精确FP/FN分解仍需匹配诊断。',
        '- **context增量关闭**：框数与分数接近baseline，符合其总体AP变化很小的观察。','',
        '## 5. 与此前V2X的关系及论文收益','',
        '| 干预 | K-Radar 3D@0.3 Δ | K-Radar BEV@0.5 Δ | V2X 3D mAP Δ | V2X BEV mAP Δ |',
        '|---|---:|---:|---:|---:|']
    v2x=list(csv.DictReader((ROOT/'analysis_exports/objdec_inference_studies_260923/interventions/comparison.csv').open()))
    vlookup={d['case']:d for d in v2x}
    for c,name in [('gate_mean','gate均值化'),('shuffle_mean','gate打乱（三次均值）'),('no_query','关闭query增量'),('no_output','关闭output增量')]:
        k=[(summary('all',m,i) if c=='shuffle_mean' else value(c,'all',m,i))-value('baseline','all',m,i) for m,i in [('AP3D',.3),('BEV',.5)]]
        v=[float(np.mean([float(vlookup[s][key]) for s in SHUFFLES])) if c=='shuffle_mean' else float(vlookup[c][key]) for key in ['delta_3D','delta_BEV']]
        lines.append('| '+name+' | '+' | '.join(f'{x:+.4f}' for x in k+v)+' |')
    lines+=['','V2X采用三类严格IoU、AP_R40、较低分数过滤与不同检测配置；K-Radar为Sedan、AP11、conf=0.3。该表用于核对方向，不用于比较哪个数据集“收益大多少倍”。','',
        '**能加强的主张：** gate的空间组织实际参与了检测，而不只是可视化看起来聚焦前景。在主模型上，均值化和打乱分别使3D@0.3下降34.46和平均67.07点；此前V2X也得到一致下降方向。与全量FG/BG统计结合，可以在同一K-Radar模型上建立“空间响应具有前景偏向”与“破坏空间对应后检测退化”的互补证据。','',
        '**不能写成：** “增加gate本身带来67.07点提升”“已经证明全部shared/specific都具有可辨识语义”“所有控制路径各自都不可替代”。本实验在固定权重下引入内部信号分布变化，且同一个gate共同作用于token残差、模态缩放和门控context，尚未隔离这些作用。重新训练的去gate消融允许其他参数适应，与本次干预结果不同并不矛盾。','',
        '**context结论需收紧：** 同时关闭两种增量后，总体3D@0.3/BEV@0.5仅下降0.0146/0.0087点，严格IoU指标还有小幅上升。因此，在这份K-Radar权重中，“两条路径互相补偿所以单独关闭不掉点”不足以解释结果。训练时的辅助监督作用仍未被本次实验排除；也不能把关闭增量称为移除了cross-modal attention。','',
        '**建议安排：** 正文机制分析用完整模型、gate均值、gate打乱均值组成紧凑表，并明确这是完整干预研究中的gate部分；相邻文字说明query/output及二者同时关闭的总体影响很小，指向附录完整表。附录D保留全部8组、3个打乱种子、各IoU和天气结果。若篇幅允许，正文直接给六种设置（打乱合为一行）更完整。保持现有完整模型定义，不在看到test结果后临时换模型。','',
        '### 可用于正文的中文表述','',
        '为检验空间控制是否实际影响检测，我们固定K-Radar v1主模型的全部权重，仅干预推理时的gate。将gate替换为帧内均值，使AP3D@0.3/APBEV@0.5从88.36/88.11降至53.90/53.16；保持每帧gate数值分布并随机置换空间位置时，三个固定种子的平均结果进一步降至21.29/21.01。这支持该模型对gate与局部特征的空间对应关系的依赖。相比之下，同时关闭query与output的上下文增量，仅使上述两项指标分别下降0.015和0.009个百分点。这些固定权重干预与重新训练的组件消融分别报告。','',
        '### Suggested English wording','',
        'With all weights of the K-Radar v1 model fixed, replacing the predicted gate map with its frame-wise mean reduces AP3D at IoU 0.3 and APBEV at IoU 0.5 from 88.36/88.11 to 53.90/53.16. Permuting gate values within each frame while preserving their distribution yields average scores of 21.29/21.01 across three fixed seeds. These interventions support the model’s dependence on spatial correspondence between gates and local features. In contrast, jointly removing the query and output context increments decreases the two metrics by only 0.015 and 0.009 percentage points. We distinguish these fixed-weight interventions from retrained component ablations.','',
        '## 6. 全部天气的六项指标','']
    for w,name in zip(WEATHERS,WEATHER_NAMES):
        lines+=['### '+name+f"（{r['baseline'][w]['frames']}帧）",'']+table(w)+['']
    lines+=['## 7. 文件来源','',
        '- 原始结果：`analysis_exports/objdec_kradar_v1_interventions_260923/results.json`及`metrics.log`。',
        '- 完整机器可读表：`reporting_260924/all_conditions_metrics.csv`，含384项AP及配对差值。',
        '- 预测数量诊断：`reporting_260924/prediction_count_and_score_diagnostics.csv`。',
        '- 本次核验：`reporting_260924/collection_audit.json`；原始脚本、模型权重与配置未改。',
        '- 本文更新状态与分析，不启动额外训练或推理，也不调整阈值或选模。','']
    report=ROOT/'results/objdec_kradar_v1_interventions_results_260924.md'
    report.write_text('\n'.join(lines))
    write(OUT/'collection_audit.json',dict(passed=True,frames=len(indices),cases=CASES,metric_cells=len(all_rows),
        weather_counts=dict(collections.Counter(frame_weathers)),sedan_gt_boxes=gt_count,
        source_hashes_verified=True,checkpoint_verified=True,baseline_max_difference_pp=max(abs(x) for x in check['differences'].values()),
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in chunks+[HERE/'results.json',HERE/'status.json',Path(__file__).resolve()]},
        new_inference=False,extra_diagnostics='Post-NMS score/count summaries only; not official TP/FP or recall.',report=str(report)))
    print(report,flush=True)


if __name__=='__main__':main()
