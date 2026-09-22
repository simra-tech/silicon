# IO buffer convergence reduction — candidate remains unadopted

The nominal isolated HV receiver/driver completes tight DC and 8µs transient checks with the 5nF/10Ω/10kΩ load. Adding the unchanged protected analog pad fails numerically. No card, rule deck, delivered circuit or layout was changed.

The runtime is the pinned IHP revision84374023ee8b4b126bebbba67fcbada0a9c0ff0b. Campaign manifests identify image, simulator, model and generated-deck hashes. Legacyngspice46 and nativeARMngspice47 are separate runtimes; these diagnostics do not establish global equivalence.

| Diagnostic | Evidence under `sim/campaigns/` | Result |
|---|---|---|
| Direct schematic driver, nominal27°C, tight tolerances | `isolated_20260921T220422Z_b39f0d59/direct*` | Passed scopedDC/high/low/turnoff checks; gatehigh3.27759V, fall below1V517.25ns after inputfall, input half-output threshold0.725V |
| Same driver plus protected analogpad | Same campaign `analog_pad*` | Timeout120s at1.06714µs; DC completed, transient incomplete |
| Native47 direct / analogpad | `isolated_20260921T220707Z_8bff6863` | Direct passed; analogpad fatal at1.06714µs, reported upper-secondary `dpperim` |
| Trap / Gear100ps | `isolated_20260921T220740Z_ae2861ef` / `...22d4c98a` | Both timeout60s |
| Bypass disabled | `isolated_20260921T220954Z_9cb3a6b6` | Timeout60s |
| Ideal supply / extra10Ωdriver resistor | `isolated_20260921T221122Z_bbceef58` / `...930e6177` | Both timeout60s |
| KLU | `isolated_20260921T221310Z_eb58c435` | Timeout60s |
| Ideal100ns ramp, upperdiode / secondary / analogpad | `diode_20260921T221046Z_9b690af6` | All three numerical endpoints complete; no driver acceptance |
| Recorded direct-driver voltage replay through50Ω | `diode_20260921T221311Z_1eba6f59` | Upperdiode completes8µs; secondary and analogpad fail~1.072063µs |
| Same replay, lower `dantenna` alone | `diode_20260921T221633Z_70c51525` | Fails1.071792µs without MOS, modeled resistor or fullpad |

The lower-diode reduction is important: the fatal message can name the upper diode or supply source, while the final device dump in `diode_20260921T221446Z_0e9baac6/secondary.log` places the lower `darea` intrinsic bias at−0.0782931V. The ngspice current-equation branch boundary at27°C is−3n·kT/q=−0.0782931038V.

`analyze_diode_branch.py` reads unchanged PDK parameters and evaluates the checked-in ngspice46/47 branch equations at nominal temperature. `campaigns/diode_branch_20260921_r3.json` records inputs and source hashes. For this geometry the level1 algorithm produces effective breakdown−22.9486V, and the two current branches differ by approximately37.06pA at that boundary. This is a simulator-equation diagnosis consistent with the observed failure, not a qualified physical correction or proof that every historical failure shares this cause. PWL shape, circuit loading and solver choices affect whether a run steps through the discontinuity.

The [ngspice diode equations](https://ngspice.sourceforge.io/docs/ngspice-46-manual.pdf) describe reverse/breakdown region matching. The upstream [IHP issue921](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/921) reports related IO-cell convergence trouble; a [maintainer diagnostic](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/921#issuecomment-4432344570) simplifies antenna models and relaxes solver settings. Those modifications have **not** been applied here. Updating to the testedngspice47 alone does not remove this reproducer.

Reproduce the smallest saved-waveform failure:

```sh
G1_EDA_IMAGE=g1-sim-arm64:20260921 G1_EDA_PLATFORM=linux/arm64 G1_CPUS=1 G1_MEMORY=2g \
 flow/run.sh env PATH=/opt/ngspice-47/bin:/opt/iverilog/bin:/usr/local/bin:/usr/bin:/bin \
 python3 designs/g1-guardian/blocks/g1_gate/sim/candidates/io_buffer/run_diode_reproducer.py \
 --image-id sha256:ab853b72c0b95f467d562afc77b09cfb7093a87910e26bf671ad46566dadd82e \
 --replay designs/g1-guardian/blocks/g1_gate/sim/campaigns/isolated_20260921T220422Z_b39f0d59/direct_tran.tsv \
 --cases dantenna
```

The protectedpad adds approximately587Ω to the externalgate path. It is not characterized as a30mAoutputpad. Candidate physical implementation, EM/ESD, fullPVT/mismatch, real-FET arming and turnoff remain **not run to qualification**. The original unsafe IO-first GATE condition remains a design failure. Bulk repetitions of this failed candidate are deferred until a justified new remedy exists.

The initial equation analysis assumed NR=1 and modern physical constants; r2 corrected the verified defaultNR=2, and r3 reads ngspice’s own `const.h`. These corrections change the tiny recombination term and nanovolt-scale branch value, while the rounded37.06pA jump remains. Both earlier analyses are retained as superseded diagnostics.

A separately declared current-tolerance diagnostic kept reltol1e−5/vntol100nV and all cards/capacitances unchanged, changing only abstol10fA→100pA. Native47 `isolated_20260921T223302Z_5576af1b` still timed out60s at1.06714µs. The planned200pA/step-comparison continuation is **not run** because the first endpoint did not complete. This attempt does not qualify an alternative numerical setting or close the failure. Contract: `campaigns/io_buffer_current_tolerance_contract_20260921.json`.
