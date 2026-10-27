| Corner | clk -> CDAC lines (ns) | clk -> valid / raw (ns), need valid min >= 0.5, max <= 7.0 | mclk rise / fall -> comparator clocks (ns) | true / complement skew (ns) | window gates: clock-gating check slack (ns) | latch close margin (ns) | ctrl request -> trk (ns) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fast | 0.490 .. 0.650 (limit 0.71) pass | 0.900 .. 1.110 / 0.440 .. 0.500 pass | 0.330 .. 0.730 / 0.320 .. 0.600 | 0.250 | setup 22.406 / hold 0.228 pass | 0.16 pass | 0.340 .. 0.810, A/B 0.160 |
| typ | 0.737 .. 0.990 (limit 1.18) pass | 1.340 .. 1.700 / 0.660 .. 0.760 pass | 0.500 .. 1.120 / 0.490 .. 0.910 | 0.400 | setup 21.913 / hold 0.366 pass | 0.16 pass | 0.500 .. 1.270, A/B 0.250 |
| slow | 1.163 .. 1.550 (limit 2.07) pass | 2.140 .. 2.700 / 1.050 .. 1.190 pass | 0.800 .. 1.780 / 0.770 .. 1.440 | 0.630 | setup 21.114 / hold 0.710 pass | 0.15 pass | 0.820 .. 2.030, A/B 0.410 |
