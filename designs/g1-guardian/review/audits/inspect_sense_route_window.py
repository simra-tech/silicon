#!/usr/bin/env python3
"""Read-only source geometry inventory for the isolated SENSE route remedy."""
import argparse
import hashlib
import json
from pathlib import Path
import pya

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("gds", type=Path)
p.add_argument("--box", default="980,450,1035,612")
a = p.parse_args()
ly = pya.Layout()
ly.read(str(a.gds))
top = ly.cell("g1_chip_top")
box = pya.DBox(*map(float, a.box.split(","))).to_itype(ly.dbu)
result = {"source_sha256": hashlib.sha256(a.gds.read_bytes()).hexdigest(),
          "klayout_version": pya.__version__, "dbu_um": ly.dbu,
          "instances": [{"cell": i.cell.name, "bbox_um": str(i.dbbox())}
                        for i in top.each_inst() if i.bbox().overlaps(box)], "layers": {}}
for layer in (30, 49, 50, 66, 67, 125, 126, 133, 134):
    for dt in ((0, 22) if layer not in (49, 66, 125, 133) else (0,)):
        li = ly.layer(layer, dt)
        region = (pya.Region(top.begin_shapes_rec(li)) & pya.Region(box)).merged()
        local = []
        for shape in top.shapes(li).each_overlapping(box):
            if not shape.is_text():
                local.append(str(shape.polygon.to_dtype(ly.dbu)))
        result["layers"][f"{layer}/{dt}"] = {
            "recursive_polygons_um": [str(q.to_dtype(ly.dbu)) for q in region.each()],
            "top_shapes_um": local}
print(json.dumps(result, indent=2))
