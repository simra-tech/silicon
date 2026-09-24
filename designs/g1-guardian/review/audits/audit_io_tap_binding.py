#!/usr/bin/env python3
"""Audit preserved source and textual LVSDB; this does not rerun extraction."""
import argparse
import hashlib
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parents[4]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists()
source = root / 'build/scratch/p01-full-io-normalized-20260921/g1_chip_top_reference.cdl'
database = root / 'build/scratch/p01-full-io-normalized-20260921/g1_chip_top_normalized.lvsdb'
cdl = source.read_text()
db = database.read_text()
assert '\nH(\n' in db and '\nZ(\n' in db
reference = db.split('\nH(\n', 1)[1].split('\nZ(\n', 1)[0]
circuits = dict(re.findall(r'^ X\((\S+)(.*?)(?=^ X\(|\Z)', reference, re.M | re.S))
classes = re.findall(r'^ K\((\S+)', reference, re.M)
cells = ['sg13g2_Corner', 'sg13g2_Filler2000', 'sg13g2_Filler400', 'sg13g2_Filler4000',
         'sg13g2_LevelUpInv', 'sg13g2_RCClampInverter', 'sg13g2_SecondaryProtection']
rows = []
for cell in cells:
    sub = re.search(r'^\.SUBCKT\s+' + re.escape(cell) + r'\b.*?^\.ENDS[^\n]*', cdl, re.I | re.M | re.S)
    assert sub, cell
    lines = [line for line in sub[0].splitlines() if re.search(r'^X\S+\s+\S+\s+\S+\s+[pn]tap1\b', line, re.I)]
    rows.append({'cell': cell, 'source_definition_present': True, 'source_tap_lines': lines,
                 'source_instantiation_count': len(re.findall(r'^X[^\n]*/\s*' + re.escape(cell) + r'\s*$', cdl, re.M | re.I)),
                 'compared_reference_circuit_present': cell.upper() in circuits,
                 'compared_reference_device_count': len(re.findall(r'^  D\(', circuits.get(cell.upper(), ''), re.M))})
result = {'scope': 'Read-only audit of exact saved source and final reference netlist within existing LVSDB; no new LVS run.',
          'inputs': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (source, database)},
          'reference_device_classes': classes,
          'reference_tap_device_class_present': any(name.lower() in ('ptap1', 'ntap1') for name in classes),
          'source_ptap1_subcircuit_definition_present': bool(re.search(r'^\.SUBCKT\s+ptap1\b', cdl, re.M | re.I)),
          'cells': rows, 'stock_reader_probe': 'not run', 'normalized_reference_LVS': 'not run'}
a.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
