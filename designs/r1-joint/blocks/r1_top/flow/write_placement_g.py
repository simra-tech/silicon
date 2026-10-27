# SPDX-License-Identifier: Apache-2.0
"""Placement table of r1_top try g with the try-f origin and the delta (track T8e).
  python3 write_placement_g.py <r1_top_assembly.json> <out.csv>
"""
import csv
import json
import sys

asm = json.load(open(sys.argv[1]))
rows = []
for r in asm["placement"]:
    f = r.get("try_f_origin_um")
    o = r["origin_um"]
    bb = r["bbox_um"]
    d = "" if not f else "%+.2f, %+.2f" % (o[0] - f[0], o[1] - f[1])
    fs = r.get("try_f_size_um")
    sz = "%.2f x %.2f" % (bb[2] - bb[0], bb[3] - bb[1])
    rows.append([r["instance"], r["macro"], r["orientation"], o[0], o[1], " ".join(str(v) for v in bb), sz,
                 "" if not f else "%s, %s" % (f[0], f[1]), d,
                 "" if not fs else "%.2f x %.2f" % tuple(fs), r["source"], r["source_sha256"]])
dr = asm.get("antenna_decap_row")
if dr:
    rows.append(["u_decap_ant[0:%d]" % (dr["count"] - 1), dr["cell"], "R0 (array %d x 1, pitch %s)" % (dr["count"], dr["pitch_um"]),
                 dr["origin_um"][0], dr["origin_um"][1], " ".join(str(v) for v in dr["bbox_um"]), "", "as try f",
                 "+0.00, +0.00", "", "PDK libs.ref/sg13g2_stdcell (PDK commit 84374023), " + dr["cell_source"], "-"])
for tc in asm.get("tie_cells", []):
    rows.append([tc["instance"], tc["cell"], tc["orientation"], tc["origin_um"][0], tc["origin_um"][1],
                 " ".join(str(v) for v in tc["bbox_um"]), "", "as try f", "+0.00, +0.00", "",
                 "PDK libs.ref/sg13g2_stdcell (PDK commit 84374023), " + tc["cell_source"], "-"])
rows.append(["u_adiode_* (30)", "sg13g2_antennanp", "-", "", "", "", "", "y 661.0 (try f)", "removed", "", "-", "-"])
with open(sys.argv[2], "w", newline="") as fo:
    w = csv.writer(fo)
    w.writerow(["instance", "macro", "orientation", "origin_x_um", "origin_y_um", "bbox_um", "size_um",
                "try_f_origin_um", "delta_vs_try_f_um", "try_f_size_um", "source", "source_sha256"])
    w.writerows(rows)
print("rows", len(rows))
