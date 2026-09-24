"""Observe the existing downloader, verify pinned hashes, extract without overwrite.

Run outside the PID sandbox so /proc refers to the actual downloader processes.
This script never deletes archives and never launches training.
"""
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import time
import zipfile
import zlib

ROOT = Path('/home/hongsheng/datasets/V2X-Radar-V')
OUT = Path('/home/hongsheng/dec_con_asf/analysis_exports/v2x_taskdec_260916')
DEST = ROOT / 'extracted_260916'


def write_state(stage, **kw):
    data = dict(stage=stage, updated_at=datetime.datetime.now().astimezone().isoformat(),
                pid=os.getpid(), destination=str(DEST), **kw)
    p = OUT / 'data_preparation_status.json'
    q = p.with_suffix('.tmp')
    q.write_text(json.dumps(data, indent=2))
    q.replace(p)
    print(json.dumps(data), flush=True)


def matching_process(pid, needle):
    try:
        return needle in Path('/proc/{}/cmdline'.format(int(pid))).read_bytes().decode(errors='replace')
    except (OSError, ValueError, TypeError):
        return False


def wait_download():
    retries = 0
    while True:
        state = json.loads((ROOT / 'download_status.json').read_text())
        live = (matching_process(state.get('controller_pid'), 'run_download.py') or
                matching_process(state.get('aria2_pid'), '/usr/bin/aria2c'))
        if live:
            write_state('waiting_download', downloader_status=state.get('status'), retries=retries)
            time.sleep(60)
            continue
        if state.get('status') == 'complete':
            return
        # The downloader's flock also prevents a race with a separately resumed job.
        if retries >= 3:
            raise RuntimeError('Downloader terminal without completion after 3 resume attempts: ' + str(state))
        retries += 1
        write_state('resuming_download', retries=retries)
        with (ROOT / 'download.log').open('ab') as log:
            subprocess.run([sys.executable, '-u', str(ROOT / 'run_download.py')],
                           stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        time.sleep(10)


def crc_file(path):
    crc = 0
    with path.open('rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
            crc = zlib.crc32(b, crc)
    return crc & 0xffffffff


def extract_archive(path):
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        names = set()
        # Full path/collision preflight before writing any member of this archive.
        for info in infos:
            rel = PurePosixPath(info.filename)
            if rel.is_absolute() or '..' in rel.parts or '\\' in info.filename:
                raise ValueError('Unsafe zip member: ' + info.filename)
            if info.filename in names or stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError('Duplicate or symlink member: ' + info.filename)
            names.add(info.filename)
            dest = DEST.joinpath(*rel.parts)
            if not dest.resolve().is_relative_to(DEST.resolve()):
                raise ValueError('Escaping destination: ' + str(dest))
            if dest.is_symlink():
                raise ValueError('Destination symlink: ' + str(dest))
            if dest.exists() and not info.is_dir():
                if not dest.is_file() or dest.stat().st_size != info.file_size or crc_file(dest) != info.CRC:
                    raise ValueError('Existing nonmatching file; refusing overwrite: ' + str(dest))
        count = 0
        for info in infos:
            dest = DEST / info.filename
            if info.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
                continue
            if not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                # Exclusive creation, ZipExtFile verifies CRC when fully consumed.
                with z.open(info) as src, dest.open('xb') as dst:
                    shutil.copyfileobj(src, dst, 8 * 1024 * 1024)
            if dest.stat().st_size != info.file_size:
                raise ValueError('Extracted size mismatch: ' + str(dest))
            count += 1
            if count % 5000 == 0:
                write_state('extracting', archive=path.name, files=count)
        return count


def validate_splits():
    data = DEST / 'V2X-Radar-V' / 'training'
    split_dir = DEST / 'ImageSets'
    splits = {}
    for name in ('train', 'val', 'test', 'trainval'):
        ids = (split_dir / (name + '.txt')).read_text().split()
        if len(set(ids)) != len(ids) or not all(i.isdigit() for i in ids):
            raise ValueError('Invalid/duplicate split IDs: ' + name)
        splits[name] = set(ids)
    for a, b in [('train', 'val'), ('train', 'test'), ('val', 'test')]:
        if splits[a] & splits[b]:
            raise ValueError('Overlapping splits: ' + a + '/' + b)
    if splits['trainval'] != splits['train'] | splits['val']:
        raise ValueError('trainval is not train union val')
    ids = splits['trainval'] | splits['test']
    counts = {}
    for group in ('image_2', 'velodyne', 'radar', 'calib', 'label_2'):
        files = list((data / group).iterdir())
        actual = {p.stem for p in files if p.is_file()}
        if actual != ids or len(files) != len(ids):
            raise ValueError('Missing/extra modality files: ' + group)
        counts[group] = len(files)
    return dict(split_counts={k: len(v) for k, v in splits.items()}, modality_counts=counts,
                dataset_root=str(data.parent), split_root=str(split_dir),
                scope='Archive SHA256, extraction CRC/size, split disjointness and modality path coverage; geometry pending')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / '.prepare_data.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        wait_download()
        manifest = json.loads((ROOT / 'download_manifest.json').read_text())
        checked = []
        for item in manifest['files']:
            p = ROOT / 'downloads' / item['name']
            write_state('verifying_sha256', archive=p.name)
            if p.stat().st_size != item['bytes']:
                raise ValueError('Archive size mismatch: ' + str(p))
            h = hashlib.sha256()
            with p.open('rb') as f:
                for b in iter(lambda: f.read(16 * 1024 * 1024), b''):
                    h.update(b)
            if h.hexdigest() != item['sha256']:
                raise ValueError('Archive SHA256 mismatch: ' + str(p))
            checked.append(dict(name=p.name, bytes=p.stat().st_size, sha256=h.hexdigest()))
        (OUT / 'archive_verification.json').write_text(json.dumps(checked, indent=2))
        DEST.mkdir(exist_ok=True)
        extracted = {}
        for item in manifest['files']:
            extracted[item['name']] = extract_archive(ROOT / 'downloads' / item['name'])
        report = validate_splits()
        report.update(archives=checked, extracted_files=extracted, revision=manifest['revision'])
        (OUT / 'data_integrity.json').write_text(json.dumps(report, indent=2))
        write_state('complete', **report)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        write_state('failed', error=repr(exc))
        raise
