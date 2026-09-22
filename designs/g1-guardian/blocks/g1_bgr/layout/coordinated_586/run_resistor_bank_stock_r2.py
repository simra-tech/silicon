#!/usr/bin/env python3
"""Frozen r1 stock checker, with explicitly bounded r2 input substitution."""
import hashlib
import json
import os
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    here = Path(__file__).resolve().parent
    root = here.parents[5]
    base = root / 'build/scratch/bgr-resistor-bank-pilot-20260922-r2'
    old = root / 'build/scratch/bgr-resistor-bank-stock-20260922-r1'
    out = root / 'build/scratch/bgr-resistor-bank-stock-20260922-r2'
    assert os.sched_getaffinity(0) == {6} and not out.exists()
    original = here / 'run_resistor_bank_stock.py'
    old_summary = json.loads((old / 'summary.json').read_text())
    assert sha(original) == old_summary['script_sha256']
    audit = json.loads((base / 'landing_revision_audit.json').read_text())
    assert audit['status'] == 'passed scoped M3-only landing reduction'
    assert all(audit[k] for k in ('all_text_exact', 'native_devices_exact',
                                 'tracks_via_centers_cuts_exact', 'all_Via2_Via3_M3_55nm_enclosure'))
    bindings = {p: sha(p) for p in (original, base / 'landing_revision_audit.json',
                                   base / 'manifest.json', old / 'summary.json')}
    replacements = [
        ('bgr-resistor-bank-pilot-20260922-r1', 'bgr-resistor-bank-pilot-20260922-r2'),
        ('bgr-resistor-bank-stock-20260922-r1', 'bgr-resistor-bank-stock-20260922-r2'),
        ('14056b42510b67485bbcfdc8a36cb4803a9e6696e35b868f228fbf1f131601f8',
         '4019838faa0efb2b5038e69f9652c6e52eb60ab070ac964f2d39f72af29e0d17'),
        ('RESISTOR_BANK_STOCK_CONTRACT_20260922.md', 'RESISTOR_BANK_STOCK_R2_CONTRACT_20260922.md')]
    source = original.read_text()
    for before, after in replacements:
        assert source.count(before) == 1
        source = source.replace(before, after)
    scope = {'__file__': str(Path(__file__)), '__name__': 'frozen_r2_stock'}
    exec(compile(source, str(original), 'exec'), scope)
    scope['main']()
    (out / 'derived_runner.py').write_text(source)
    summary = json.loads((out / 'summary.json').read_text())
    summary.update(declared_replacements=replacements, original_runner_sha256=sha(original),
                   derived_runner_sha256=sha(out / 'derived_runner.py'),
                   landing_audit_sha256=bindings[base / 'landing_revision_audit.json'],
                   revision_bindings_unchanged=all(sha(p) == h for p, h in bindings.items()))
    if not summary['revision_bindings_unchanged']:
        summary['status'] = 'failed'
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    raise SystemExit(0 if summary['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
