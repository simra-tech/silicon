#!/usr/bin/env python3
"""Collect the revision-4 R2-4 option results (post_ref4.py outputs) into sim/results/r4/ref4_options.json."""
import json
import os
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "..", "results", "r4")
OPT = [  # file, label, gmin, area note
    ("ref4_tt_n0_buf32.json", "buf32, revision-3 error amplifier (tail 10 uA), stagger 0", "1e-10"),
    ("ref4_tt_n0_buf64.json", "buf64 (msf 64, mib 320), revision-3 error amplifier, stagger 0", "1e-10"),
    ("ref4_tt_n0_buf32cg4.json", "buf32, gate capacitor ncg 4, stagger 0", "1e-10"),
    ("ref4_tt_n2_buf32.json", "buf32, stagger N = 2 ticks (option 1)", "1e-10"),
    ("ref4_tt_n0_buf32_ea8.json", "buf32, error-amplifier tail mt 1 / lt 8 um (~0.6 uA)", "1e-10"),
    ("ref4_tt_n0_buf32_ea8cg2.json", "buf32, tail mt 1 / lt 8 um, ncg 2", "1e-10"),
    ("ref4_tt_n0_buf64_ea8.json", "buf64, tail mt 1 / lt 8 um", "1e-10"),
    ("ref4_tt_n0_bufsel.json", "CHOSEN (r1_refbuf4 defaults): buf32, tail mt 1 / lt 8 um, ncg 1; ideal run at the buffer level", "1e-9"),
    ("ref4_tt_n0_bufh.json", "r1_refbuf4h (no input divider), bandgap model 190 kohm + 10 pF input filter; ideal run at the buffer level", "1e-9"),
    ("ref4_ss125_n0_bufsel.json", "CHOSEN at ss / 125 C / 1.08 V", "1e-9"),
    ("ref4_ffm40_n0_bufsel.json", "CHOSEN at ff / -40 C / 1.32 V", "1e-9"),
    ("ref4_tt_n0_buf32_ea32cg2.json", "buf32, tail mt 1 / lt 32 um, ncg 2; ideal run at the chosen buffer level", "1e-9"),
]
out = {"label": "simulated, tt unless stated, 10 frames (sim/r4/points/ref10.json, +-0.88 V both slices), post_ref4.py",
       "metrics": {"test_input_error_lsb": "residue-resolved conversion error of the 10 test inputs vs the ideal-VREF run",
                   "max_code_diff_lsb": "12-bit code difference with design weights (includes the static VREF gain)",
                   "worst_case_input_error_lsb": "comparator input error 25 ns into the tick, decisions 5..13, along the common decision path: bound on the conversion error over all inputs (decisions 5..13 have about 0.31 LSB redundancy)"},
       "options": []}
for f, lab, g in OPT:
    p = os.path.join(R, f)
    if not os.path.exists(p):
        continue
    d = json.load(open(p))
    out["options"].append({"file": "sim/results/r4/" + f, "option": lab, "gmin": g, "runs": [d["run_buffer"], d["run_ideal"]],
                           "n_stag": d["n_stag"], "idda_mA": round(d.get("idda_mA", 0), 3),
                           "test_input_error_lsb": round(d["max_abs_error_lsb"], 3), "max_code_diff_lsb": d["max_abs_code_diff_lsb"],
                           "worst_case_input_error_lsb": round(d["max_abs_input_error_mid_eval_lsb"], 3)})
json.dump(out, open(os.path.join(R, "ref4_options.json"), "w"), indent=1)
for o in out["options"]:
    print("%-95s gmin %s IDDA %.3f test %.3f code %d worst %.3f" % (o["option"][:95], o["gmin"], o["idda_mA"], o["test_input_error_lsb"], o["max_code_diff_lsb"], o["worst_case_input_error_lsb"]))
