#!/usr/bin/env bash
# Formal sequential equivalence of the frozen ECO RTL against the r3 candidate v2 netlist
# (4b83f181, copied to build/g1_gls_eco/in_r3cand2/) plus a negative control against the
# superseded v1 netlist (c3aa2856, build/g1_gls_eco/in_r3cand/). From the repository root:
#   G1_CPUSET=46-47 G1_CPUS=2 G1_CONTAINER_ENGINE=podman \
#     G1_WORKDIR=designs/g1-guardian/blocks/g1_ctrl/sim/gls_eco_r3v2/equiv flow/run.sh bash run_equiv.sh
set -uo pipefail
yosys -V; yosys-abc -q "version" 2>/dev/null | head -1
sha256sum /work/build/g1_gls_eco/in_r3cand2/g1_digital.nl.v /work/build/g1_gls_eco/in_r3cand/g1_digital.nl.v \
  /work/designs/g1-guardian/blocks/g1_ctrl/rtl_eco_20260925/*.v /work/designs/g1-guardian/blocks/g1_seu/rtl_eco_20260925/*.v
yosys -l seq_equiv.log -q seq_equiv.ys
yosys-abc -c "read_aiger miter.aig; print_stats; strash; dprove -v" > dprove.log 2>&1; tail -1 dprove.log
yosys -l seq_equiv_negctl.log -q seq_equiv_negctl.ys
yosys-abc -c "read_aiger miter_negctl.aig; print_stats; strash; dprove -v" > dprove_negctl.log 2>&1; tail -1 dprove_negctl.log
# name-based attempt (diagnostic only): yosys equiv_make/equiv_simple/equiv_induct
yosys -l equiv.log -q equiv.ys; grep "Of those" equiv.log
