| Corner | clk -> CDAC lines (ns) | clk -> valid / raw (ns), need valid min >= 0.5, max <= 7.0 | mclk rise / fall -> comparator clocks (ns) | true / complement skew (ns) | clk -> busy -> window close (ns) | latch close margin (ns) | ctrl request -> trk (ns) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fast | 0.480 .. 0.830 (limit 0.71) FAIL | 0.920 .. 1.150 / 0.450 .. 0.590 pass | 0.260 .. 0.610 / 0.210 .. 0.560 | 0.180 | 1.240 (limit 1.210) FAIL | 0.16 pass | 0.320 .. 1.030, A/B 0.710 |
| typ | 0.720 .. 1.230 (limit 1.18) FAIL | 1.380 .. 1.760 / 0.670 .. 0.900 pass | 0.380 .. 0.930 / 0.310 .. 0.860 | 0.290 | 1.880 (limit 1.800) FAIL | 0.15 pass | 0.470 .. 1.590, A/B 1.110 |
| slow | 1.140 .. 1.930 (limit 2.07) pass | 2.220 .. 2.800 / 1.060 .. 1.400 pass | 0.600 .. 1.470 / 0.500 .. 1.340 | 0.440 | 2.970 (limit 2.910) FAIL | 0.14 pass | 0.760 .. 2.550, A/B 1.770 |
