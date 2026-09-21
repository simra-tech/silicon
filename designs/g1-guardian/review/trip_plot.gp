set terminal pngcairo size 1500,700 font 'DejaVu Sans,18'
set output 'designs/g1-guardian/review/trip_response.png'
set title 'Simulated chip-path gate response — nominal schematic models'
set xlabel 'Time after load step (microseconds)'
set ylabel 'GATE voltage (V)'
set xrange [-0.3:3]
set yrange [-0.1:3.6]
set grid back
set key top right
set border 3
set tics nomirror
set arrow from graph 0, first 0.33 to graph 1, first 0.33 nohead lc rgb '#808080' dt 2
plot 'designs/g1-guardian/blocks/g1_top/sim/results/waves/c_sch_tl_tt_27C_clockfix.txt' using ($1*1e6-30):2 with lines lw 3 lc rgb '#245b87' title 'Digital hard-trip path', 'designs/g1-guardian/blocks/g1_top/sim/results/waves/c_fast_sch_tl_tt_27C_clockfix.txt' using ($1*1e6-30):2 with lines lw 3 lc rgb '#d07820' title 'FAST_EN path'
