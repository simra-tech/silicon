#!/usr/bin/env python3
"""Write run.json for every sign-off run of 2026-10-21 into the bulk root, and a copy into sim/signoff/results/<id>/.
usage: write_run_json.py <results_root>/r1_ctrl   (run from the block directory)"""
import json, os, sys, shutil
root = sys.argv[1]
PDK = '84374023ee8b4b126bebbba67fcbada0a9c0ff0b'
TOOLS = {'container': 'tapeoutbench-eda:latest sha256:ddeb69576f28', 'iverilog': 'Icarus Verilog 14.0 (devel) s20260301', 'yosys': '0.67 (2d1509d1b)', 'opensta': 'sta 3.1.0'}
RTL = '6ca24fce22d79594601c5d73de0db91f73fd3fa7b62944b96e08eda01e2f6eb0'
COMMON = dict(block='r1_ctrl', pdk_commit=PDK, tools=TOOLS, rtl_concat_sha256=RTL, subject='hardening run r1ctrl_ll_20261021_t7 (RTL revision 0.4)')
def GL(cmd, q, res, disp): return dict(command=cmd, question=q, result=res, disposition=disp)
RUNS = {
 'r1ctrl_20261021_t7sta': dict(
   command='flow/run.sh sh sim/signoff/sta_all.sh <dir>; sta_borrow.sh; sta_fanout.sh; sta_names.sh; sta_en.sh (OpenSTA on t7 final/nl + final/sdc + final/spef/nom)',
   question='What is the true setup slack per corner, the hold slack, the max-fanout nets, and the EN to gate delay of the t7 netlist?',
   result='setup (excluding latch borrow) typ +9.570 recovery / +9.725 flop, fast +10.235 / +11.247, slow +1.776 (meas_angle[2] -> u_pos.cx[15]); latch borrow <= 1.02 ns of 11.47 (slow); hold typ +0.0748, fast +0.0209, slow +0.1834; 6 max-fanout nets, limit 8; en_pad -> gate_x 0.90 / 0.58 / 1.47 ns (typ / fast / slow)',
   disposition='passed (information; no path below +0.3 ns at slow)'),
 'r1ctrl_gl_20261021_a': GL('flow/run.sh sh sim/signoff/run_gl.sh r1ctrl_gl_20261021_a slow 2', 'Gate-level simulation', 'stopped before any result (testbench status bit-width error); see ABORTED.txt', 'failed (abandoned, kept)'),
 'r1ctrl_gl_20261021_b': GL('flow/run.sh sh sim/signoff/run_gl.sh r1ctrl_gl_20261021_b slow|typ 2', 'Do the chip-level checks pass on the t7 post-layout netlist? (SDF NOT applied: Icarus compiled without -gspecify, so this is a zero-delay gate-level run)', 'zero-delay gate level, mode dirs slow and typ are identical in function: biss 23.810 47 pass + 1 skipped, ssi, spi, gate, safe, cal all pass; biss 33.333 and 47.619 were stopped by me (rerun in run h)', 'zero-delay fallback; passed'),
 'r1ctrl_gl_20261021_c': GL('flow/run.sh sh sim/signoff/run_gl.sh r1ctrl_gl_20261021_c slow 2', 'SDF gate level', 'Icarus SDF reader crashed (NULL handle in vpi_scan) on INTERCONNECT entries and escaped instance names', 'failed (tooling)'),
 'r1ctrl_gl_20261021_d': GL('flow/run.sh sh sim/signoff/run_gl.sh r1ctrl_gl_20261021_d slow 2', 'SDF gate level', 'SDF header (VOLTAGE ::) and min:typ:max triples rejected', 'failed (tooling)'),
 'r1ctrl_gl_20261021_e': GL('flow/run.sh sh sim/signoff/run_gl.sh r1ctrl_gl_20261021_e slow|typ 2', 'SDF gate level', 'empty top-level ABSOLUTE block rejected (syntax error at line 14)', 'failed (tooling)'),
 'r1ctrl_gl_20261021_f': GL('flow/run.sh sh sim/signoff/run_gl.sh r1ctrl_gl_20261021_f slow|typ 2 (prep_sdf.py: instance renames, INTERCONNECT dropped, triples collapsed to max / typ)', 'Do the chip-level checks pass on the t7 post-layout netlist with SDF cell delays at slow (nom_slow_1p08V_125C, max) and typ (nom_typ_1p20V_25C)?', 'see reports/signoff_v04.md section 3 and sim/signoff/results/gl_summary.md', 'see summary'),
 'r1ctrl_gl_20261021_g': GL('flow/run.sh sh sim/signoff/run_gl.sh r1ctrl_gl_20261021_g slow 1 with GL_JOBS=biss:23.810 (model copied from run f)', 'biss at 23.810 ns, slow SDF', 'see reports/signoff_v04.md section 3', 'see summary'),
 'r1ctrl_gl_20261021_h': GL('flow/run.sh sh sim/signoff/run_gl.sh r1ctrl_gl_20261021_h zd 2 with GL_JOBS="biss:33.333 biss:47.619" (model copied from run b)', 'biss at 33.333 and 47.619 ns, zero delay', 'see reports/signoff_v04.md section 3', 'see summary'),
 'r1ctrl_gl_20261021_i': GL('flow/run.sh sh sim/signoff/run_gl_one.sh r1ctrl_gl_20261021_f/typ r1ctrl_gl_20261021_i/typ biss 23.810 TYPICAL', 'biss at 23.810 ns, typ SDF (line-buffered, partial results kept)', 'see reports/signoff_v04.md section 3', 'see summary'),
 'r1ctrl_eqy_20261021_a': dict(command='flow/run.sh sh sim/signoff/run_eqy.sh r1ctrl_eqy_20261021_a (strategy sby)', question='RTL vs post-synthesis netlist equivalence with eqy', result='partitions "equivalence unknown"; SMT engine gave no status', disposition='failed (kept)'),
 'r1ctrl_eqy_20261021_b': dict(command='run_eqy.sh r1ctrl_eqy_20261021_b (strategy sat)', question='as above', result='"No configured strategy supports partition" (memory)', disposition='failed (kept)'),
 'r1ctrl_eqy_20261021_c': dict(command='run_eqy.sh r1ctrl_eqy_20261021_c (sat, memory_map)', question='as above', result='305 of 1843 names matched; first partitions not proven; stopped by me', disposition='abandoned (kept)'),
 'r1ctrl_eqy_20261021_d': dict(command='run_eqy.sh r1ctrl_eqy_20261021_d (sat, memory_map, splitnets)', question='as above', result='1836 names matched; 331 partitions at about 1 min each; stopped by me', disposition='abandoned (kept)'),
 'r1ctrl_equiv_20261021_a': dict(command='run_equiv.sh r1ctrl_equiv_20261021_a', question='as above, Yosys equiv_* flow', result='ERROR: async FF cell has no SAT model (async2sync missing)', disposition='failed (kept)'),
 'r1ctrl_equiv_20261021_b': dict(command='run_equiv.sh r1ctrl_equiv_20261021_b (equiv_make, async2sync, equiv_simple, equiv_induct)', question='as above', result='1835 name pairs matched; equiv_simple proved 797 of 1882 compare points, 1085 unproven; equiv_induct did not converge and was stopped', disposition='inconclusive (not passed)'),
 'r1ctrl_sdftry_20261021': dict(command='sim/signoff/sdftry/try.sh', question='Which SDF variant does the Icarus reader accept?', result='full SDF crashes; without INTERCONNECT entries the reader works but needs renamed instances and collapsed triples', disposition='tooling study (information)'),
}
os.makedirs('sim/signoff/results', exist_ok=True)
for rid, d in RUNS.items():
    bulk = os.path.join(root, rid)
    if not os.path.isdir(bulk):
        continue
    j = dict(run_id=rid, **COMMON, **d, inputs='scripts under sim/signoff/, t7 run files under <G1_RESULTS_ROOT>/r1_ctrl/r1ctrl_ll_20261021_t7/', bulk_results='<G1_RESULTS_ROOT>/r1_ctrl/' + rid)
    json.dump(j, open(os.path.join(bulk, 'run.json'), 'w'), indent=1)
    os.makedirs('sim/signoff/results/' + rid, exist_ok=True)
    json.dump(j, open('sim/signoff/results/%s/run.json' % rid, 'w'), indent=1)
    print('wrote', rid)
