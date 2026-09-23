# BGR586 seed 44090 reverse-grid method diagnostic

Two separately gated, sequential CPU0 runs used the original 120 s watchdog
per case. Source `586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b`,
image, PDK, models, seed-specific input files and solver options were held.
The only deck edit in each case was `dc temp -40 125 5` to
`dc temp 125 -40 -5`. No IC, UIC, nodeset or tolerance change was made.
The original seed 44090 population failure and successful forward seed 44089
remain unchanged.

| Diagnostic | Engine | Frozen parameters | 34-point result | Exact comparison |
| --- | --- | --- | --- | --- |
| 44090 reverse | Completed, 22.8116 s | All 2,842 BEFORE and AFTER exact | Finite; original TC formula gives 10.0149698796 ppm, diagnostic only | 30°C row versus independent 30°C OP: **failed** bit-exact; 11/12 cells differ, maximum absolute difference 1.1641310138e-10 |
| 44089 reverse control | Completed, 21.4095 s | All 2,842 BEFORE and AFTER exact | Finite; original TC formula gives 9.7988111222 ppm, diagnostic only | Temperature-aligned versus saved forward 34 rows: **failed** bit-exact; 374/408 cells differ, maximum absolute difference 2.8320013001e-10 |

The saved 44089 forward TC was 9.7988111354 ppm. The small numerical
differences are reported, **not** accepted through a new tolerance. Therefore
reverse-grid parity is unqualified; the reverse 44090 result is not used as a
population replacement, TC qualification or yield estimate. It demonstrates
only that the same frozen realization can complete this changed sweep order.
Both runs retained the initial temperature-limiting NaN message. The 44090
reverse log also retained 1,488 model `vmax` warnings; no model-validity pass
is inferred. No further watchdog ladder was run.

The summaries are SHA-256
`87fd44a1fccd7d9692d589a9a7960f86cb3f689ede8af53268131c35673d27c6`
(44090) and
`7e5ff692a77a18e37a5c7a4253107ac4a19de331ef3f2c2867a9b11af1204373`
(44089). Diagnostic deck SHA-256 values are respectively
`48d1a72325b2fa77178bcaa9b8282461803db23875969572dad7655c028466e1`
and `e8e46539c459f951b58068d6e3708a775a4da403cd346d1d73c7e3bff79614f7`.
The fresh resource-gate SHA-256 values were
`19722a23fb745647149f8816e796c94e7dc978b51e46487ff67beaca84302761`
and `ac09256d7331618160275c25a52960461922ddea0d6dbe92cecb998c1b0e14aa`.
Bulk artifacts remain under logical result identities
`bgr586-s44090-reverse-diagnostic-20260923-r1` and
`bgr586-s44089-reverse-control-20260923-r1`, not copied into Git.

The exact invocation for each case was:

```sh
G1_CPUSET=0 G1_CPUS=1 G1_RESULTS_ROOT="$G1_RESULTS_ROOT" flow/run.sh python3 designs/g1-guardian/blocks/g1_bgr/sim/qualification/run_586_reverse_grid_diagnostic.py --seed <44090-or-44089> --output "$G1_RESULTS_ROOT/<fresh-run-id>" --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0 --resource-gate "$RESOURCE_GATE"
```

Population recovery, original forward-grid TC for 44090, full-chip electrical
qualification and model-validity qualification: **not run/not established**.
