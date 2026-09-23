#!/usr/bin/env python3
"""Strict source-held stock LVS; adapt only the isolated candidate status."""
import sys
from pathlib import Path
from screen_sense_dual_gate_proposal import sha
from build_sense_m2_feed_remedy import STATUS


def main():
    original = Path(__file__).with_name('run_sense_dual_gate_lvs.py')
    assert sha(original) == '72031707e91e1613bb0d581b1b6b7480d6b895508c2962bc548cf09381ef4535'
    text = original.read_text()
    old = "candidate['status'] == 'passed source-held dual-ended gate geometry'"
    assert text.count(old) == 1
    text = text.replace(old, "candidate['status'] == "+repr(STATUS))
    output = Path(sys.argv[sys.argv.index('--output')+1])
    prep = output.with_name(output.name+'-preparation'); assert not prep.exists(); prep.mkdir(parents=True)
    derived = prep/'derived_stock_lvs.py'; derived.write_text(text)
    (prep/'adapter_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (prep/'original_sha256.txt').write_text(sha(original)+'\n')
    namespace = {'__file__': str(derived), '__name__': 'm2_feed_lvs_derivative'}
    exec(compile(text, str(derived), 'exec'), namespace); namespace['main']()


if __name__ == '__main__': main()
