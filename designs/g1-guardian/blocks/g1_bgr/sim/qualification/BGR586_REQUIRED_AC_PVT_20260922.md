# Unchanged586 process, supply and local AC checks

The[81-condition audit](bgr586-pvt81-audit-20260922.json) includes all3HBT×3MOS×3R
corners and3.0/3.3/3.6V supplies, each with34 points from−40 to125C. The already
qualified nominal condition is reused literally;80 new conditions were attempted.
80/81 conditions completed with all2842 parameters exact before/after and finite
endpoint-complete waves. None of those80 exceeds the unchanged50ppm/C criterion;
the maximum simulated TC is31.438815ppm/C.

**Failed:** typHBT/ffMOS/typR at3.0V hit its120s watchdog at120.165s, last logged
DC progress30C. No completed sweep, AFTER vector or TC is inferred for it.
The81-condition campaign is not an all-pass result and supplies no survivor-yield
claim. The original failed leaf remains in[portable evidence](portable_evidence/required-ac-pvt-20260922).

Thirteen standalone AC analyses completed numerically using literal historical
decks with only the source replaced by exact nominal586. Noise is simulated
100.111µV RMS over1Hz–10MHz; PSRR rejection is102.807dB at1Hz and81.953dB at1kHz.
No noise budget was adopted by this diagnostic.

| Conditional Tian cut | Nominal minimum\|1+T\| | Slow | Fast |
|---|---:|---:|---:|
| PBIAS | 0.637686 | 0.634123 | 0.845034 |
| PCASC | 0.713673 | 0.718208 | 0.909681 |

Each cut uses paired voltage/current AC injections, preserving DC connectivity.
Source reconstruction after removing the probe and restoring the156 PBIAS or77
PCASC gate pins is byte exact. All1036 original devices remain. Other loops stay
closed; this is **not global stability, phase-margin or gain-margin acceptance**.
The numerical definitions are unchanged from the earlier local-loop harness.
Noise uses nominal27C; slow iswcs/ss/wcs,3.0V,−40C; fast isbcs/ff/bcs,3.6V,125C.

The common fixture is ideal1V IPTAT termination and1pF VREF. Source hash:
586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b,
with336MOS/399R/301HBT and the historical329 capacitances unchanged.
Built against pinned image manifest5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0,
ngspice46 and PDK84374023ee8b4b126bebbba67fcbada0a9c0ff0b; model/OSDI hashes
were checked against the qualified source runtime. Initialization warnings
remain in logs and summaries; no model-card edits or model-validity waiver.

Commands and exact source/deck/runtime hashes are in the portable receipts.
New physicalCC, actual loaded joint calibration and global stability: **not run**
by these checks. Separate existing matched-load results do not substitute for
these missing scopes.

## Nominal capacitive-load observations

The three literal historical 40 µs, 100 nA load-step fixtures also completed
with source 586, at nominal process, 27 C and 3.3 V. VREF load capacitances
were 0.1, 10 and 100 pF. Each produced 20,020 finite rows through 40 µs;
simulator wall times were 166.445, 152.951 and 154.351 seconds respectively.
[Portable receipts](portable_evidence/capload-nominal3-20260922) retain exact
commands, source/deck hashes, numerical results and raw-wave hashes.
These are numerical load-response observations: no new recovery-error or
stability acceptance budget was adopted. The six slow/fast capacitive-load
conditions and the new physical capacitance view remain **not run** here.
