#!/usr/bin/env bash
# Red-team 2026-09-27. From the repository root:
#   G1_CPUSET=16-17 G1_CPUS=2 G1_CONTAINER_ENGINE=podman \
#     G1_WORKDIR=designs/g1-guardian/review/redteam-20260927/digital/equiv_en_reset flow/run.sh bash run_equiv_en.sh
set -uo pipefail
yosys -V
sha256sum /work/build/g1_gls_eco/in_r3cand2/g1_digital.nl.v
yosys -l seq_equiv_en.log -q seq_equiv_en.ys
yosys-abc -c "read_aiger miter_en.aig; print_stats; strash; dprove -v" > dprove_en.log 2>&1; tail -1 dprove_en.log
# negative control: the superseded v1 netlist c3aa2856 (MODE reset 0x23) must be found not equivalent
sha256sum /work/build/g1_gls_eco/in_r3cand/g1_digital.nl.v
yosys -l seq_equiv_en_negctl.log -q seq_equiv_en_negctl.ys
yosys-abc -c "read_aiger miter_en_negctl.aig; print_stats; strash; dprove -v" > dprove_en_negctl.log 2>&1; tail -1 dprove_en_negctl.log
