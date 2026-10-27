| Corner | clk -> CDAC lines (ns) | clk -> valid / raw (ns), need valid min >= 0.5, max <= 7.0 | mclk rise / fall -> comparator clocks (ns) | true / complement skew (ns) | clk -> busy -> window close (ns) | latch close margin (ns) | ctrl request -> trk (ns) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fast | 0.490 .. 0.650 (limit 0.71) pass | 0.900 .. 1.110 / 0.440 .. 0.500 pass | 0.330 .. 0.730 / 0.320 .. 0.600 | 0.260 | 1.360 (limit 1.280) FAIL | 0.16 pass | 0.340 .. 0.810, A/B 0.470 |
| typ | 0.737 .. 0.990 (limit 1.18) pass | 1.340 .. 1.700 / 0.660 .. 0.760 pass | 0.500 .. 1.120 / 0.490 .. 0.910 | 0.420 | 2.090 (limit 1.920) FAIL | 0.16 pass | 0.500 .. 1.270, A/B 0.760 |
| slow | 1.163 .. 1.550 (limit 2.07) pass | 2.140 .. 2.700 / 1.050 .. 1.190 pass | 0.800 .. 1.780 / 0.770 .. 1.440 | 0.650 | 3.310 (limit 3.110) FAIL | 0.15 pass | 0.820 .. 2.030, A/B 1.200 |
