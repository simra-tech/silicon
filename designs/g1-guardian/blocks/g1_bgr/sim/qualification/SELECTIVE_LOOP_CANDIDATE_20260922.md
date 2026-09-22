# Selective PTAT-loop replication hypothesis

The baseline simulated mismatch campaign has 54/100 TC failures. Replicating
the full core four times retains 23/100 failures with quarter-length resistors
and 19/100 with parallel full-length resistors. Neither is an accepted remedy.
Full-core 16-unit replication was rejected as implausible in the local footprint.

The new, unadopted candidate confines replication to the PTAT and bias loops.
It keeps the startup, detector, VREF output and IPTAT output branches unchanged.
The exact 13 MOS, 12 HBT and 15 resistor mapping is in the generator and candidate
manifest. Sixteen physical copies add 600 original-geometry units; legal Nx=1
HBT units are copied separately. No model card or arbitrary mismatch scaling is
changed. The intent is to preserve current density and nominal bias while
averaging loop mismatch. Physical footprint and spatial correlation are unknown;
the smaller instance count is not evidence of fit or yield.

Prepare once from the repository root:

```sh
python3 designs/g1-guardian/blocks/g1_bgr/sim/qualification/prepare_selective_loop_candidate.py --units 16
```

After a fresh resource gate, run a bounded nominal mechanism check:

```sh
G1_CPUSET=6 G1_CPUS=1 G1_MEMORY=4g G1_WORKDIR=designs/g1-guardian/blocks/g1_bgr/sim/qualification flow/run.sh python3 run_campaign.py --run-id bgr_selective_loop16_nominal_20260922_r1 --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0 --suite nominal --pex-source candidates/bgr_selective_loop16/bgr_selective_loop16.spice --all-fingerprints
```

The DC leaf has a 120 s watchdog and a 0.25 GiB output reservation. At preparation,
nominal simulation, HBT current-density check, all-parameter mismatch qualification,
layout feasibility, DRC/LVS/new PEX, stability and remaining campaign gates are
**not run**. Baseline extracted wire capacitances are retained; new geometry
parasitics are not represented. Startup HV NMOS terminal concerns remain separate.

## Nominal mechanism result

`bgr_selective_loop16_nominal_20260922_r1` completes in7.626s with simulated
TC22.5563ppm/°C and VREF25=1.039342729V. The direct25°C unit-current comparison
`bgr_selective_loop16_density_20260922_r1` completes both baseline/candidate OPs;
all193 active HBT units differ from their original unit collector current by at
most7.98×10⁻⁹ relative. Across the nominal temperature sweep, maximum VREF
difference is0.256µV and IPTAT difference2.86pA. This supports the nominal
current-density-preservation hypothesis, not mismatch yield or physical fit.

Supply current at25°C increases from21.893µA to206.693µA (approximately0.682mW
at3.3V); maximum current over the nominal sweep is274.656µA. Power and routing
must be included in adoption review. `selective_loop16_nominal_analysis_20260922_r1.json`
contains all individual HBT comparisons and waveform hashes. All-parameter
mismatch qualification, sample expansion, startup, stability and physical gates
remain **not run** for this candidate.

## Completed candidate100 and startup diagnostics

The exact1877-parameter six-case harness qualification passes, including repeated
waveform bytes, reverse-temperature parameter identity, disabled-seed invariance
and enabled variation in all modeled device classes. The initial20 independent
samples pass TC, but the prespecified80-sample extension exposes **7/100 TC
failures**, maximum68.759198ppm/°C. All100 numerical sweeps complete with frozen
parameters and distinct complete sample fingerprints. This candidate improves
the observed failure count but does not close the TC target and remains unadopted.
`selective_loop16_mc100_audit_20260922_r1.json` rehashes sources and reproduces
TC from all3400 saved temperature points; original baseline54/100 failures remain.

Descriptive100-sample correlations with signed endpoint slope are−0.859 for
mean Q1 area,+0.882 for the Q2/Q1 log-area ratio and−0.486 for the unscaled
reference HBT area. They motivate the separately documented fixed-draw diagnostic
plan but are not causal proof or a new fitted correction.

`bgr_selective_loop16_startup6_20260922_r1` completes all six original3.0V,
1ms/100ms supply ramps. Numerical completion, final VREF0.9–1.2V and IPTAT>1µA,
and sampled external HBT VCE≤1.6V pass. Maximum saved supply current is314.949µA
at the fast/hot tuple. Short HV NMOS XM31 reaches2.9733V VGS and XM33 approximately
3.0V. These3.0V startup fixtures do not clear the original3.3/3.6V reliability
concerns. Added terminal-vector data and all original-deck hashes are retained.
Physical fit, via/current margin, new extraction and global stability remain
**not run** for this simulation-only candidate.
