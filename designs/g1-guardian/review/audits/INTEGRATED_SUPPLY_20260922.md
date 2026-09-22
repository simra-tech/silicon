# Completed integrated waveform: scoped block-supply audit

The completed nominal analog/RTL fixture supplies about **3.463 mW to the named analog blocks before the fault**, compared with 3.418 mW EN-low and 3.421 mW after tripping. These are simulated block rail powers, not whole-chip power or die heat. The omitted real oscillator, RTL switching power, actual output-pad behavior, and clock/control-source energy prevent a <10 mW whole-chip acceptance claim.

Evidence is the immutable 28 µs waveform in `blocks/g1_top/sim/campaigns/stream_20260921T220244Z_879e85e2/observations.tsv`, SHA-256 `7187ed00e90e37be56eb92f09eff1c449e52f56a8d038f75a6e18eca041623ca`. Its completed electrical acceptance record passes the coordinator's functional checks. This audit verifies the waveform hash against that record, finite values, strictly increasing times and endpoint before analyzing power. No partial raw stream is used.

The fixture is nominal 27°C, block C-PEX, ideal oscillator at the configured fixture frequency, real RTL through XSPICE, behavioral external switch, and fitted output-pad drivers. Each board rail has a 0.5 Ω series resistor and 1 nF local capacitor. It is not assembled PDN/package extraction. The zero-volt block probes have positive current into each block; V12 source current has the opposite sign and is negated for source accounting. Window means use trapezoidal integration with interpolated boundaries, not an arithmetic average of variable-timestep samples.

| Window | BGR VDDA (µA) | SENSE VDDA (µA) | TRIP VDD (µA) | TRIP VDDA (nA) | Named rail power (mW) |
|---|---:|---:|---:|---:|---:|
| EN-low, 1–2.8 µs | 22.03691 | 1013.85638 | 0.005044 | 3.032 | 3.417930 |
| Configuration active, 4–10 µs | 22.03691 | 1026.49653 | 2.757440 | 2.736 | 3.462931 |
| Gate on before fault, 14–15.9 µs | 22.03691 | 1026.49277 | 2.875402 | 3.037 | 3.463061 |
| Tripped, 20–28 µs | 22.03691 | 1013.85591 | 2.603470 | 2.941 | 3.421046 |

The gate-on interval uses the configured hard-threshold behavior; `soft_armed` remains zero throughout all these windows. It must not be described as a verified soft-armed workload. GATE core supply means are approximately 0.56 nA VDDA and 0.65–0.70 nA VDD; real output-drive power is outside those core probes. The `vm_osc` branch contains only a 1 TΩ dummy and contributes no meaningful oscillator power.

TRIP VDD sampled peaks are 1.680 mA during configuration, 1.660 mA before fault, and 1.586 mA after tripping. These are sampled values, not worst-case peak envelopes. The comparatively small average current does not justify using it alone for dynamic rail disturbance. Ideal clock and DAC/control input sources can exchange energy with TRIP independently of its supply pins; those source powers and equivalent RTL power are not included here.

## Conditional supply interpretation

The previously retained geometric mesh model estimates a TRIP VDD supply/return loop of 22.37–23.03 Ω at sampled access points. Multiplying that range by the pre-fault nominal mean 2.8754 µA gives about 64.3–66.2 µV of **own-load static contribution only**. Shared SENSE/CTRL/other-return currents, actual package, IO-return paths and dynamic decoupling are not included by this multiplication. The same instantaneous resistive calculation at the sampled 1.660 mA peak is about 37.1–38.2 mV, illustrating why the average is insufficient; it is not a simulated rail waveform. The actual integrated fixture uses 0.5 Ω/1 nF, so its ~0.173 mV sampled VDD droop does not qualify the delivered mesh.

A nominal TRIP contribution of about 3.46 µW may be added to an explicitly incomplete per-block budget that previously omitted TRIP. It is a single programmed nominal trajectory, not a PVT/activity maximum. Do not add the entire 3.463 mW sum to existing BGR/SENSE/GATE entries: that would double-count the same blocks. The earlier 5.68–5.96 mW mixed-fixture estimates remain conditional sums, not validated whole-chip power.

## Charge reconciliation and limits

After subtracting named VDDA branch charge and the local 1 nF capacitor's endpoint charge, the largest window residual is 0.000732 pC. VDD residuals reach 0.02851 pC; its unprobed pad/behavioral branches and numerical integration are not separately isolated. No new numerical tolerance is imposed to call these residuals passed. IOVDD primarily feeds unprobed modeled pads/behavioral output branches and is kept separate. The earlier real-GATE split-fixture dynamic 0.1 pC KCL failure is unchanged by this different waveform.

`integrated-supply-20260922-r2/summary.json` retains per-window currents, sampled extrema, rail powers/energies, state checks, supply voltages, charge accounting, source hashes and limitations. Initial analyzer r1 failed because installed NumPy lacks `trapz`; the API call was corrected to `trapezoid`, with failure log and snapshot preserved. No simulation, waveform, model card or acceptance record was modified.

```sh
G1_CPUS=1 flow/run.sh env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 designs/g1-guardian/review/audits/analyze_integrated_supply.py --run designs/g1-guardian/blocks/g1_top/sim/campaigns/stream_20260921T220244Z_879e85e2 --output designs/g1-guardian/review/audits/integrated-supply-new
```

Full workload/PVT power, real IO return impedance, extracted assembled IR, supply-induced threshold error and complete chip power are **not run** here.

## Later current-evidence reconciliation

`current-accounting-20260922-r1` retains a separately hashed arithmetic update using the actual clock-receiver fixture: OSC code8 mean 110.682 µA (132.819 µW at 1.2 V), while the root buffer plus 16 immediate buffers draw 29.8474 µA (35.8169 µW). The receiver current is **not added** to the CTRL STA estimate, where those cells already belong; a cell-by-cell reconciliation and actual activity analysis would be needed. Its sampled 20.517 mA peak under ideal rails is neither a worst-case bound nor compatible with substituting average current for dynamic supply analysis.

Replacing only the old code0/50 fF OSC power with this code8/actual-receiver OSC power, then adding the nominal TRIP rail contribution, changes the prior incomplete 5.681305 mW subtotal to approximately **5.68251 mW**. This remains an intentionally mixed-fixture subtotal; the trim code, load and frequency differ, so the current change cannot be attributed solely to receiver loading. No whole-chip target is passed.

The new fast/hot combined BGR+T2F+three actual level-shifters fixture reports its largest selected steady-window power 355.057 µW at 3.6/1.32 V and 125°C, with 98.4290 µA on the analog rail and 0.539808 µA on the digital rail. It already includes BGR and cannot be summed with a separate BGR entry. It is retained alongside, rather than silently mixed into the nominal subtotal. Exact source manifests/data hashes and all exclusions are in the reconciliation JSON; candidate circuits remain unadopted.
