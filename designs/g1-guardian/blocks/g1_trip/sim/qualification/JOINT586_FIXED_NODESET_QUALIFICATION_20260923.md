# Fast fixed-nodeset qualification

Status: **passed** the separately declared14-control consistency gate.
This is not a calibration/population pass or a physical-layout qualification.

All controls use the same eight canonical external-node guesses from the
original78001 operating-point record. Guesses are not retuned by seed,
temperature, rail, common mode, code or outcome. The original SPARSE solver,
models, sources, tolerances, clocks and1200s/4800s bounds remain unchanged.

The independent corrected-b audit verifies all11512 before/after values and
27 legacy anchors, finite complete waves and actual/legacy decisions for:

- enabled, exact repeat, changed seed, disabled, disabled changed seed and
  same-instance25→125→−40→25 temperature return;
- the output-only18/19-column actual-SHN pair;
- all six declared rail/temperature/common-mode fixtures.

Enabled-repeat and disabled-changed vectors and decoded wave bytes are exact.
All3500 randomized primitives change under the distinct enabled seed. All
four return-phase vectors, initial-room and returned-room waves are exact.
The SHN pair preserves the original18-column decoded projection exactly.
All six fixture numerical/parameter/sampling gates pass. One low-cold
fixture is reused only through its exact deck/source/runtime/receipt cache;
it was not simulated twice for this suite.

Every available waveform comparison against the original no-nodeset
fixture fails exact equality and remains a **failed exact comparison**.
No numerical tolerance silently replaces those comparisons. The original
low-cold timeout has no complete waveform to compare. Original failures
are unchanged.

The first return-a attempt failed before ngspice because its validation
helper accepted only one `wrdata` command, while the return has four. That
attempt and the original-a aggregate audit remain failed. A fresh return-b
validates each output using separate validation-only views, without changing
the actual analog deck. It completes in1124.988597 simulated-run wall seconds
with all four phases qualified. The corrected-b audit explicitly binds the
12 unchanged a-controls, exact low-cold cache and fresh return-b provenance.

[Corrected14-control audit](joint586-fast-nodeset-rescue-audit-20260923-b.json)
SHA256`394fb2748f821e2477fbe29050f80c07b18136850ce5b92119b4187abd0830d6`.
[Original failed audit](joint586-fast-nodeset-rescue-audit-20260923.json)
SHA256`330cdf0c2020402dc4750212e2f67b31bffed0683c0fd62ef3243da27a360157`.
The corrected contract is`c75fc0398debd9c7b481899ab6ba61f3490d71b16749ca5acf518e7ffae40463`.

Only the separately reviewed first calibration sample78101 is now running.
Its result, subsequent29 samples, fast crossed72 checks and population
adoption are **not run to completion** at this checkpoint. The original
binary/guard/residual criteria remain unchanged.
