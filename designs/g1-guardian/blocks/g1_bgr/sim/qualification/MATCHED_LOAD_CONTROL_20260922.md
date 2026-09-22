# Matched nominal reference-load control

Prospective: **not run**. Compare baseline source72417e07 and coordinated
HV-length derivative586ffb58 using the exact retained `bgr_stress3_20260921_01`
load deck, byte for byte. Both runs use identical initialization, pinned models,
27 C, 3.3 V, VREF1 pF, IPTAT held at1 V, and a100 nA VREF load applied
5.00–5.01 us and removed20.00–20.01 us. End40 us, original2 ns step and
tolerances. Only source content changes between these two controls.

Run sequentially on one CPU with300-second watchdog each. Stop at the first
numerical or diagnostic-return failure; no retry or tolerance ladder. Fresh
resource check reserves0.25 GiB HOME growth and retains8 GiB free. Approximately
7 seconds for the historical baseline and30–90 seconds for the larger candidate
are forecasts, not guarantees. No population is drawn (mismatch disabled).

Require finite12-column strictly increasing full40 us waveforms, time0 present,
clean solver log and endpoint level0.9<VREF<1.2 V/IPTAT>1 uA. Report sampled
extrema/current, means over4–4.9 us and19–19.9 us, and final5 us return error.
Prospective engineering diagnostic return bands are1 mV VREF and0.1% IPTAT,
relative to the pre-load mean. These are not product allocations. Report the
finite100 nA step response in V/A, not AC impedance. No same-wave baseline
parity is asserted unless archived complete waveforms can be compared.

This is not actual periodic SENSE/DAC/T2F loading. Full MOS/HBT terminal,
hot/high-rail reliability, timestep convergence, PVT/MC, new-geometry PEX and
candidate adoption remain **not run**. The exact fixture preserves original
limited saved nodes; no additional terminal-limit pass is inferred from them.
Earlier startup failures remain failed; the20 us maximum-step startup result
does not qualify timestep convergence or replace this distinct load fixture.
