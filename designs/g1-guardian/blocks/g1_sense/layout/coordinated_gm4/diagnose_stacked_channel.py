#!/usr/bin/env python3
"""Capture exact failed geometry at its first invariant, without changing it."""
import hashlib
import json
from pathlib import Path
import os


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    here = Path(__file__).resolve().parent
    root = here.parents[5]
    original = here / 'build_stacked_pair.py'
    failed = here / 'stacked-pair-20260922-r1'
    output = here / 'stacked-pair-channel-diagnostic-20260922-r1'
    assert not output.exists() and os.sched_getaffinity(0) == {7}
    failure = json.loads((failed / 'failure.json').read_text())
    assert sha(original) == failure['script_sha256'] == sha(failed / 'builder_snapshot.py')
    source = original.read_text()
    anchor = "assert ((before[1]&before[5])^(after[1]&after[5])).is_empty() and (before[1]-after[1]).is_empty()"
    assert source.count(anchor) == 1
    derived = source.replace(anchor, 'capture_failure(cell, before, after); raise StopAfterCapture()')
    output.mkdir()
    (output / 'derived_builder.py').write_text(derived)

    class StopAfterCapture(Exception):
        pass

    def capture(cell, before, after):
        original_channels = before[1] & before[5]
        channels = after[1] & after[5]
        groups = {'added_channels': channels - original_channels,
                  'removed_channels': original_channels - channels,
                  'removed_native_Activ': before[1] - after[1]}
        rows = {}
        for name, region in groups.items():
            rows[name] = dict(area_um2=region.area() * 1e-6, polygons=[
                dict(bbox_um=[v * .001 for v in (p.bbox().left, p.bbox().bottom, p.bbox().right, p.bbox().top)],
                     area_um2=p.area() * 1e-6, polygon_dbu=p.to_s()) for p in region.each()])
        gds = output / 'failed_geometry.gds'
        cell.layout().write(str(gds))
        report = dict(status='passed diagnostic capture; original geometry gate remains failed',
                      original_builder_sha256=sha(original), derived_builder_sha256=sha(output / 'derived_builder.py'),
                      failure_sha256=sha(failed / 'failure.json'), GDS_sha256=sha(gds),
                      only_change='Output capture replaces first failed assertion; all preceding geometry generation is identical',
                      differences=rows, stock_LVS_DRC='not run', adoption='not run')
        (output / 'diagnostic.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))

    scope = {'__file__': str(original), '__name__': 'diagnostic_only',
             'capture_failure': capture, 'StopAfterCapture': StopAfterCapture}
    exec(compile(derived, str(original), 'exec'), scope)
    pack = root / 'designs/g1-guardian/review/audits/coordinated-bbox-pack-20260922-r4.json'
    assert sha(pack) == failure['pack_sha256']
    schematic = here.parents[1] / 'reports/resume-server-20260922/gm4comp3-qualified-source.spice'
    assert sha(schematic) == failure['source_sha256']
    layout = scope['pya'].Layout()
    layout.dbu = .001
    try:
        scope['build'](layout, schematic, json.loads(pack.read_text()))
    except StopAfterCapture:
        assert (output / 'diagnostic.json').exists()
        return
    raise AssertionError('Expected original first invariant was not reached')


if __name__ == '__main__':
    main()
