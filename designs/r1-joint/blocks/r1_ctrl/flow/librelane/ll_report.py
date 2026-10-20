#!/usr/bin/env python3
"""Small markdown extract of a finished LibreLane run of r1_ctrl (revision 0.3).
Usage: python3 ll_report.py <bulk run dir> <run id> <out.md>
Reads the last state_out.json metrics, run.json and the slow-corner violator list; no machine paths are written.
SPDX-License-Identifier: Apache-2.0"""
import glob
import json
import os
import re
import sys

bdir, rid, out = sys.argv[1:4]
rj = json.load(open(os.path.join(bdir, "run.json")))
runs = glob.glob(os.path.join(bdir, "flow", "runs", "*"))
st = sorted(glob.glob(os.path.join(runs[0], "*", "state_out.json")))
m = json.load(open(st[-1]))["metrics"]
steps = sorted(os.path.basename(os.path.dirname(p)) for p in st)
cfg = open(os.path.join(bdir, "flow", "config.yaml")).read()
deflt = ("flip-flops (`R1_CFG_FLOPS` in config.yaml)" if "R1_CFG_FLOPS" in cfg else "latch words (no `R1_CFG_FLOPS`)")
var = open(os.path.join(bdir, "variant.txt")).read().strip() if os.path.exists(os.path.join(bdir, "variant.txt")) else deflt
var = re.sub(r"/\S*/", "<G1_RESULTS_ROOT>/r1_ctrl/.../", var)
g = lambda k, f="{}": (f.format(m[k]) if k in m and m[k] is not None else "not reported")
L = [f"# LibreLane run `{rid}` (r1_ctrl)", "",
     "Command (repository root, `designs/r1-joint/blocks/r1_ctrl` as `G1_WORKDIR`, CPU set 112-115):", "",
     "```", rj["command"], "```", "",
     f"- LibreLane {rj['tools']['librelane']}, Classic flow, PDK commit `{rj['pdk_commit']}`, container {rj['tools']['container']}",
     f"- Start {rj['start_utc']}, end {rj['end_utc']}, exit code {rj['exit_code']} (timeout {rj['timeout_s']} s)",
     f"- RTL: sha256 of the concatenated `rtl/*.v` copy in the run: `{rj['rtl_concat_sha256']}`; register-file variant: {var}",
     f"- Bulk run: `<G1_RESULTS_ROOT>/r1_ctrl/{rid}/` (inputs in `inputs.sha256`); last step `{steps[-1]}`", "",
     "| Metric | Value |", "| --- | --- |",
     f"| Die / core area (µm²) | {g('design__die__area', '{:.0f}')} / {g('design__core__area', '{:.0f}')} |",
     f"| Standard-cell area (µm²), utilisation | {g('design__instance__area__stdcell', '{:.0f}')}, {g('design__instance__utilization', '{:.3f}')} |",
     f"| Sequential / clock buffers / timing-repair buffers (µm²) | {g('design__instance__area__class:sequential_cell', '{:.0f}')} / {g('design__instance__area__class:clock_buffer', '{:.0f}')} / {g('design__instance__area__class:timing_repair_buffer', '{:.0f}')} |"]
for c in ("nom_typ_1p20V_25C", "nom_fast_1p32V_m40C", "nom_slow_1p08V_125C"):
    L.append(f"| Sign-off STA {c} at 42 MHz: setup WS / TNS (ns), violators; hold WS (ns); max-slew violations | "
             f"{g('timing__setup__ws__corner:' + c, '{:.3f}')} / {g('timing__setup__tns__corner:' + c, '{:.2f}')}, "
             f"{g('timing__setup_vio__count__corner:' + c)}; {g('timing__hold__ws__corner:' + c, '{:.3f}')}; "
             f"{g('design__max_slew_violation__count__corner:' + c)} |")
L += [f"| Detailed routing DRC errors (final) | {g('route__drc_errors')} |",
      f"| Magic DRC / KLayout DRC errors | {g('magic__drc_error__count')} / {g('klayout__drc_error__count')} |",
      f"| LVS errors (netgen) | {g('design__lvs_error__count')} |",
      f"| Antenna violating nets | {g('antenna__violating__nets')} |"]
vl = glob.glob(os.path.join(runs[0], "*stapostpnr*", "nom_slow_1p08V_125C", "max.rpt"))
if vl:
    starts = {}
    for blk in open(vl[0]).read().split("Startpoint: ")[1:]:
        if "VIOLATED" in blk:
            t = re.match(r"\S+ \((.*?)\)", blk).group(1)
            starts[t] = starts.get(t, 0) + 1
    L += ["", "Slow-corner setup violators in the sign-off report, by start-point type: " +
          (", ".join(f"{v} × {k}" for k, v in starts.items()) if starts else "none")]
open(out, "w").write("\n".join(L) + "\n")
print("\n".join(L))
