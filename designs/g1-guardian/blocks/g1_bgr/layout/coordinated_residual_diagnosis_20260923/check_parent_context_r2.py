#!/usr/bin/env python3
"""Held complete-parent audit bound to the smaller six-cut candidate."""
import hashlib
from pathlib import Path


def main():
    original = Path(__file__).resolve().with_name('check_parent_context.py')
    text = original.read_text()
    assert hashlib.sha256(original.read_bytes()).hexdigest() == '87bd81c9a8b9517139e44203eafcd40b032033232e0ffcb0ea7f6f0578d4fba2'
    for before, after, count in (
        ('bgr-dvbe-cuts-candidate-20260923-r1', 'bgr-dvbe-cuts-candidate-20260923-r2', 2),
        ('dfcd9e5a5c309c6f490c09aa25b71f3a4294c1acabc4cfc723010f53a283555a',
         'f4d14755511ec73220c3afdcd211ee6547e0eb025d4615a30a4919c7d0e819c7', 1)):
        assert text.count(before) == count
        text = text.replace(before, after)
    scope = dict(__file__=str(Path(__file__).resolve()), __name__='six_cut_parent_context')
    exec(compile(text, str(original), 'exec'), scope)
    scope['main']()


if __name__ == '__main__':
    main()
