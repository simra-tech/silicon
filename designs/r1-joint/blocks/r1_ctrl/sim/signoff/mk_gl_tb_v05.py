#!/usr/bin/env python3
"""Second stage of the gate-level testbench for RTL 0.5 (run after mk_gl_tb.sh): replaces the probes of the 0.5 tests that
do not exist in the flattened netlist. usage: mk_gl_tb_v05.py <tb_gl.v in> <tb_gl.v out> [netlist.v]
Probes that survive as escaped nets (sin_code, cos_code, i_a, i_b, u_biss.ma_rst_n) are mapped to them.
Probes that do not survive are replaced by constants and the checks that depend on them are labelled GLSKIP in the log:
 - thr_* / cal_* / ana_ctrl (folded into the tap logic): the cal test and two single checks cannot run
 - adc_arm, u_gate.nra / nrb (disc monitors), force of frame_pos (cdc D): disc and cdc cannot run at gate level
Revision 0.6 also delays the ADC inputs by the SDC minimum input delay (0.5 ns), see the end of the script.
SPDX-License-Identifier: Apache-2.0"""
import re, sys
t = open(sys.argv[1]).read()
NL = open(sys.argv[3]).read() if len(sys.argv) > 3 else ""   # netlist: a bit that is not a net (constant-folded) reads as 0
def bus(name, w): return "{" + ", ".join(("dut.\\%s[%d] " % (name, i)) if (not NL or ("\\%s[%d] " % (name, i)) in NL) else "1'b0" for i in range(w - 1, -1, -1)) + "}"
inj = ("    // GL (0.5): probes mapped to surviving nets, others to constants\n"
       "    wire [11:0] gl_sin_code = %s, gl_cos_code = %s, gl_i_a = %s, gl_i_b = %s;\n"
       "    wire gl_ma_rst_n = dut.\\u_biss.ma_rst_n ;\n"
       "    reg gl_arm = 1'b0, gl_nra = 1'b0, gl_nrb = 1'b0;   // GLSKIP: adc_arm, u_gate.nra / nrb are not nets of the netlist\n"
       % (bus("sin_code", 12), bus("cos_code", 12), bus("i_a", 12), bus("i_b", 12)))
t = t.replace("    wire [15:0] ana_ctrl = dut.ana_ctrl;\n", inj + "    wire [15:0] ana_ctrl = 16'hxxxx;   // GLSKIP\n")
t = t.replace("dut.thr_oc_a, thr_neg_a = dut.thr_neg_a, thr_oc_b = dut.thr_oc_b, thr_neg_b = dut.thr_neg_b", "6'bxxxxxx, thr_neg_a = 6'bxxxxxx, thr_oc_b = 6'bxxxxxx, thr_neg_b = 6'bxxxxxx")
t = t.replace("dut.cal_oc_a, cal_neg_a = dut.cal_neg_a, cal_oc_b = dut.cal_oc_b, cal_neg_b = dut.cal_neg_b", "6'bxxxxxx, cal_neg_a = 6'bxxxxxx, cal_oc_b = 6'bxxxxxx, cal_neg_b = 6'bxxxxxx")
t = t.replace("ana_ctrl == 16'hA5C3", "1'b1 /* GLSKIP ana_ctrl */").replace("ana_ctrl == 16'h0028", "1'b1 /* GLSKIP ana_ctrl */")
t = t.replace("dut.adc_arm", "gl_arm").replace("dut.u_gate.nra", "gl_nra").replace("dut.u_gate.nrb", "gl_nrb")
for n in ["sin_code", "cos_code", "i_a", "i_b"]: t = re.sub(r"dut\.%s\b" % n, "gl_" + n, t)
t = t.replace("dut.u_biss.ma_rst_n", "gl_ma_rst_n")
t = t.replace("dut.u_gate.conv", "dut.\\u_gate.conv ")
t = t.replace("force dut.frame_pos = alt_pos;", "; // GLSKIP force frame_pos").replace("release dut.frame_pos;", "; // GLSKIP release frame_pos")
# Revision 0.6: honour the SDC minimum input delay of the ADC inputs (set_input_delay -min 0.5 ns). The RTL testbench changes
# adc_valid_* / adc_raw_* at the clock edge (zero delay); with the post-layout clock latency of 1.6 ns at the slow corner that
# is a hold violation of the stimulus, not of the design (t12: is_smp stuck high; t9f passed by chance of the latency).
t = t.replace(".adc_valid_a(adc_valid_a), .adc_raw_a(adc_raw_a), .adc_valid_b(adc_valid_b), .adc_raw_b(adc_raw_b),",
              ".adc_valid_a(adc_valid_a_d), .adc_raw_a(adc_raw_a_d), .adc_valid_b(adc_valid_b_d), .adc_raw_b(adc_raw_b_d),")
t = t.replace("    r1_ctrl_top dut (", "    wire #0.5 adc_valid_a_d = adc_valid_a, adc_valid_b_d = adc_valid_b;   // GL: SDC set_input_delay -min 0.5 ns\n"
              "    wire [13:0] #0.5 adc_raw_a_d = adc_raw_a, adc_raw_b_d = adc_raw_b;\n    r1_ctrl_top dut (", 1)
open(sys.argv[2], "w").write(t)
