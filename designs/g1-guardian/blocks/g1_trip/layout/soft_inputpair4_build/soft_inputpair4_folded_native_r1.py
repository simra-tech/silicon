"""Unintegrated soft comparator folding proposal; no production or PDK writes.

The generated cell is intentionally standalone. Its internal cell pins move;
full-parent integration must reroute them without changing any macro pin.
DRC/LVS/field/loading qualification is NOT RUN by this preparer.
"""
import ast
import hashlib
import inspect
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
GENERATOR = ROOT / 'designs/g1-guardian/blocks/g1_trip/layout/gen_trip_layout.py'


def plan():
    old_width = .68 + 2 * .34 + .38
    new_width = .68 + 4 * .68 + 3 * .38
    shift = round(new_width - old_width, 3)
    return dict(status='prepared isolated folding; physical qualification not run',
                total_width_um=24., length_um=.68, fingers=4,
                finger_width_um=6., active_width_um=round(new_width, 3),
                old_active_width_um=round(old_width, 3), outer_shift_um=shift,
                drains=[0, 2, 4], sources=[1, 3],
                drain_net_by_side={'right': 'xq', 'left': 'xp'}, source_net='tail',
                input_area_ratio=4.,
                interface='Standalone internal comparator pins may move; no full-parent insertion or macro pin change authorized by this file.',
                unqualified=['DRC', 'LVS', 'actual-parent fit', 'macro feed rerouting',
                             'native extracted effective W/L', 'mismatch representation',
                             'neutralization/loading', 'timing/power', 'full population'])


def transform_class(source):
    """Exact-source transform, with explicit all-finger drain/source contacts."""
    changes = [
        ("class CmpBuilder:", "class SoftInputpair4FoldedBuilder:"),
        ("name='g1_cmp'", "name='g1_cmp_soft_inputpair4_folded_r1'"),
        ("OXN = {'in': 2.07, 'dum': 4.5, 'cc': 6.0, 'inv': 7.5, 'l1': 9.5, 'l2': 11.0}",
         "OXN = {'in': 2.07, 'dum': 7.3, 'cc': 8.8, 'inv': 10.3, 'l1': 12.3, 'l2': 13.8}"),
        ("m, gc = self.nmos(side, X(OXN['in'], 1.74, side), 12.0, 0.34, 2)\n            for i in (0, 2):",
         "m, gc = self.nmos(side, X(OXN['in'], 4.54, side), 24.0, 0.68, 4)\n            for i in (0, 2, 4):"),
        ("D.vpad('Via1', m.strip_x(1), 4.4, hi='h')\n            gin = gc",
         "for source_strip in (1, 3):\n                D.vpad('Via1', m.strip_x(source_strip), 4.4, hi='h')\n            gin = gc"),
        ("D.hwire('M2', -2.94, 2.94, 4.4, ext=False)",
         "D.hwire('M2', -5.40, 5.40, 4.4, ext=False)"),
    ]
    result = source
    for before, after in changes:
        assert result.count(before) == 1, ('source anchor changed', before)
        result = result.replace(before, after)
    ast.parse(result)
    return result


def build_standalone(output):
    """Requires an explicit engine-slot lease outside this function."""
    import sys
    sys.path.insert(0, str(GENERATOR.parent))
    import gen_trip_layout as g
    target = Path(output)
    assert not target.exists()
    text = transform_class(inspect.getsource(g.CmpBuilder))
    scope = dict(vars(g))
    exec(compile(text, str(Path(__file__)), 'exec'), scope)
    ly = g.pya.Layout(); ly.dbu = .001
    builder = scope['SoftInputpair4FoldedBuilder'](ly)
    builder.build()
    target.mkdir()
    ly.write(str(target / 'standalone.gds'))
    record = plan()
    record.update(generator_sha256=hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  gds_sha256=hashlib.sha256((target/'standalone.gds').read_bytes()).hexdigest(),
                  internal_pins=builder.pins, halfwidth_um=builder.xw,
                  scope='Standalone geometry only. Production hard/soft cells and full-parent GDS untouched.')
    (target/'preparation.json').write_text(json.dumps(record, indent=2)+'\n')
    return record
