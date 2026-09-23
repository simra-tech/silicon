# Isolated RZ follow-up to the incomplete-field stability failure

The C45/R62 source has a simulated fast-corner conditional phase margin of
55.28121348 degrees with the 844-pair partial-capacitance network, below the
unchanged 60-degree requirement. Its previous bare-source phase margin of
60.42146255 degrees does not establish robustness to that network.

The initial bounded screen changes only `XOTA/XRZ` length from 62 to 80 or
100 micrometres. Width remains 1 micrometre; the main MIM remains 45 by
23 micrometres. All other source devices, model cards, instance identities,
external ports, and stimulus/loading definitions remain unchanged.

`prepare_comp45_rz_remedy.py` checks exact reversal to source
`b8912a862b61554266239634dd388ed0ffad229c0b0e48819ad129d589352e97`,
159 primitive identities, 134 source nets, projected private-node aliases,
and precisely one declared resistor geometry change. Five negative/positive
preparation controls are in `test_comp45_rz_remedy.py`.

The initial screen intentionally borrows all 844 source-net-pair capacitors
from the completed R62 native extraction, byte for byte. This is a diagnostic
design sensitivity, **not candidate-specific PEX**. The 134 unbound substrate
pairs remain explicitly omitted; omission is neither zero physical coupling
nor a bound. Complete MIM extrinsic fields, model/reference-plane composition,
wire resistance, and final full-chip/fill context remain unresolved. No whole
MIM-pair subtraction or fabricated capacitance is permitted.

Each candidate receives an own-source differential baseline, followed by the
established voltage/current Tian pair. Exact old-source operating-point
equality is recorded separately and is not acceptance for an intentionally
changed resistor. Within-source probe controls remain 1 microvolt and
1 nanoampere. Every leaf requires finite spectra, exact tool/model/source
bindings, all 11,512 model observations before/after, 11,511 unchanged
observations versus the reference, the native C45 mismatch-area relation,
and the legacy 27 observations. The two probe operating points and model
inventories must match each other exactly.

Electrical screen limits remain gain 19.9–20.1 V/V, bandwidth at least 2 MHz,
phase margin at least 60 degrees, and gain margin at least 10 dB. Each simulator
leaf has a 120-second bound; the wrapper has a 150-second bound. Resource
availability is freshly measured before each leaf. Failures are preserved;
no solver/tolerance ladder or automatic population launch is allowed.

Fast-corner screens precede nominal and slow/low-rail characterization of a
promising candidate. Native geometry, stock checks, candidate-specific fields,
own-source zero-C waveform controls, affected transient/noise and population
qualification are **not run** for these new source variants at preparation.
Prior b891 instrumentation controls establish only the earlier adapter method,
not electrical qualification of either changed circuit. Old population results
must not be transferred by matching the unchanged model observations alone.
