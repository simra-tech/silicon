set terminal pngcairo size 1600,1100 font 'DejaVu Sans,19'
set output 'designs/g1-guardian/review/results/top_soft_trip.png'
set multiplot layout 2,1 title 'Simulated soft-trip integration test | behavioural front end, tt, 27 C'
set grid back
set key outside top center horizontal
set xrange [0:1250]
set xlabel 'Time (microseconds)'
set ylabel 'Voltage (V)'
plot 'designs/g1-guardian/blocks/g1_top/sim/results/waves/b_sch_beh_tt_27C_clockfix.txt' using ($1*1e6):18 with lines lw 2 title 'Comparator input', '' using ($1*1e6):19 with lines lw 2 title 'Soft threshold at comparator'
set ylabel 'Voltage (V)'
plot 'designs/g1-guardian/blocks/g1_top/sim/results/waves/b_sch_beh_tt_27C_clockfix.txt' using ($1*1e6):2 with lines lw 3 title 'GATE', '' using ($1*1e6):21 with lines lw 2 title 'Digital trip'
unset multiplot
set output 'designs/g1-guardian/review/results/top_rearm.png'
set multiplot layout 2,1 title 'Simulated hard trip and re-arm | transistor-level blocks, tt, 27 C'
set xrange [0:50]
set ylabel 'Voltage (V)'
plot 'designs/g1-guardian/blocks/g1_top/sim/results/waves/f_sch_tl_tt_27C_clockfix.txt' using ($1*1e6):2 with lines lw 3 title 'GATE', '' using ($1*1e6):12 with lines lw 2 title 'EN core'
set ylabel 'Load current (A)'
plot 'designs/g1-guardian/blocks/g1_top/sim/results/waves/f_sch_tl_tt_27C_clockfix.txt' using ($1*1e6):23 with lines lw 3 title 'Load current'
unset multiplot
