#!/usr/bin/env python3
"""Synthetic two-gate timing control; no production geometry or deck changes."""
import argparse
import hashlib
import json
from pathlib import Path
import pya

p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
a = p.parse_args(); assert not a.output.exists(); a.output.mkdir(parents=True)
ly = pya.Layout(); ly.dbu = .001; top = ly.create_cell('CONTROL')
for n, boxes in {1:[(0,0,1000,1000),(10000,0,13000,1000)],
                 8:[(0,0,2000,2000),(10000,0,14000,2000)],
                 10:[(1000,500,11000,1500)]}.items():
    for box in boxes: top.shapes(ly.layer(n,0)).insert(pya.Box(*box))
ly.write(str(a.output/'control.gds'))
(a.output/'source.py').write_bytes(Path(__file__).read_bytes())
deck = Path(__file__).with_name('net_evaluation_control.drc')
(a.output/'control.drc').write_bytes(deck.read_bytes())
(a.output/'contract.json').write_text(json.dumps(dict(gate_areas_um2=[1,3], metal1_areas_um2=[4,8],
    expected_immediate_before_ratios=[4,8/3], expected_after_ratio=3,
    deferred_before_alternative=3, stock_PDK_changed=False,
    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    deck_sha256=hashlib.sha256(deck.read_bytes()).hexdigest()),indent=2)+'\n')
