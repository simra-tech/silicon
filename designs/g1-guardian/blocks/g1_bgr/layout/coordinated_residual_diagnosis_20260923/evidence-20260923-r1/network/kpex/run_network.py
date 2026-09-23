#!/usr/bin/env python3
"""Unchanged qualified metal worker; CPU48 scheduling adapter only."""
import hashlib
from pathlib import Path


def main():
    original = Path(__file__).resolve().parent.parent/'coordinated_return_remedy/run_candidate_metal.py'
    text = original.read_text()
    assert hashlib.sha256(original.read_bytes()).hexdigest() == '63cfee289f9397e0de72200e1bdc8b24e9f9cd74e4949bd817c3ff8f6e6edede'
    replacements = [
        ('next(iter(os.sched_getaffinity(0))) in range(4)', 'next(iter(os.sched_getaffinity(0))) == 48'),
        ("worker = Path(__file__).with_name('extract_metal_r.py')", "worker = Path(__file__).resolve().parent.parent/'coordinated_return_remedy/extract_metal_r.py'")]
    for before, after in replacements:
        assert text.count(before) == 1
        text = text.replace(before, after)
    scope = dict(__file__=str(Path(__file__).resolve()), __name__='held_metal_cpu48')
    exec(compile(text, str(original), 'exec'), scope)
    return scope['main']()


if __name__ == '__main__':
    raise SystemExit(main())
