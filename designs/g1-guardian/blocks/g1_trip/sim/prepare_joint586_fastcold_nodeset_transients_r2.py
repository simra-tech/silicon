#!/usr/bin/env python3
"""Version prepared-only pair for explicit fatal analysis-aborted inventory."""
import difflib
import json
from pathlib import Path
from prepare_joint586_fastcold_nodeset_transients import SIM, ROOT, ORIGINAL, PACKET, transform, sha
from result_directory import allocate_run


def main():
    target = SIM/'qualification/joint586-fastcold-nodeset-transients-contract-20260923-b.json'
    assert not target.exists()
    packet = json.loads(PACKET.read_text())
    body = (ORIGINAL/'population_transient.cir').read_text()
    for case in packet['cases']:
        old = SIM/'qualification'/case['run']
        assert not (old/'run.log').exists()
        case['run'] = case['run'][:-1]+'b'
        out = allocate_run(SIM, case['run'])
        for name, digest in packet['source_hashes'].items():
            assert sha(old/name) == digest
            (out/name).write_bytes((old/name).read_bytes())
        deck, audit = transform(body, case['run'], case['solver'], packet['guesses_original_printed_strings'])
        (out/'population_transient.cir').write_text(deck)
        (out/'transform_audit.json').write_text(json.dumps(audit, indent=2)+'\n')
        (out/'declared_initialization_difference.diff').write_text(''.join(difflib.unified_diff(
            body.splitlines(True), deck.splitlines(True), fromfile='originalFailedFast78001', tofile=case['solver']+'NodesetFullTransient')))
        case.update(deck_sha256=sha(out/'population_transient.cir'), transform_sha256=sha(out/'transform_audit.json'))
    for path in [PACKET, Path(__file__).resolve(), SIM/'run_joint586_fastcold_nodeset_transients_r2.py',
            SIM/'test_joint586_fastcold_nodeset_transients_r2.py']:
        packet['bindings_sha256'][str(path.relative_to(ROOT))] = sha(path)
    packet.update(adapter_sha256=sha(SIM/'run_joint586_fastcold_nodeset_transients_r2.py'),
        revision_scope='Prepared a remains unrun and unchanged. r2 adds explicit analysis-aborted fatal inventory only; electrical decks unchanged except fresh output destinations. Base runner.py and effective error_inventory_adapter.py both retained and hash-bound.')
    target.write_text(json.dumps(packet, indent=2)+'\n')
    print(target.relative_to(ROOT), sha(target))


if __name__ == '__main__':
    main()
