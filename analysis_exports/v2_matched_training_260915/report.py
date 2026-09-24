"""Refresh a clearly labelled report as each independent long run completes."""
import csv
import datetime
import fcntl
import io
import json
from common import HERE, ROOT, REFERENCE, CONDITIONS, WEATHER, records, save

with (HERE/'report.lock').open('w') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    pre=json.loads((HERE/'preflight.json').read_text())
    strong=json.loads((REFERENCE/'strong_evaluation.json').read_text())
    metrics={'Strong (existing)':strong}
    statuses={}
    for method in ['asf','l4dr']:
        path=HERE/method/'status.json'
        statuses[method]=json.loads(path.read_text()) if path.exists() else {'status':'not_started'}
        path=HERE/method/'evaluation.json'
        if path.exists():
            value=json.loads(path.read_text())
            if value['status']=='complete':metrics[method.upper()+' (local, 11 epochs)']=value
    def metric(source,cls,iou,group='all',kind='3d'):
        c=next(x for x in source['metrics'][group]['classes'] if x['cls']==cls)
        return c[kind][c['iou'].index(iou)]
    def table(header,rows):
        return '\n'.join(['| '+' | '.join(header)+' |','| '+' | '.join(['---']*len(header))+' |']+
            ['| '+' | '.join(map(str,row))+' |' for row in rows])
    summary_rows=[]
    for method,state in statuses.items():
        summary_rows.append([method.upper(),state['status'],state.get('completed_epochs',0),
            str(state.get('global_step',0))+'/79123',f"{state.get('training_wall_seconds',0)/3600:.2f}",state.get('gpu','—')])
    text=['# K-Radar v2：ASF / L4DR 按 Strong 训练预算本地复现','',
        '更新：'+datetime.datetime.now().astimezone().isoformat(),'',
        '作者已选择：**同训练集、11 轮、有效 batch=2，另记录实际单卡训练耗时**。'
        '本次是新增本地训练对照；此前官方结果与本次结果分别保存。','',
        table(['任务','状态','完成轮数','完成更新步数','已完成轮训练小时','GPU'],summary_rows),'',
        '## 已核验的预算与初始化','',
        '- 训练 14,386 帧，测试 13,727 帧。ASF、L4DR 原生标签解析器逐帧 GT 完全一致；测试 GT 与 Strong 归档一致。',
        '- 每轮 7,193 步，共 79,123 次更新，158,246 次训练样本呈现。batch=2、FP32、seed=20250215。',
        '- AdamW，lr=0.001，min_lr=0.0001，weight_decay=0.01；保留 Strong 原始逐步 cosine 调度（T_max=7193，不在轮间重置）。',
        '- ASF：原生 A2Fusion + SCL，沿用 Strong 同一组官方单模态编码器；编码器固定参数逐项匹配 Strong，全部保留状态严格加载。融合模块和检测头重新初始化；FREEZE=True、FREEZE_BN=False。',
        '- L4DR：原生双类别 MGF + PointNet / BiDF 结构，从头训练全部模块；不加载已完整训练的官方 detector checkpoint。不为凑预算更改网络宽度或骨干。',
        '- 两者使用 Strong 相同的雷达文件路径，保留各自原生采样、体素化和输入通道。ASF 为 C+L+R，L4DR 为 L+R。',
        '- 11 轮后只评最后 checkpoint；统一 revised evaluator、conf>0.3、NMS=0.01。输出 Total、七天气、昼夜和道路完整结果。',
        '- 只保留一份最新可恢复 checkpoint；更新时原子替换。训练结束自动全量推理、评分并刷新本表。','',
        '**可比性边界：** 这是相同样本与优化步数的训练预算，不能写成相同 FLOPs、相同 GPU 小时或相同总预训练成本。'
        'ASF/Strong 依赖已有单模态预训练；L4DR 此轮是原生网络从头训练且缩短为 11 轮，公开配置默认 35 轮。'
        '因此不能用这个受限预算结果代替 L4DR 的官方充分训练结果，也不能预设复现分数应下降。','',
        f"Strong 原日志包含 epoch 0–10 共 11 轮，训练进度条累计约 {pre['budget']['historical_strong_training_wall_hours']:.2f} 小时。"
        '历史加载使用 workers=0；本次用 4 个 worker 并解除点云缓存，因此历史墙钟不能直接当成模型计算量。'
        '本次 training_wall_seconds 记录单卡训练循环耗时（含加载，不含末轮评测），对应占用一张卡的训练 GPU-hours；不代表 CUDA 内核活跃时间。','',
        '## 当前完整结果','',
        '仅列已经完成全量评测的运行。尚在训练的任务不填估计 AP。','']
    rows=[]
    for model,source in metrics.items():
        values=[]
        for iou in [.3,.5]:
            vv=[metric(source,c,iou) for c in ['sed','bus']]
            values += vv+[sum(vv)/2]
        rows.append([model]+[f'{v:.2f}' for v in values])
    text += [table(['方法','Sedan@0.3','Bus@0.3','Mean@0.3','Sedan@0.5','Bus@0.5','Mean@0.5'],rows),'',
        '此前官方参考：ASF 官方结果归档两类均值为 66.55 / 41.57；L4DR 官方双类别 checkpoint 本地统一评测为 69.48 / 48.23。'
        'ASF 的归档数字并非上一轮在本地重新推理其 checkpoint 得到。','',
        '## 分天气','']
    for iou in [.3,.5]:
        wr=[]
        for cls in ['sed','bus']:
            for model,source in metrics.items():
                wr.append([cls,model]+[('—' if cls=='bus' and group=='fog' else f'{metric(source,cls,iou,group):.2f}')
                    for group in ['all']+WEATHER])
        text += [f'AP3D@{iou}', '',table(['类别','方法','Total','Normal','Light snow','Heavy snow','Rain','Sleet','Overcast','Fog'],wr),'']
    text += ['## 记录与复现','',
        '- [运行目录与命令](../analysis_exports/v2_matched_training_260915/README.md)',
        '- [数据、预算与配置核验](../analysis_exports/v2_matched_training_260915/preflight.json)',
        '- [ASF 当前状态](../analysis_exports/v2_matched_training_260915/asf/status.json)',
        '- [L4DR 当前状态](../analysis_exports/v2_matched_training_260915/l4dr/status.json)',
        '- [官方权重统一评测报告](taskdec_v2_l4dr_aligned_evaluation_260915.md)','']
    path=ROOT/'results/taskdec_v2_matched_training_260915.md';path.write_text('\n'.join(text))
    out=[]
    for method,source in metrics.items():
        for group in CONDITIONS:
            for cls in ['sed','bus']:
                for kind in ['3d','bev']:
                    for iou in [.3,.5,.7]:
                        out.append(dict(method=method,condition=group,cls=cls,metric=kind,iou=iou,
                            ap=metric(source,cls,iou,group,kind)))
    buf=io.StringIO();writer=csv.DictWriter(buf,fieldnames=list(out[0]));writer.writeheader();writer.writerows(out)
    (ROOT/'results/taskdec_v2_matched_training_260915.csv').write_text(buf.getvalue())
    save(HERE/'summary_status.json',dict(status='complete' if all(s['status']=='complete' for s in statuses.values()) else 'in_progress',
        runs={k:s['status'] for k,s in statuses.items()},report=str(path)))
    print('Report refreshed',path)
