#!/usr/bin/env python3
"""Write a copy of a GDS with the PDK fill datatype (22, '<layer>.filler' in
sg13g2.lyp) removed from every cell; report what was removed and flat shape
counts before/after. Datatype 23 ('nofill') markers and all other shapes are
kept. The input file is not modified."""
import argparse, hashlib, json, collections, time
from pathlib import Path
import klayout.db as kdb
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--input', required=True, type=Path); ap.add_argument('--output', required=True, type=Path)
ap.add_argument('--report', required=True, type=Path); ap.add_argument('--fill-datatype', type=int, default=22)
a = ap.parse_args()
if a.output.exists() or a.report.exists(): ap.error('refusing to overwrite')
t0 = time.time()
ly = kdb.Layout(); ly.read(str(a.input)); top = ly.top_cell()
def flat_counts():
    d = {}
    for li in ly.layer_indices():
        n = 0; it = top.begin_shapes_rec(li)
        while not it.at_end(): n += 1; it.next()
        if n: d[ly.get_info(li).to_s()] = n
    return d
before = flat_counts()
removed_cells = collections.defaultdict(dict)
for li in ly.layer_indices():
    info = ly.get_info(li)
    if info.datatype != a.fill_datatype: continue
    for c in ly.each_cell():
        n = c.shapes(li).size()
        if n: removed_cells[c.name][info.to_s()] = n; c.shapes(li).clear()
after = flat_counts()
opts = kdb.SaveLayoutOptions(); opts.write_context_info = False
ly.write(str(a.output), opts)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rep = dict(input=str(a.input), input_sha256=sha(a.input), output=str(a.output), output_sha256=sha(a.output),
    script_sha256=sha(Path(__file__)), klayout=kdb.__version__, top=top.name, fill_datatype=a.fill_datatype,
    removed_by_cell=removed_cells,
    flat_shapes_before=before, flat_shapes_after=after,
    flat_total_before=sum(before.values()), flat_total_after=sum(after.values()),
    flat_fill_removed={k: before[k]-after.get(k, 0) for k in before if before[k] != after.get(k, 0)},
    wall_s=round(time.time()-t0, 1))
a.report.write_text(json.dumps(rep, indent=1)+'\n')
print(json.dumps({k: v for k, v in rep.items() if k not in ('flat_shapes_before', 'flat_shapes_after')}, indent=1))
