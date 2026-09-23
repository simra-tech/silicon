#!/usr/bin/env python3
"""Held builder, exact six-upper-cut count for the revised passed ledger."""
import hashlib
from pathlib import Path


def main():
    original = Path(__file__).resolve().with_name('build_dvbe_cuts.py')
    text = original.read_text()
    assert hashlib.sha256(original.read_bytes()).hexdigest() == '7c16b7c3b4428911f63569457ee303ed35c93732de1faba97b20ebe2b0a6f757'
    for before, after in (("sum(r['layer'] in CUTS for r in ledger) == 32", "sum(r['layer'] in CUTS for r in ledger) == 26"),
                          ('added_cuts=32', 'added_cuts=26')):
        assert text.count(before) == 1
        text = text.replace(before, after)
    scope = dict(__file__=str(Path(__file__).resolve()), __name__='six_upper_cut_builder')
    exec(compile(text, str(original), 'exec'), scope)
    scope['main']()


if __name__ == '__main__':
    main()
