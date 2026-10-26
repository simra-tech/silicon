# SPDX-License-Identifier: Apache-2.0
"""List density-deck markers of a filled r1_top run and relate each to the ADC placeholder box.

  python3 fill_density_markers.py <fill_exclusions.json> <out.json> <density.lyrdb>

A density marker is a window polygon (800 x 800 um for the window rules) or the chip outline (global rules).
"overlaps_adc": the marker polygon overlaps the placeholder box; "centre_in_adc": the marker centre lies inside it;
"window_contains_adc": the marker polygon contains the whole placeholder box.
"""
import json
import sys
import klayout.db  # noqa: F401  (binds DPolygon for klayout.rdb)
import klayout.rdb as rdb

ex = json.load(open(sys.argv[1]))
adc = [i["bbox_um"] for i in ex["instances"] if i["cell"] == "r1_adc_ph"][0]
db = rdb.ReportDatabase("")
db.load(sys.argv[3])
rows = []
for item in db.each_item():
    cat = db.category_by_id(item.category_id()).name()
    bb = None
    for v in item.each_value():
        if v.is_polygon():
            bb = v.polygon().bbox()
        elif v.is_box():
            bb = v.box()
        if bb is not None:
            break
    if bb is None:
        rows.append({"rule": cat, "bbox_um": None})
        continue
    b = [bb.left, bb.bottom, bb.right, bb.top]
    ov = not (b[2] <= adc[0] or b[0] >= adc[2] or b[3] <= adc[1] or b[1] >= adc[3])
    rows.append({"rule": cat, "bbox_um": [round(x, 3) for x in b],
                 "overlaps_adc": ov,
                 "centre_in_adc": adc[0] <= (b[0] + b[2]) / 2 <= adc[2] and adc[1] <= (b[1] + b[3]) / 2 <= adc[3],
                 "window_contains_adc": b[0] <= adc[0] and b[1] <= adc[1] and b[2] >= adc[2] and b[3] >= adc[3]})
res = {"adc_box_um": adc, "total": len(rows), "overlap_adc": sum(1 for r in rows if r.get("overlaps_adc")),
       "centre_in_adc": sum(1 for r in rows if r.get("centre_in_adc")),
       "not_overlapping_adc": sum(1 for r in rows if not r.get("overlaps_adc")), "markers": rows}
json.dump(res, open(sys.argv[2], "w"), indent=1)
print("markers", res["total"], "overlap ADC box", res["overlap_adc"], "centre in ADC box", res["centre_in_adc"],
      "not overlapping", res["not_overlapping_adc"])
for r in rows:
    print(r["rule"], r["bbox_um"], r.get("overlaps_adc"))
