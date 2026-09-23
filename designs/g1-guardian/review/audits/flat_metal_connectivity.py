#!/usr/bin/env python3
"""Instance-resolved conductor extraction, without local-cell net-ID aliasing."""
import argparse
import json
import os
from pathlib import Path
import pya
from audit_placed_decap_domains import physical, identity
from place_closed_analog import region, sha

LAYERS = (8, 10, 30, 50, 67, 126, 134, 19, 29, 49, 66, 125, 133)


def flat_physical(layout, top):
    flat = pya.Layout(); flat.dbu = layout.dbu
    cell = flat.create_cell('instance_resolved_metal_graph')
    for layer in LAYERS:
        expected = region(layout, top, pya.LayerInfo(layer, 0))
        cell.shapes(flat.layer(layer, 0)).insert(expected)
        assert (region(flat, cell, pya.LayerInfo(layer, 0)) ^ expected).is_empty()
    net, metals = physical(flat, cell)
    # Keep the copied layout alive while callers use its extraction layers.
    return net, metals, flat


def controls(output):
    assert not output.exists() and len(os.sched_getaffinity(0)) == 1
    assert pya.__version__ == '0.30.9'
    ly = pya.Layout(); ly.dbu = .001
    top = ly.create_cell('CONTROL_TOP'); child = ly.create_cell('REUSED_CHILD')
    child.shapes(ly.layer(8, 0)).insert(pya.Box(0, 0, 1000, 1000))
    # Deliberately identical annotations must never create physical joining.
    child.shapes(ly.layer(8, 25)).insert(pya.Text('SAME_LABEL', pya.Trans(500, 500)))
    top.insert(pya.CellInstArray(child.cell_index(), pya.Trans()))
    top.insert(pya.CellInstArray(child.cell_index(), pya.Trans(3000, 0)))
    net, metals = physical(ly, top)
    original = [identity(net, metals[8], p) for p in ([500, 500], [3500, 500])]
    assert None not in original and original[0] == original[1]
    n, m, held = flat_physical(ly, top)
    separate = [identity(n, m[8], p) for p in ([500, 500], [3500, 500])]
    assert None not in separate and separate[0] != separate[1]
    # Same geometry, one explicit conductor bridge: only then must they join.
    top.shapes(ly.layer(8, 0)).insert(pya.Box(500, 400, 3500, 600))
    n, m, held = flat_physical(ly, top)
    joined = [identity(n, m[8], p) for p in ([500, 500], [3500, 500])]
    assert None not in joined and joined[0] == joined[1]
    top.shapes(ly.layer(10, 0)).insert(pya.Box(400, 400, 600, 1600))
    n, m, held = flat_physical(ly, top)
    crossing = [identity(n, m[layer], point) for layer, point in [(8, [500, 500]), (10, [500, 1500])]]
    assert None not in crossing and crossing[0] != crossing[1]
    top.shapes(ly.layer(19, 0)).insert(pya.Box(450, 450, 550, 550))
    n, m, held = flat_physical(ly, top)
    via = [identity(n, m[layer], point) for layer, point in [(8, [500, 500]), (10, [500, 1500])]]
    assert None not in via and via[0] == via[1]
    result = dict(status='passed four flat-geometry connectivity controls',
        script_sha256=sha(Path(__file__)), KLayout=pya.__version__,
        original_hierarchical_identity_control='failed distinguish disconnected repeated cells',
        original_keys=original, disconnected_copies=separate, explicit_bridge=joined,
        crossing_without_via=crossing, crossing_with_via=via,
        not_run=['stock DRC/LVS on synthetic geometry', 'fullchip connectivity'],
        not_applicable=['physical device or current-capacity qualification'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n'); print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control-output', type=Path, required=True)
    controls(parser.parse_args().control_output)
