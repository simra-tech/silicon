#!/usr/bin/env python3
"""Prepare source-derived CDL tap syntax normalization, preserving circuit intent."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[4]
DEFAULT = ROOT / 'build/scratch/p01-full-io-normalized-20260921/g1_chip_top_reference.cdl'
EXPECTED = 'e6cb15318a93055bf76912ff3daf38c23e23d62d0e50df45375bb260d3371c3e'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--source', type=Path, default=DEFAULT)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
if a.source == DEFAULT:
    assert sha(a.source) == EXPECTED
a.output.mkdir(parents=True, exist_ok=False)
shutil.copyfile(__file__, a.output / 'generator.py')
source = a.source.read_text()
pattern = re.compile(r'^(\s*)(X\S+)(\s+\S+\s+\S+\s+)([pn]tap1)(\s+.*)$', re.I)
current = None
edits = []
result = []
seen = {}
for line in source.splitlines(keepends=True):
    subckt = re.match(r'^\s*\.subckt\s+(\S+)', line, re.I)
    if subckt:
        current = subckt[1]
        seen[current] = set()
    match = pattern.match(line.rstrip('\n'))
    if match:
        # Keep original unique identity under an explicit resistor prefix.
        # Nodes, model and every parameter token are preserved byte-for-byte.
        new_name = 'R_G1_BIND_' + match[2]
        edited = match[1] + new_name + match[3] + match[4] + match[5]
        edited += '\n' if line.endswith('\n') else ''
        assert edited[len(match[1]) + len(new_name):] == line[len(match[1]) + len(match[2]):]
        edits.append({'cell': current, 'original': line.rstrip('\n'),
                      'normalized': edited.rstrip('\n'), 'model': match[4]})
        line = edited
    token = line.strip().split()
    if current and token and token[0][0].upper() in 'RMCQDXL' and '=' not in token[0]:
        assert token[0].upper() not in seen[current], (current, token[0])
        seen[current].add(token[0].upper())
    result.append(line)
assert edits
normalized = ''.join(result)
target = a.output / 'g1_chip_top_tap_syntax.cdl'
target.write_text(normalized)
cells = ['sg13g2_Filler400', 'sg13g2_LevelUpInv', 'sg13g2_RCClampInverter']
for cell in cells:
    for label, text in [('original', source), ('normalized', normalized)]:
        sub = re.search(r'^\.SUBCKT\s+' + re.escape(cell) + r'\b.*?^\.ENDS[^\n]*', text, re.I | re.M | re.S)
        assert sub
        (a.output / (cell + '_' + label + '.cdl')).write_text(sub[0] + '\n')
manifest = {'scope': 'Reference syntax hypothesis only, no geometry/model/deck edits and no extraction-derived reference',
            'source_sha256': sha(a.source), 'normalized_sha256': sha(target),
            'generator_sha256': sha(Path(__file__)), 'edits': edits,
            'preservation': 'Only instance identifier/prefix changed; full node/model/parameter suffix identical per line.',
            'reader_probe': 'not run', 'stock_LVS': 'not run',
            'remaining_failures': ['Tap geometry versus original A/P parameter mismatch remains visible.',
                                   'PolyRes recognition and physically split same-name rails remain separate.']}
(a.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'normalized_sha256': manifest['normalized_sha256'], 'tap_lines_rebound': len(edits),
                  'cells': len({row['cell'] for row in edits})}, indent=2))
