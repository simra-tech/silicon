#!/usr/bin/env python3
"""Export compact portable evidence from completed runs; retain bulk artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', nargs='+', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[5]
    args.output.mkdir(parents=True, exist_ok=True)
    permitted = {'summary.json', 'provenance.json', 'analysis.json', 'step_characterization.json',
                 'same_deck_replay.json', 'recovery_validation.json', 'host_parity.json',
                 'controlled_solver_preflight.json', 'failed_solver_diagnostic_preflight.json',
                 'partition_comparison.json', 'solver_comparison.json', 'runner.py', 'driver.py', 'replay_driver.py',
                 'preparation.json', 'preparer.py', 'declared_clock_difference.diff',
                 'declared_output_difference.diff', 'declared_draw_audit_difference.diff',
                 'non_bgr_inventory.json', 'prelaunch_reference_bindings.json',
                 'declared_substitution_difference.diff', 'substitution_structure_audit.json',
                 'declared_prefix_difference.diff', 'prefix_structure_audit.json',
                 'declared_fullhot_difference.diff', 'declared_runner_difference.diff',
                 'fullhot_structure_audit.json', 'declared_calibration_difference.diff',
                 'recovery_contract.json', 'recovery_wrapper.py',
                 'population_inventory.json', 'declared_population_deck_difference.diff',
                 'declared_population_source_difference.json',
                 'declared_population_transient_difference.diff'}
    for run in args.runs:
        # Do not resolve: source is a portable repository-relative run identity,
        # even when its directory is an ignored external-storage symlink.
        logical = run if run.is_absolute() else root / run
        relative = logical.relative_to(root)
        assert (logical / 'summary.json').is_file() and (logical / 'provenance.json').is_file()
        destination = args.output / logical.name
        destination.mkdir(exist_ok=False)
        files = []
        for path in sorted(logical.iterdir()):
            if not path.is_file():
                continue
            size = path.stat().st_size
            entry = {'name': path.name, 'sha256': sha(path), 'bytes': size}
            copy = (path.name in permitted or path.name.endswith('.dat.archive.json')
                    or path.name.startswith(('resume_configuration.', 'resume_driver.', 'recovery_map.')))
            if copy:
                # A frozen17-sample BGR parent includes both full2842 vectors.
                assert size < 16*1024*1024, 'Unexpectedly large compact artifact'
                text = path.read_text()
                assert not re.search(r'/(?:home/|Users/|opt/sim/)', text), 'Machine-specific path must not enter public export'
                shutil.copyfile(str(path), str(destination / path.name))
                assert sha(destination / path.name) == entry['sha256']
            entry['exported'] = copy
            files.append(entry)
        manifest = {'logical_run': str(relative), 'artifacts': files,
                    'scope': 'Exact compact summaries, provenance and runner snapshots; bulk artifacts retained separately by logical run ID and hashes. Missing local bulk data is not a rerun or an omitted failure. Source/model/tool/image/PDK identities and command arguments remain in provenance.json.',
                    'bulk_artifact_total_bytes': sum(f['bytes'] for f in files if not f['exported']),
                    'exported_bytes': sum(f['bytes'] for f in files if f['exported']),
                    'exporter_sha256': sha(Path(__file__))}
        (destination / 'artifact_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(str(relative), manifest['exported_bytes'], 'exported bytes')


if __name__ == '__main__':
    main()
