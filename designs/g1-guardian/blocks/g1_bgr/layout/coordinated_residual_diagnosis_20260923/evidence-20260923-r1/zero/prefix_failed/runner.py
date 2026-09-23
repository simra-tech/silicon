#!/usr/bin/env python3
"""Held conditional OP source with CPU48 and successor allocation gates only."""
import hashlib
from pathlib import Path


def main():
    original = Path(__file__).resolve().parent.parent/'coordinated_dvbe_remedy_20260923/run_op.py'
    text = original.read_text()
    assert hashlib.sha256(original.read_bytes()).hexdigest() == 'd41717067404a74b16566facd75e86437aa6f3859bed3d0448750c5593fc0a56'
    for before, after in (('choices=(0,), default=0', 'choices=(48,), default=48'),
                          ("gate['project_cpu_budget'] >= 43", "gate['project_cpu_budget'] >= 56")):
        assert text.count(before) == 1
        text = text.replace(before, after)
    scope = dict(__file__=str(Path(__file__).resolve()), __name__='held_OP_cpu48')
    exec(compile(text, str(original), 'exec'), scope)
    scope['main']()


if __name__ == '__main__':
    main()
