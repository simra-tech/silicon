#!/usr/bin/env python3
"""Write one run.json per case from runs/<tag>/<case>/metrics.json (host python 3.6). Usage: finalize.py <tag>"""
import json, sys, glob, os, hashlib
tag = sys.argv[1]
def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()
HERE = os.path.dirname(os.path.abspath(__file__))
net = sha(os.path.join(HERE, "..", "schematic", "r1_gate.spice"))
cells = sha(os.path.join(HERE, "..", "schematic", "g1_cells_copy.spice"))
Q = {"pkg0": "Delay, edge times, edge overlap with 50 ns dead time, and the fault-path time of the gate path into the PDK pad model (ideal supplies).",
     "pkg1": "Peak and mean IOVDD current and IOVDD/IOVSS bounce with all three gates switching together (package model)."}
for f in sorted(glob.glob(os.path.join(HERE, "runs", tag, "*", "metrics.json"))):
    m = json.load(open(f))
    d = os.path.dirname(f)
    deck = "<G1_RESULTS_ROOT>/r1_gate/%s/%s/deck.cir" % (tag, m["case"])
    rj = {
      "run_id": "%s/%s" % (tag, m["case"]),
      "question": Q["pkg1" if m["pkg"] else "pkg0"] + (" Light-load case: pad cross-conduction." if m["load_F"] == "1p" else ""),
      "command": "G1_CPUSET=119 G1_CPUS=1 G1_RESULTS_ROOT=<G1_RESULTS_ROOT> python3 designs/r1-joint/blocks/r1_gate/sim/run_gate.py --topo %s --corner %s --load %s --pkg %d --cdec %s --seg %g --nodcn %d --tag %s"
                 % (m["topology"], m["corner"], m["load_F"], m["pkg"], m["cdec"], m["seg_us"], m["nodcn"], tag),
      "tools": {"ngspice": "ngspice-46 (container tapeoutbench-eda:latest)", "image_id": "sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2",
                "pdk_commit": "84374023ee8b4b126bebbba67fcbada0a9c0ff0b", "host_python": "3.6"},
      "inputs": {"deck": deck, "waveform": "<G1_RESULTS_ROOT>/r1_gate/%s/%s/wave.dat" % (tag, m["case"]), "log": "<G1_RESULTS_ROOT>/r1_gate/%s/%s/ngspice.log" % (tag, m["case"]),
                 "netlist_sha256": net, "g1_cells_copy_sha256": cells,
                 "pad_model": ("deck-local copy of sg13g2_io.spi without dantenna devices (<G1_RESULTS_ROOT>/r1_gate/sg13g2_io_nodcn.spi, made by sim/make_nodcn.sh)" if m["nodcn"] else "stock PDK sg13g2_io.spi"),
                 "corner": m["corner"], "mos": m["mos_corner"], "temp_C": m["temp_C"], "iovdd_V": m["iovdd_V"], "vdd_V": m["vdd_V"], "load": m["load_F"], "rg_ohm": m["rg_ohm"],
                 "package_model": bool(m["pkg"]), "decap": m["cdec"]},
      "result": m["result"], "wall_s": m["wall_s"], "metrics": "metrics.json (same directory)",
      "disposition": ("kept: label simulated; see README tables" if m["completed"] else "failed run kept in the record: " + json.dumps(m.get("stall", m.get("error_tail"))))}
    json.dump(rj, open(os.path.join(d, "run.json"), "w"), indent=1, sort_keys=True)
    print("wrote", d)
