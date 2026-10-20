#!/bin/sh
# post_r2_all.sh: regenerate the revision-2 conversion results in sim/results/r2/ from the raw files.
# Needs G1_RESULTS_ROOT. Order: (1) full ramp -> ramp-calibrated weights (bench method, D12),
# (2) windows, sine, held-frame decks with those weights.
set -e
cd "$(dirname "$0")/../.."
R=$G1_RESULTS_ROOT/r1_adc
S=sim/results/r2
python3 sim/r2/post_adc2.py static $S/ramp_tt.json 3.178e-3 $S/r2-ramp-tt-a-f1_segments.json $S/r2-ramp-tt-a-f2_segments.json > /dev/null
W="--weights $S/ramp_tt.json"
for w in tt27-a-c1024:-0.4629552 tt27-a-c2048:-0.0035888 tt27-a-c3072:0.4557776 ss125-a-c2048:-0.0035888 \
         ffm40-a-c2048:-0.0035888 vdd108-a-c2048:-0.0035888 vdd132-a-c2048:-0.0035888; do
  n=${w%%:*}; v0=${w#*:}
  python3 sim/r2/post_adc2.py static $S/win_$n.json 2.243e-4 $R/r2-win-$n/codes.raw@$v0 $W > /dev/null
  python3 sim/r2/post_adc2.py static $S/win_${n}_designW.json 2.243e-4 $R/r2-win-$n/codes.raw@$v0 > /dev/null
done
python3 sim/r2/post_adc2.py dyn $S/dyn_tt_a_n256.json 25 256 0.88 $S/r2-dyn-tt-a-n256_segments.json $W > /dev/null
python3 sim/r2/post_adc2.py dyn $S/dyn_tt_a_n256_designW.json 25 256 0.88 $S/r2-dyn-tt-a-n256_segments.json > /dev/null
python3 sim/r2/post_adc2.py dyn $S/dyn_tt_ab_n128.json 13 128 0.88 $S/r2-dyn-tt-ab-n128_segments.json $W > /dev/null
python3 sim/r2/post_adc2.py dyn $S/dyn_tt_ab_n128_designW.json 13 128 0.88 $S/r2-dyn-tt-ab-n128_segments.json > /dev/null
python3 sim/r2/post_adc2.py frames $S/isa_tt.json $R/r2-isa-tt-a/codes.raw "SIN +0.4 V (CM 0.6),COS -0.4 V (CM 0.6);ISA +0.85 V (CM 0.57),ISB -0.85 V (CM 0.57);SIN -0.4 V,COS +0.4 V;ISA -0.85 V,ISB +0.85 V" $W > /dev/null
python3 sim/r2/post_adc2.py frames $S/quick_tt.json $R/r2-quick-tt-acc/codes.raw "0,0;+0.3,-0.3;-0.3,+0.3;+0.9,-0.9;-0.9,+0.9;+0.0003,-0.0003;+0.99,-0.99;-0.99,+0.99" $W > /dev/null
python3 sim/r2/post_ref_adc.py $R/r2-ref-adc-tt-buf-a/codes.raw $R/r2-ref-adc-tt-ideal-a/codes.raw $S/ramp_tt.json $S/ref_adc_tt.json > /dev/null
python3 sim/r2/post_cmp2_noise.py $R/r2-cmp-noise-tt-cm01-d/noise_B16.txt $S/cmp2_tran_tt27.json B16_cm0.1 $S/cmp2_noise_tt27_cm01_b16.json > /dev/null
python3 sim/r2/post_cmp2_noise.py $R/r2-cmp-noise-ss125-cm01-d/noise_B16.txt $S/cmp2_tran_ss125.json B16_cm0.1 $S/cmp2_noise_ss125_cm01_b16.json > /dev/null
echo done
