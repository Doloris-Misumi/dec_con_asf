"""Read-only job observer; writes only progress/report artifacts, never signals jobs."""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import json
import math
import os
import subprocess
from pathlib import Path
import time

BASE = Path(__file__).resolve().parent
FORMAL = BASE / 'controlled_80ep'
PROJECT = BASE.parents[1]
PROGRESS = PROJECT / 'results/taskdec_v2x_radar_v_progress_260916.md'
BEGIN = '<!-- V2X_LIVE_STATUS_BEGIN -->'
END = '<!-- V2X_LIVE_STATUS_END -->'
ZONE = timezone(timedelta(hours=8))


def read(path, fallback=None):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback


def write(path, data):
    temporary = path.with_suffix(path.suffix + '.observer.tmp')
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False))
    os.replace(temporary, path)


def process(pid, expected):
    if not pid:
        return {'verified_live': False, 'reason': 'no_pid'}
    try:
        cmd = (Path('/proc') / str(pid) / 'cmdline').read_bytes().replace(b'\0', b' ').decode()
        stat = (Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()
        return {'verified_live': expected in cmd and stat[0] != 'Z',
                'pid': pid, 'state': stat[0], 'start_ticks': int(stat[19]), 'command': cmd.strip()}
    except FileNotFoundError:
        return {'verified_live': False, 'pid': pid, 'reason': 'process_missing'}
    except (PermissionError, OSError) as exc:
        # Observation failure is unknown, not terminal.
        return {'verified_live': None, 'pid': pid, 'reason': str(exc)}


def completed_table(runs):
    lines = [r'\begin{tabular}{lrrrr}', r'\hline',
             r'Method (C+L+R) & Vehicle & Pedestrian & Cyclist & Mean \\', r'\hline']
    count = 0
    for name in ['concat', 'patch', 'taskdec']:
        result = read(FORMAL / name / 'final_best.json')
        if not result:
            continue
        values = result['results']['test_deduplicated']['metrics']
        nums = [values['V2X/' + cls + '_3D_moderate_strict'] for cls in ['Vehicle', 'Pedestrian', 'Cyclist']]
        nums.append(values['V2X/Overall_3D_moderate'])
        if not all(math.isfinite(v) for v in nums):
            raise ValueError('Nonfinite final AP: ' + name)
        lines.append(name + ' & ' + ' & '.join('%.2f' % v for v in nums) + r' \\')
        count += 1
    lines += [r'\hline', r'\end{tabular}',
              '% Local deduplicated test; strict moderate 3D AP_R40; validation-selected best checkpoint.',
              '%% Completed rows: %d/3. Missing rows are unfinished, never zero AP.' % count]
    # Separate export avoids mutating any frozen training or evaluator source.
    (FORMAL / 'paper_main_table.tex').write_text('\n'.join(lines) + '\n')


def observe():
    stamp = datetime.now(ZONE)
    controller = read(FORMAL / 'controller_status.json', {})
    controller_live = process(controller.get('pid'), controller.get('command_match', 'v2x_taskdec.launch_controlled'))
    cfg = read(FORMAL / 'config.json')
    validation_records = {}
    for name in ['taskdec', 'concat', 'patch']:
        validation_records[name] = [record for epoch in cfg['val_epochs']
            for record in [read(FORMAL / name / ('val_epoch_%03d.json' % epoch))] if record]
    pooled = [record for records in validation_records.values() for record in records]
    fallback_eval = max([r['evaluation_seconds'] for r in pooled] or [900.])
    fallback_inference = max([r['inference_seconds'] for r in pooled] or [180.])
    runs = {}
    for name in ['taskdec', 'concat', 'patch']:
        status = read(FORMAL / name / 'status.json', {'status': 'pending'})
        launch = read(FORMAL / name / 'launch.json', {})
        live = process(status.get('pid', launch.get('pid')), 'v2x_taskdec.train --variant ' + name)
        completed = status.get('completed_epochs', 0)
        elapsed = status.get('train_seconds', 0.)
        epochs = status.get('epochs', 80)
        fallback = read(BASE / ('throughput_' + name + '.json'))['mean_seconds'] * 4196
        if completed and elapsed:
            seconds_epoch, basis = elapsed / completed, 'completed_training_epochs'
        elif status.get('step', 0) >= 100:
            seconds_epoch = status['epoch_elapsed_seconds'] / status['step'] * 4196
            basis = 'provisional_partial_epoch'
        else:
            seconds_epoch, basis = fallback, 'engineering_single_job_throughput'
        remaining = max(0., (epochs - completed) * seconds_epoch)
        if status.get('status') == 'training':
            remaining = max(0., remaining - status.get('epoch_elapsed_seconds', 0.))
        if status.get('status') == 'complete':
            remaining = 0.
        runs[name] = dict(status=status, process=live, seconds_per_training_epoch=seconds_epoch,
                          timing_basis=basis, remaining_training_seconds=remaining)
        records = validation_records[name]
        mean_eval = sum(r['evaluation_seconds'] for r in records) / len(records) if records else fallback_eval
        mean_inference = sum(r['inference_seconds'] for r in records) / len(records) if records else fallback_inference
        pending_val = len(cfg['val_epochs']) - len(records)
        # Four inference passes: best/last x original val/test. Each prediction
        # set has original and deduplicated evaluation, hence eight metric calls.
        final_remaining = 0.
        if status.get('status') != 'complete':
            for tag in ['best', 'last']:
                if not (FORMAL / name / ('final_' + tag + '.json')).exists():
                    final_remaining += 2 * mean_inference + 4 * max(0., mean_eval - mean_inference)
        runs[name].update(measured_validation_seconds=mean_eval,
                          validation_timing_basis='own_completed_validation' if records else 'other_variants_or_conservative_fallback',
                          pending_scheduled_validations=pending_val,
                          remaining_scheduled_validation_seconds=pending_val * mean_eval,
                          remaining_final_evaluation_seconds=final_remaining)
    # Queue is fixed: GPU1 concat then patch. This remains a forecast, never an
    # achieved end time. A 25% allowance is explicit and includes no guarantee.
    def with_allowance(row):
        return 1.25 * (row['remaining_training_seconds'] + row['remaining_scheduled_validation_seconds'] +
                       row['remaining_final_evaluation_seconds'])
    if controller.get('assignment', {}).get('patch') == 2:
        remainder = max(with_allowance(row) for row in runs.values())
    else:
        remainder = max(with_allowance(runs['taskdec']), with_allowance(runs['concat']) + with_allowance(runs['patch']))
    projection = stamp + timedelta(seconds=remainder)
    result = dict(updated_at=stamp.isoformat(), observer_pid=os.getpid(), controller_process=controller_live,
                  runs=runs, forecast_finish_with_25percent_allowance=projection.isoformat(),
                  forecast_note='Completed-epoch training time plus measured validation and final evaluation estimates, with 25% allowance. Pending patch uses engineering training throughput and observed validation from other variants. No protocol changes.')
    write(FORMAL / 'runtime_observation.json', result)
    lines = [BEGIN, '## 自动运行观察（每五分钟更新）', '', '核查时间：' + stamp.isoformat(), '',
             '| 实验 | 状态 | PID已验证存活 | 已完成轮数 | 当前批次 | 训练秒/轮及依据 |',
             '|---|---|---|---:|---:|---|']
    for name, row in runs.items():
        state = row['status']
        lines.append('| %s | %s | %s | %d | %d | %.1f (%s) |' %
                     (name, state['status'], row['process']['verified_live'], state.get('completed_epochs', 0),
                      state.get('step', 0), row['seconds_per_training_epoch'], row['timing_basis']))
    lines += ['', '当前排队顺序下的条件排期（显式计入剩余定期验证、最佳/末轮最终评测，再加25%预留）：' + projection.isoformat() + '。',
              '此时间是预测，首轮未结束时依据部分批次；不代表训练或评测完成。',
              '验证开销优先使用该组已完成评测的均值；未启动组参考其他组实测。训练缓存、预测数量及并行干扰变化会影响排期。',
              '完整状态与真实进程证据：`analysis_exports/v2x_taskdec_260916/controlled_80ep/runtime_observation.json`。',
              '结果表与全部指标：同目录 `results.md` / `complete_metrics.csv`；论文LaTeX完整表：`paper_main_table.tex`。', END]
    content = PROGRESS.read_text()
    block = '\n'.join(lines)
    if BEGIN in content and END in content:
        left, rest = content.split(BEGIN, 1)
        _, right = rest.split(END, 1)
        content = left + block + right
    else:
        marker = '## 启动时状态（历史记录，不代表当前状态）'
        content = content.replace(marker, block + '\n\n' + marker, 1)
    temporary = PROGRESS.with_suffix('.observer.tmp')
    temporary.write_text(content);os.replace(temporary, PROGRESS)
    completed_table(runs)
    all_done = all(r['status']['status'] == 'complete' for r in runs.values())
    stopped = controller_live['verified_live'] is False and all(r['process']['verified_live'] is False for r in runs.values())
    accounting_done = all_done and controller.get('status') == 'complete' and controller_live['verified_live'] is False
    result['observer_disposition'] = ('waiting_for_controller_accounting' if all_done else
                                      ('needs_attention' if stopped else 'monitoring'))
    if accounting_done:
        with (FORMAL / 'delivery_audit.log').open('w') as log:
            audit = subprocess.run([str(PROJECT / 'v2x_taskdec/.venv/bin/python'),
                                    str(BASE / 'audit_delivery.py')], stdout=log, stderr=subprocess.STDOUT)
        result['delivery_audit_exit_code'] = audit.returncode
        result['observer_disposition'] = 'await_final_review' if audit.returncode == 0 else 'delivery_audit_needs_attention'
    write(FORMAL / 'runtime_observation.json', result)
    return result, accounting_done or (stopped and not all_done)


def main():
    parser = argparse.ArgumentParser();parser.add_argument('--once', action='store_true');args = parser.parse_args()
    handle = open(FORMAL / '.observer.lock', 'a');fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    signature = None
    while True:
        result, terminal = observe()
        latest = tuple((name, row['status']['status'], row['status'].get('completed_epochs', 0)) for name, row in result['runs'].items())
        if latest != signature:
            print(result['updated_at'], latest, result['observer_disposition'], flush=True);signature = latest
        if args.once or terminal:
            return
        time.sleep(300)


if __name__ == '__main__':
    main()
