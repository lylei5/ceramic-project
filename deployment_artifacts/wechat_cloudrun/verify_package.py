"""Verify all model and source bytes before starting the service."""
import hashlib
import json
from pathlib import Path


def verify():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / 'package-manifest.json').read_text())
    for name, expected in manifest['sha256'].items():
        digest = hashlib.sha256()
        with (root / name).open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        if digest.hexdigest() != expected:
            raise RuntimeError('Package checksum mismatch: ' + name)
    print('Package verified: step 114750, 57-bit protocol', flush=True)


if __name__ == '__main__':
    verify()
