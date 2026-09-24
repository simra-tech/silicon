# Four interface midpoint clips

Exact delivered-GDS geometry and unchanged pinned KPEX rules were used.
Each clip is **20 µm long**, with transverse contexts of 12, 24 and 48 µm.
Targets and the prospective gates are in
[the coupling contract](INTERFACE_COUPLING_CONTRACT_20260922.md).

All 12 clip preparations/extractions and all 96 independent ngspice capacitor
matrix checks **passed**. The last 11 cases, including explicit reuse of one
completed extraction, are recorded in
[the context manifest](interface-context-20260922-r2/manifest.json).
The original 12 µm ISENSE/clock pilot has its separate
[AC checks](interface-isense-clock-w12-20260922-r1/ac_checks.json).

The maximum relative matrix-entry change from 24 to 48 µm was
7.4472e−6 (0.00074472%), below the prospectively declared 1% gate.

| Victim / neighbor | Mutual C (fF) | Victim-to-ground equivalent (fF) | Neighbor-to-ground equivalent (fF) |
| --- | ---: | ---: | ---: |
| ISENSE / comparator clock | 3.488206 | 3.829637 | 1.087630 |
| VREF / DAC soft bit 5 | 3.374785 | 4.255471 | 2.096923 |
| Buffered VREF / DAC hard bit 4 | 3.523705 | 4.116325 | 2.040374 |
| IPTAT / ISENSE | 3.488613 | 3.865093 | 2.191705 |

These are simulated/extracted values for the 48 µm context, actual fill,
floating-fill boundary. Substrate and other context conductors are grounded
in the reduction. Their actual switching behavior and physical connectivity
outside the window are not thereby qualified. Fill connected to another
conductor follows that extracted conductor; it is not made artificially floating.

An earlier analysis **failed** because long SPICE capacitor records used
continuation lines. Its extraction completed and is retained unchanged.
The separate strict parser handles continuations and physical net aliases,
rejects target shorts, missing targets and malformed values, and passed its
five unit tests. Recovery then passed all eight independent AC matrix checks.
The original parser and failed artifacts remain unchanged.

## Whole-interval follow-up

The clock shared interval plus 10/20 µm end margins was extracted with 12/24 µm
transverse context. All four clips and 32 independent AC checks **passed**;
the aggregate full-matrix context test **failed**, with maximum relative change
18.2721%. The mutual end-margin test passed (maximum relative change 7.9579e−6).
See [the retained interval manifest](interface-clock-interval-20260922-r1/manifest.json).

Wider windows include more of the actual horizontal clock conductor beyond the
parallel interval, so this is not fixed-target ground-capacitance convergence.
Floating-fill mutual values are 5.232855634, 5.232828531, 5.233872140 and
5.233830490 fF for width/margin combinations 12/10, 12/20, 24/10 and 24/20 µm.
These values support a separately labeled incremental mutual-capacitance
diagnostic, not a retroactive full-matrix pass or whole-route R/C model.

The longer IPTAT/ISENSE full-interval attempt **failed** its 120 s KPEX watchdog
with both no-fill and actual-fill variants; database preparation passed but
electrical extraction results are **not run** to completion. The wrapper's
zero exit code does not override those child timeouts.

Actual-impedance, clocked electrical acceptance remains **not run** pending the
paired diagnostic. These midpoint values must not be scaled by length and
presented as full-route extraction. No production geometry or whole-interface
acceptance follows. Physical measurement is **not applicable** to the numerical
cross-check; silicon coupling measurement remains **not run**.
