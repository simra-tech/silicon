#!/usr/bin/env python3
"""Current source-faithful saved-graph comparison on exact RZ keepout DB."""
from pathlib import Path

base=Path(__file__).with_name('compare_current_saved.py')
code=base.read_text()
edits=[
 ('current-purefill-dummy-proof-20260923-r1','current-purefill-rz-keepout-dummy-proof-20260923-r2'),
 ('current-purefill-dummy-projection-20260923-r1','current-purefill-rz-keepout-dummy-projection-20260923-r1'),
 ('6b9c5878a81a0ac4d3f68d3d8dbb5fa1927442675606aa6bd46a14d6552def51','5d121548bb9406f8229fdca7e7e26c1c3e6581ad1b0745f8a2cfce4615af8684'),
 ('current-purefill-native-lvs-20260923-r1/reports/pure_fill_flattened.lvsdb','current-purefill-rz-keepout-stock-lvs-20260923-r1/rz_fill_keepout.lvsdb'),
 ('7efa28056f533df4fec8b585654e5445e8d932d4a775747ee5813ae65660cf85','8b32688b34d4461d0534531889ca222f0eac482f65195e04ea421a3a13bcf804'),
 ('current-purefill-saved-diagnostics-20260923-r1','current-purefill-rz-keepout-saved-diagnostics-20260923-r2')]
for old,new in edits:
    assert code.count(old)>0,(old,code.count(old));code=code.replace(old,new)
exec(compile(code,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
