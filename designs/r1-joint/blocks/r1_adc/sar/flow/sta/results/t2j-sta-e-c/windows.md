| Corner | clk -> CDAC lines (ns) | clk -> valid / raw (ns), need valid min >= 0.5, max <= 7.0 | mclk rise / fall -> comparator clocks (ns) | true / complement skew (ns) | clk -> busy -> window close (ns) | latch close margin (ns) | ctrl request -> trk (ns) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fast | 0.482 .. 0.790 (limit 0.71) FAIL | 0.930 .. 1.170 / 0.460 .. 0.590 pass | 0.270 .. 0.530 / 0.230 .. 0.420 | 0.090 | 1.200 (limit 1.220) pass | 0.15 pass | 0.290 .. 0.850, A/B 0.560 |
| typ | 0.723 .. 1.180 (limit 1.18) pass | 1.400 .. 1.780 / 0.690 .. 0.900 pass | 0.400 .. 0.790 / 0.340 .. 0.640 | 0.140 | 1.780 (limit 1.820) pass | 0.14 pass | 0.430 .. 1.300, A/B 0.870 |
| slow | 1.141 .. 1.880 (limit 2.07) pass | 2.250 .. 2.830 / 1.090 .. 1.410 pass | 0.640 .. 1.240 / 0.530 .. 1.000 | 0.220 | 2.790 (limit 2.950) pass | 0.11 pass | 0.670 .. 2.070, A/B 1.400 |
