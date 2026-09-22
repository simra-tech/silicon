#!/usr/bin/env python3
"""Export portable manifest-based OSC/T2F evidence without copying bulk waves."""
import argparse
import json
from pathlib import Path
import re
import shutil
from export_run_evidence import sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs', type=Path, nargs='+', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    root = Path(__file__).resolve().parents[5]
    a.output.mkdir(exist_ok=True, parents=True)
    for path in a.runs:
        run = path if path.is_absolute() else root/path
        relative = run.relative_to(root)
        manifest = json.loads((run/'manifest.json').read_text())
        assert manifest.get('cases'), 'No completed or failed attempted case ledger'
        destination = a.output/run.name
        destination.mkdir(exist_ok=False)
        artifacts = []
        for file in sorted(run.iterdir()):
            if not file.is_file():
                continue
            entry = {'name': file.name, 'sha256': sha(file), 'bytes': file.stat().st_size,
                     'exported': file.name in ['manifest.json', 'protocol.json'] or file.suffix == '.py'}
            if entry['exported']:
                assert entry['bytes'] < 16*1024*1024, 'Unexpectedly large compact evidence'
                assert not re.search(r'/(?:home/|Users/|opt/sim/)', file.read_text())
                shutil.copyfile(str(file), str(destination/file.name))
                assert sha(destination/file.name) == entry['sha256']
            artifacts.append(entry)
        receipt = {'logical_run': str(relative), 'artifacts': artifacts,
                   'scope': 'Exact attempted-case ledger, commands, source/model/runtime hashes and full sampled-parameter arrays; bulk decks/logs/waves retained separately by portable logical ID and hash. No omitted numerical or electrical failures.',
                   'exporter_sha256': sha(Path(__file__))}
        (destination/'artifact_manifest.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print(str(relative), sum(r['bytes'] for r in artifacts if r['exported']), 'exported bytes')


if __name__ == '__main__':
    main()
