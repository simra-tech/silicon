#!/usr/bin/env python3
"""Current saved controls rebound to RZ keepout, including successor metadata."""
import hashlib
from pathlib import Path

base=Path(__file__).resolve().parent.parent/'prepare_current_diagnostics.py'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='43a15aa05133d6bf2edb3abae318a7adff050f778c04698354e07bcdde98068a'
code=base.read_text()
edits=[
 ('4cffddc5ae8369c9fd5c574cb9571b4641cdee26876370c93bfbe042c4049df2','5d121548bb9406f8229fdca7e7e26c1c3e6581ad1b0745f8a2cfce4615af8684'),
 ('1b2156355d671e31970482eb3ec8f47b5e4b7bb25d7b111155bfb0ea7306460f','8b32688b34d4461d0534531889ca222f0eac482f65195e04ea421a3a13bcf804'),
 ('gshared-fill-20260923-r4','current-purefill-rz-keepout-20260923-r2'),
 ('io-physical-ap-native-lvs-20260923-r1/reports/route_fill_pruned.lvsdb','current-purefill-rz-keepout-stock-lvs-20260923-r1/rz_fill_keepout.lvsdb'),
 ('route_fill_pruned.gds','rz_fill_keepout.gds'),
 ('io-physical-ap-source-20260923-r2','trip-hard-full-reference-20260923-r1'),
 ('d39ce8512f167545ab2818582bd1e51e88f6402ff810dcf3368cd7d277ddb4d4','94e50a2a7f0646282f4499831bcfe03a2cf8871fbc33a7549b6e8f94fded207b')]
for old,new in edits:
    assert code.count(old)>0,(old,code.count(old));code=code.replace(old,new)
needle='        ("assert material[\'native_filler_polygons\'] == 7058","assert material[\'native_filler_polygons\'] > 0 # Exact current material proof, not old-parent count.")])'
replacement='''        ("assert material['native_filler_polygons'] == 7058","assert material['native_filler_polygons'] > 0 # Exact current material proof, not old-parent count."),
        ("meta = json.loads((a.candidate / 'analysis.json').read_text())","meta = json.loads((a.candidate / 'summary.json').read_text())"),
        ("meta['GDS_sha256']","meta['output_gds_sha256']"),
        ("a.candidate / 'analysis.json')","a.candidate / 'summary.json')")])'''
assert code.count(needle)==1
code=code.replace(needle,replacement)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
