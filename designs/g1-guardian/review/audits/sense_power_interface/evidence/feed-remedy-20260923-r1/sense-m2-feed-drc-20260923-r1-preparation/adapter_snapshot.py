#!/usr/bin/env python3
"""Unchanged stock decks with two bounded 120-second isolated block checks."""
import sys
from pathlib import Path


def main():
    audits = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(audits))
    original = audits/'run_core_candidate_drc.py'
    text = original.read_text()
    old = '120<=a.main_watchdog<=900 and 300<=a.maximal_watchdog<=1800'
    assert text.count(old) == 1
    text = text.replace(old, 'a.main_watchdog==120 and a.maximal_watchdog==120')
    output = Path(sys.argv[sys.argv.index('--output')+1])
    prep = output.with_name(output.name+'-preparation'); assert not prep.exists(); prep.mkdir(parents=True)
    derived = prep/'derived_stock_drc.py'; derived.write_text(text)
    (prep/'run_core_maximal_only.py').write_bytes((audits/'run_core_maximal_only.py').read_bytes())
    (prep/'adapter_snapshot.py').write_bytes(Path(__file__).read_bytes())
    namespace = {'__file__': str(derived), '__name__': 'm2_feed_drc_derivative'}
    exec(compile(text, str(derived), 'exec'), namespace); namespace['main']()


if __name__ == '__main__': main()
