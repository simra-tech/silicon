# SPDX-License-Identifier: Apache-2.0
"""Placement table of an r1_top try on the 1700 um ring, with the S7 C4 origin and the delta (track T8, try e).
  python3 write_placement_e.py <r1_top_assembly.json> <out.csv>
"""
import csv
import json
import sys

asm = json.load(open(sys.argv[1]))
rows = []
for r in asm["placement"]:
    s7 = r.get("s7_c4")
    o = r["origin_um"]
    bb = r["bbox_um"]
    ll = [bb[0], bb[1]]                       # lower-left corner of the outline (S7 gives lower-left corners)
    d = "" if not s7 else "%+.1f, %+.1f" % (ll[0] - s7[0], ll[1] - s7[1])
    rows.append([r["instance"], r["macro"], r["orientation"], o[0], o[1], " ".join(str(v) for v in bb),
                 "" if not s7 else "%s, %s" % (s7[0], s7[1]), d, r["source"], r["source_sha256"]])
dr = asm.get("antenna_decap_row")
if dr:
    rows.append(["u_decap_ant[0:%d]" % (dr["count"] - 1), dr["cell"], "R0 (array %d x 1, pitch %s)" % (dr["count"], dr["pitch_um"]),
                 dr["origin_um"][0], dr["origin_um"][1], " ".join(str(v) for v in dr["bbox_um"]), "", "",
                 "PDK libs.ref/sg13g2_stdcell (PDK commit 84374023), " + dr["cell_source"], "-"])
for tc in asm.get("tie_cells", []):
    rows.append([tc["instance"], tc["cell"], tc["orientation"], tc["origin_um"][0], tc["origin_um"][1],
                 " ".join(str(v) for v in tc["bbox_um"]), "", "",
                 "PDK libs.ref/sg13g2_stdcell (PDK commit 84374023), " + tc["cell_source"], "-"])
with open(sys.argv[2], "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["instance", "macro", "orientation", "origin_x_um", "origin_y_um", "bbox_um", "s7_c4_lower_left_um",
                "delta_vs_s7_um", "source", "source_sha256"])
    w.writerows(rows)
print("rows", len(rows))
