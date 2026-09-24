"""Operational handoff: preserve live training PIDs; move pending patch to GPU2.

Does not modify any frozen training source, configuration, or initialization.
Only the old scheduling process is terminated, never its training children.
"""
import argparse
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
sys.path.insert(0, str(ROOT))
from v2x_taskdec.experiment import FORMAL, atomic_json, now, sha, verify_sources
from v2x_taskdec.report import main as report


def read(path):
    return json.loads(path.read_text())


def identity(pid):
    try:
        proc = Path('/proc') / str(pid)
        command = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode().strip()
        stat = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        return dict(pid=pid, command=command, state=stat[0], start_ticks=int(stat[19]))
    except FileNotFoundError:
        return None


def alive(record):
    current = identity(record['pid'])
    return bool(current and current['start_ticks'] == record['start_ticks']
                and current['state'] != 'Z' and current['command'] == record['command'])


def preflight():
    verify_sources()
    asf = read(ROOT / 'analysis_exports/v2_matched_training_260915/asf/status.json')
    assert asf['status'] == 'complete' and asf['evaluation_samples'] == 13727
    controller = read(FORMAL / 'controller_status.json')
    old = identity(controller['pid'])
    assert old and old['command'].endswith('-m v2x_taskdec.launch_controlled') and alive(old)
    assert controller['schedule'] == {'0': [], '1': ['patch']}
    assert not (FORMAL / 'patch/status.json').exists()
    assert not (FORMAL / 'patch/last.pt').exists()
    adopted = {}
    for gpu, name in [('0', 'taskdec'), ('1', 'concat')]:
        launch = read(FORMAL / name / 'launch.json')
        record = identity(launch['pid'])
        assert record and record['command'].endswith('-m v2x_taskdec.train --variant ' + name)
        assert alive(record) and launch['gpu'] == int(gpu)
        assert controller['active'][gpu] == dict(pid=record['pid'], variant=name)
        adopted[name] = dict(record, gpu=int(gpu), started_at=launch['started_at'])
    return controller, old, adopted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight-only', action='store_true')
    args = parser.parse_args()
    handoff_lock = open(FORMAL / '.gpu2_handoff.lock', 'a')
    fcntl.flock(handoff_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    controller, old, adopted = preflight()
    if args.preflight_only:
        print(json.dumps(dict(status='passed',old_controller=old,adopted=adopted)), flush=True)
        return
    # Preserve the existing three independent resource checks, 20 s apart.
    snapshots = []
    for index in range(3):
        row = subprocess.check_output(['nvidia-smi', '-i', '2',
            '--query-gpu=memory.free,utilization.gpu', '--format=csv,noheader,nounits'], text=True)
        free, util = [int(x.strip()) for x in row.split(',')]
        assert free >= 26000 and util <= 30, 'GPU2 resource check failed'
        snapshots.append(dict(at=now(), free_mib=free, utilization=util))
        print('GPU2 resource sample', snapshots[-1], flush=True)
        if index < 2:
            time.sleep(20)
    controller, old, adopted = preflight()
    handoff = dict(request='User authorized pending patch on freed GPU2', at=now(),
        old_controller=old, previous_status=controller, preserved_training=adopted,
        new_assignment={'taskdec': 0, 'concat': 1, 'patch': 2},
        script_sha256=sha(__file__), resource_checks=snapshots,
        frozen_sources_verified=True, frozen_configuration_unchanged=True)
    atomic_json(FORMAL / 'gpu2_handoff.json', handoff)
    # Signal exactly the verified scheduler PID, not its process group.
    assert alive(old)
    os.kill(old['pid'], signal.SIGTERM)
    deadline = time.monotonic() + 10
    while alive(old):
        if time.monotonic() > deadline:
            raise RuntimeError('Old scheduler has not exited; refusing duplicate launch')
        time.sleep(.1)
    lock = open(FORMAL / '.controller.lock', 'a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert all(alive(record) for record in adopted.values()), 'Existing training process disappeared'
    controller.update(pid=os.getpid(), command_match=str(Path(__file__).resolve()),
        handoff_at=now(), previous_controller_pid=old['pid'],
        schedule={'0': [], '1': [], '2': ['patch']},
        assignment={'taskdec': 0, 'concat': 1, 'patch': 2}, status='running', updated_at=now())
    atomic_json(FORMAL / 'controller_status.json', controller)
    run = FORMAL / 'patch'
    run.mkdir(exist_ok=True)
    env = os.environ.copy()
    env.update(CUDA_VISIBLE_DEVICES='2', CUDA_HOME='/usr/local/cuda-11.3',
        OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', OPENBLAS_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
    command = ['nice', '-n', '10', str(ROOT / 'v2x_taskdec/.venv/bin/python'),
               '-u', '-m', 'v2x_taskdec.train', '--variant', 'patch']
    log = open(run / 'train.log', 'a')
    started = time.monotonic()
    child = subprocess.Popen(command, cwd=str(ROOT), env=env, stdout=log, stderr=subprocess.STDOUT)
    atomic_json(run / 'launch.json', dict(command=command, pid=child.pid, gpu=2,
        started_at=now(), resource_snapshot=snapshots[-1], controller_pid=os.getpid(),
        scheduling_change='Moved from pending GPU1 queue to GPU2 by explicit user request'))
    active = {str(r['gpu']): dict(pid=r['pid'], variant=name) for name, r in adopted.items()}
    active['2'] = dict(pid=child.pid, variant='patch')
    ended = {}
    controller.update(active=active, schedule={'0': [], '1': [], '2': []}, updated_at=now())
    atomic_json(FORMAL / 'controller_status.json', controller)
    handoff.update(status='handed_off', new_controller_pid=os.getpid(), patch_pid=child.pid,
                   old_queue_cancelled=True, existing_training_pids_unchanged=True)
    atomic_json(FORMAL / 'gpu2_handoff.json', handoff)
    print('Started patch on GPU2 PID', child.pid, '; preserved', adopted, flush=True)
    while active:
        for gpu, entry in list(active.items()):
            name = entry['variant']
            if name == 'patch':
                code = child.poll()
                if code is None:
                    continue
                log.close()
                cost = dict(pid=child.pid, exit_code=code, gpu=2,
                    wall_seconds=time.monotonic() - started, finished_at=now(),
                    accounting_method='subprocess_poll')
            else:
                if alive(adopted[name]):
                    continue
                state = read(FORMAL / name / 'status.json')
                complete = state.get('status') == 'complete'
                # An adopted non-child process has no waitpid exit code.
                # Preserve that fact; completion is checked from final artifacts.
                cost = dict(pid=entry['pid'], exit_code=None, gpu=int(gpu),
                    wall_seconds=(datetime.now().astimezone() - datetime.fromisoformat(adopted[name]['started_at'])).total_seconds(),
                    finished_at=now(), completion_status=state.get('status'),
                    accounting_method='adopted_process_exit_and_complete_status')
                code = 0 if complete else 1
            with open(FORMAL / name / 'process_costs.jsonl', 'a') as stream:
                stream.write(json.dumps(cost) + '\n')
            ended[name] = code
            del active[gpu]
            print('Finished', name, cost, flush=True)
        controller.update(active=active, ended=ended, updated_at=now())
        atomic_json(FORMAL / 'controller_status.json', controller)
        report()
        if active:
            time.sleep(60)
    controller.update(status='complete' if all(v == 0 for v in ended.values()) else 'finished_with_failures',
                      finished_at=now())
    atomic_json(FORMAL / 'controller_status.json', controller)
    report()


if __name__ == '__main__':
    main()
