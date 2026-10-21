#!/bin/sh
# run_ref4.sh <cpu> <id> <stag> <ref> <refl> [vref] [corner temp vdd]: one R2-4 reference-settling run (10 frames,
# sim/r4/points/ref10.json, full save). Revision-4 campaign helper.
cd "$(dirname "$0")/../.."
: "${G1_RESULTS_ROOT:?set G1_RESULTS_ROOT to the results root}"; export G1_RESULTS_ROOT
CPU=$1; ID=$2; N=$3; R=$4; RL=$5; VR=${6:-1.0}; C=${7:-mos_tt}; T=${8:-27}; V=${9:-1.2}
python3 sim/r4/run_points4.py --id $ID --cpu $CPU --points sim/r4/points/ref10.json --stag $N --ref $R --refl $RL \
  --vref $VR --corner $C --temp $T --vdd $V --save full \
  --question "R2-4 rev 4: reference settling, stagger $N ticks, ref $R, LSB-array ref $RL, $C/$T C/$V V" \
  --disposition "R2-4 comparison run (post_ref4.py)"
