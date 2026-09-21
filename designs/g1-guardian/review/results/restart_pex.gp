set terminal pngcairo size 1600,1100 font 'DejaVu Sans,20'
set output 'designs/g1-guardian/review/results/restart_pex_4us.png'
set multiplot layout 2,1 title 'New simulated startup diagnostic | block capacitance PEX, tt, 27 C'
set grid back
set key outside top center horizontal
set xrange [0:4]
set xlabel 'Time (microseconds)'
set ylabel 'Voltage (V)'
plot 'designs/g1-guardian/blocks/g1_top/sim/results/waves/c_pex_tl_tt_27C_clockfix_t4_prefix_s2_20260921_pex4us.txt' using ($1*1e6):2 with lines lw 3 lc rgb '#245b87' title 'VREF', '' using ($1*1e6):3 with lines lw 3 lc rgb '#d07820' title 'ISENSE'
set ylabel 'GATE voltage (V)'
plot 'designs/g1-guardian/blocks/g1_top/sim/results/waves/c_pex_tl_tt_27C_clockfix_t4_prefix_s2_20260921_pex4us.txt' using ($1*1e6):4 with lines lw 3 lc rgb '#245b87' title 'External gate model'
unset multiplot
