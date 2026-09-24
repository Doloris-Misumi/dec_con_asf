"""Detach the two-run controller after both smoke tests pass."""
import datetime
import json
from pathlib import Path
import resource
import subprocess
import sys

here = Path(__file__).resolve().parent
root = here.parents[1]
assert not (here / 'controller_launch.json').exists(), 'Already launched; inspect existing controller.'
for name in ['taskdec', 'concat']:
    p = here / 'matched_80ep' / ('smoke_' + name)
    assert json.loads((p / 'status.json').read_text())['status'] == 'smoke_passed'
    assert json.loads((p / 'head_geometry_check.json').read_text())['passed']

def setup():
    resource.setrlimit(resource.RLIMIT_CORE, (0,0))

command = [sys.executable, '-u', str(here / 'controller.py')]
with (here / 'controller.log').open('x') as log:
    process = subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL, stdout=log,
        stderr=subprocess.STDOUT, start_new_session=True, preexec_fn=setup)
receipt = dict(pid=process.pid, started_at=datetime.datetime.now().astimezone().isoformat(),
               command=command, taskdec_gpu=3, concat_gpu=2, detached=True)
(here / 'controller_launch.json').write_text(json.dumps(receipt,indent=2) + '\n')
print(json.dumps(receipt,indent=2))
