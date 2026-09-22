# Expanded digital clock, phase and reset screen

**Passed:** 4410 assertions, zero errors, unchanged digital RTL. This is a
functional RTL sensitivity screen, not timed GLS, physical IO timing or
metastability qualification.

The retained CDC bench was expanded to five oscillator frequencies
7.367/8/10/12/13.768MHz, three serial-period ratios1/2/10, and three assumed
SDI/SDO delay profiles2/0,5/5,10/10ns. Each combination covers16 relative phases,
24 partial-read reset positions, stopped-clock write rejection and EN-reset
recovery. SCLK remains no faster than OSC. The outer frequency points are
diagnostic beyond the prior8–12MHz assumption; their functional passes do not
extend physical timing sign-off. Delays are engineering sensitivities, not
extracted pad delays.

Run `cdc-expanded-20260922-r3` used pinned Icarus14 development build
`s20260301-328-geda9fdcd-dirty` and the verified amd64 EDA runtime. Compilation
passed0.101s; simulation passed23.024s, finishing at simulated118.490589280ms.
All bound source hashes remained unchanged. The full wrapper took36.533s.

| Retained check | Status |
| --- | --- |
| R1 compile: invalid Verilog real-literal spelling `2.` / `0.` | failed |
| R2 compile after literal-only correction | passed |
| R2 simulation: inherited100ms fixture watchdog | failed; full assertion set not reached |
| R3 same stimulus/assertions, literal correction and200ms fixture watchdog | passed;4410/4410 |
| Actual pad-delay extraction / timed GLS / metastability MTBF | not run |
| Statistical seed / physical measurement for this digital test | not applicable |

The expanded procedural schedule requires about119ms. Increasing the bench
watchdog allowed that schedule to finish; it did not change any stimulus time,
RTL, assertion or120s wall-clock limit. Both earlier failed runs are preserved.

Reproduce using [run_cdc_expanded_r3.py](run_cdc_expanded_r3.py) with
`--output NEW_RESULTS_DIRECTORY` inside the pinned runtime on one allocated CPU.
The wrapper hash-binds the retained original expanded runner and CDC bench.

| Bulk artifact | SHA256 |
| --- | --- |
| R1 summary | `ee62333cb3c94805d4969fe816ec89917ed0a4087088a371bc993f0710e795fb` |
| R2 summary | `308b55d307e9627ffe9a759d65b85f1f95ac8a771a0551416df1378a1f0913c6` |
| R3 summary | `7a8fc6509d969c094b42c983c65d5d9072d51279fa242a255d5e2357356a1a14` |
| R3 simulation log | `8f4ed50788cc43976f78d3e9238d39a1d5907088bb9a2ae352b807e072ba0bd0` |
| R3 generated bench | `d11825455f4c962d6c28ed9caafcf6d8280219fb5ae493c4953a0b3882aeea68` |
