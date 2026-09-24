"""Fetch one author-published dual-class checkpoint and verify its LFS digest."""
import hashlib
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent
DEST = Path('/home/hongsheng/L4DR/checkpoints/L4DR-KRadar-v2.1-model_30.pt')
REV = '4f65460867a61a704a2290ff0ca2e8d05b463312'
URL = f'https://huggingface.co/hx24/L4DR_KRadar2.1/resolve/{REV}/model_30.pt'
EXPECTED_SHA = 'ccdc151a0c16185be8ab1801affed1f71fd6f63ae6f3c2fbf94c30346a0d8180'
EXPECTED_SIZE = 248566281


def main():
    part = DEST.with_suffix('.pt.part')
    if not DEST.exists():
        with urllib.request.urlopen(URL, timeout=90) as response, part.open('wb') as output:
            while True:
                block = response.read(8 * 1024 * 1024)
                if not block:
                    break
                output.write(block)
        assert part.stat().st_size == EXPECTED_SIZE
        assert hashlib.sha256(part.read_bytes()).hexdigest() == EXPECTED_SHA
        part.replace(DEST)
    assert DEST.stat().st_size == EXPECTED_SIZE
    assert hashlib.sha256(DEST.read_bytes()).hexdigest() == EXPECTED_SHA
    provenance = dict(source=URL, revision=REV, path=str(DEST), sha256=EXPECTED_SHA,
        bytes=EXPECTED_SIZE, author_repository='https://github.com/ylwhxht/L4DR',
        note='model.pt and model_30.pt in this revision have identical LFS hashes; only one copy downloaded.')
    (HERE/'checkpoint_source.json').write_text(json.dumps(provenance, indent=2)+'\n')
    print(json.dumps(provenance), flush=True)


if __name__ == '__main__':
    main()
