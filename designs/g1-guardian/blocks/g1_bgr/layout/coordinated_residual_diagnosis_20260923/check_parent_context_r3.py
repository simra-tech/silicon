#!/usr/bin/env python3
"""Six-cut candidate versus the exact current-digital routed parent."""
import hashlib
from pathlib import Path


def main():
    original = Path(__file__).resolve().with_name('check_parent_context.py')
    text = original.read_text()
    assert hashlib.sha256(original.read_bytes()).hexdigest() == '87bd81c9a8b9517139e44203eafcd40b032033232e0ffcb0ea7f6f0578d4fba2'
    changes = [
        ('bgr-dvbe-cuts-candidate-20260923-r1', 'bgr-dvbe-cuts-candidate-20260923-r2', 2),
        ('dfcd9e5a5c309c6f490c09aa25b71f3a4294c1acabc4cfc723010f53a283555a',
         'f4d14755511ec73220c3afdcd211ee6547e0eb025d4615a30a4919c7d0e819c7', 1),
        ('bgr-supply-context-candidate-20260923-r1/supply_context_native.gds',
         'digital-reroute-streamout-20260923-r1/signal_routed_native.gds', 1),
        ('b417a132626fd1d0f4cc8162c49449868f33096a8069bc7b90408864a0b0e5de',
         '9a52cc71122df8fcc56bbd3ec3e0842958e1f7eec0f73c64ed21a8e2c7ea1805', 1),
        ('paths = [parent, local, prior, overlay, preparation, routes, Path(__file__).resolve(),',
         "terminal_audit = bulk/'digital-reroute-terminals-20260923-r1/analysis.json'\n"
         "    terminal = json.loads(terminal_audit.read_text())\n"
         "    assert terminal['status'] == 'passed exact held terminal partition and physical ports'\n"
         "    assert terminal['inputs'][str(parent)] == sha(parent)\n"
         "    paths = [terminal_audit, parent, local, prior, overlay, preparation, routes, Path(__file__).resolve(),", 1),
        ("final_digital_reroute_context='not run; parent has previous digital geometry'",
         "final_digital_reroute_context='checked against exact9a52 current-digital rerouted geometry; no integration'", 1),
    ]
    for before, after, count in changes:
        assert text.count(before) == count, before
        text = text.replace(before, after)
    scope = dict(__file__=str(Path(__file__).resolve()), __name__='current_digital_parent_context')
    exec(compile(text, str(original), 'exec'), scope)
    scope['main']()


if __name__ == '__main__':
    main()
