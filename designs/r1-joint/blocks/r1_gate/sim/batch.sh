#!/bin/sh
# Runs the r1_gate case matrix, one case after the other (one CPU). Usage (repo root):
#   G1_CPUSET=119 G1_CPUS=1 G1_RESULTS_ROOT=<G1_RESULTS_ROOT> sh designs/r1-joint/blocks/r1_gate/sim/batch.sh <tag>
TAG=$1
P="python3 designs/r1-joint/blocks/r1_gate/sim/run_gate.py --tag $TAG --nodcn 1"
# A: timing, fault path, edge overlap; G1 supply model (0.5 ohm + 1 nF), ideal ground
for load in 5n 1n; do for c in tt ss ff; do for t in hv lv; do
  $P --topo $t --corner $c --load $load --pkg 0 --seg 4
done; done; done
# B: simultaneous switching with the package model, 5 nF, decoupling 1 nF and 100 pF
for cd in 1n 100p; do for c in tt ss ff; do for t in hv lv; do
  $P --topo $t --corner $c --load 5n --pkg 1 --cdec $cd --seg 4
done; done; done
# C: output stage cross-conduction with a light load (1 pF)
for c in tt ss ff; do
  $P --topo lv --corner $c --load 1p --pkg 0 --seg 0.5
done
