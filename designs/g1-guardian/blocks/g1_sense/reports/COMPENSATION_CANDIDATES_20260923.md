# Source-isolated compensation candidates

These are simulated schematic candidates, not adopted geometry or a replacement
for the qualified-source population. Original failures are preserved.

The original gm4/comp3 source is SHA256
`baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`.
The C50 derivative is
`05c82627eca7a93d8b826dfb534a9a541eb872004414270238f7c6c247bd3017`.
It changes only the main OTA MIM width from 69 to 50 µm; length remains 23 µm.
All transistor dimensions, buffers, reference, TRIP and model cards are held.

| Simulated case | Gain V/V | Half-power bandwidth | Main conditional PM | Minimum observed GM |
|---|---:|---:|---:|---:|
| Original slow/low-rail/cold | 19.99848 | 1.56620 MHz **failed** | 71.65794° passed | 17.86231 dB passed |
| C50 slow/low-rail/cold | 19.99848 | 2.49767 MHz passed | not run | not run |
| C50 nominal | 19.95751 | 3.83543 MHz passed | 54.22507° **failed** | 11.94144 dB passed |
| C50 + main RZ 24.8 µm nominal | 19.95751 | 3.69703 MHz passed | 59.84985° **failed** | 15.47621 dB passed |
| C50 + main RZ 37.2 µm nominal | 19.95751 | 3.61250 MHz passed | 63.42303° passed | 17.69810 dB passed |
| C50 + main RZ 37.2 µm fast/high/hot | 19.98344 | 4.49697 MHz passed | 58.20287° **failed** | 15.67719 dB passed |
| C50 + main RZ 37.2 µm slow/low/cold | 19.99848 | 2.09740 MHz passed | not run | not run |
| C45 + main RZ 62 µm slow/low/cold | 19.99848 | 2.23116 MHz passed | 75.53617° passed | 19.68180 dB passed |
| C45 + main RZ 62 µm nominal | 19.95751 | 4.02613 MHz passed | 66.20580° passed | 18.24475 dB passed |
| C45 + main RZ 62 µm fast/high/hot | 19.98344 | 5.02489 MHz passed | 60.42146° passed | 16.67774 dB passed |

Criteria remain gain 19.9–20.1, bandwidth ≥2 MHz, conditional main-loop phase
margin ≥60° and gain margin ≥10 dB. Other loops remain closed during the
established two-injection measurement; this is not global stability proof.
The C50 candidate is not acceptable: improving bandwidth did not preserve the
required nominal phase margin. Fast-corner expansion of this failed candidate
was not run.

Both C50 differential fixtures preserve the corresponding original
same-topology nine quiet OP values and total fixture DC rail currents exactly.
The paired nominal loop fixtures preserve each other's OP and full parameter
vector exactly; versus the differential fixture, maximum observed voltage
change was 14.276 nV and rail-current change 0.457 pA, inside the existing
1 µV/1 nA probe-equivalence gate. Exact differential-versus-probe equality
failed and is not relabelled passed.

The unchanged native MIM mismatch law changes its area-dependent scale. The
other 11,511 recorded fingerprints and legacy 27 remain exact; each candidate's
11,512-vector is exact before/after analysis. This is source/realization
accounting, **not** transfer of transient, calibration or mismatch acceptance.
The nominal differential first failed a decimal-only model-law audit despite
completed simulation. Its original receipt is retained. A separate saved-data
reanalysis uses outward-rounded binary64 native-operation intervals, tested
against both signs, wrong draws and the original counterexample. No simulator,
solver setting, tolerance or raw output changed in that recovery.

## Next isolated design test

A separately generated derivative retains C50 and increases only the main
compensation resistor length from 6.2 to 24.8 µm, retaining width 1 µm, native
`rppd`, bulk connection and mismatch identity. The buffer resistor instances
are unchanged. This moves the compensation zero to test increased phase lead;
it is a design hypothesis, not a fitted model parameter. The pinned native
model computes resistance, head capacitance and mismatch from the new source
dimensions. The body-area increase is 18.6 µm² versus a MIM plate reduction of
437 µm²; this arithmetic is not a legal-placement or extracted-field result.
The derivative source is
`5f878809fbd4454600ff0b444eb84aa891cf0cb92f8ecde28d3c800d1bf3b0d7`.
Its nominal differential simulation completed, but the prospective exact
cross-source DC gate **failed**: the maximum nine-value OP change was
35.834 pV, ISENSE changed 14.810 pV, and total VDDA current changed 56.39 fA.
These differences are retained, not rounded to zero. A separately declared
bounded cross-source 1 µV/1 nA diagnostic passed, with signed-bound, nonfinite
and wrong-name rejection tests. That saved-data analysis did not override the
failed exact comparison or rerun the simulator. Paired Tian probes compare
against this derivative's own OP under the unchanged probe controls. They
passed source, parameter and DC-equivalence checks, but the measured phase
margin is 59.84985°: **failed**, without rounding to the 60° threshold.
Exact inverse-source and main-only controls pass.

The next isolated hypothesis increases that same main RZ length to 37.2 µm,
retaining C50 and everything else. Its resistor body adds 31 µm² versus the
original, before any placement/routing assessment. It prospectively applies
the separately declared cross-source DC diagnostic and records exact equality
as a distinct status. Its exact source is
`edde372083bbe7ac10da42d30d694d7a636f184bb1716e543115b40236a097d4`.
Nominal gain, bandwidth, conditional phase and gain margins pass the original
criteria (table above). The two probe OP/parameter vectors are mutually exact;
probe-to-own-baseline equivalence passes. Original cross-source exact DC still
fails (maximum quiet change 16.278 pV; total VDDA change 58.880 fA), separately
passing the bounded diagnostic. Adverse qualification remains pending and no
population or geometry adoption is implied by this nominal result.

For the same derivative at fast/high-rail/hot, the saved finite differential
AC gives gain 19.98344456 V/V and bandwidth 4.496969 MHz. Both exact and bounded
cross-source OP comparisons **failed**: ICMP differs by 5.189383 µV, the hard
threshold by 4.657261 µV, and total core-VDD current by 421.122 µA (original
approximately −654.232 µA versus candidate −233.110 µA). Total VDDA differs
by 0.323813 nA. This is not characterized as merely voltage print rounding;
the cause of the large core-current difference is not established.

A separate saved-data baseline verifies only the candidate's own finite OP,
source inverse, runtime, full native parameter accounting and finite AC. It
does not assert equivalence to the original source. Paired probes must still
meet the original 1 µV/1 nA limits against that own-source baseline; any such
within-source failure blocks return-ratio qualification. The own-source probe
controls passed, but the resulting phase margin is 58.20287°: **failed**. This
derivative is not acceptable despite its nominal pass. A slow-corner prelaunch
resource gate failed; no analog child started for that attempt. A later fresh
gate admitted the unchanged required slow differential characterization.

Saved-evidence diagnosis found that the original source's failed fast voltage
probe already had the lower core current (−233.109746673 µA), agreeing with
the candidate differential value within 0.807 fA. Thus the lower-current
solution is not unique to changed compensation. The original transient t=0
row matches the original nine OP values exactly and has soft output
0.676473911 V on a 1.32 V rail, a midrail value. A different comparator DC
solution is a supported hypothesis, not an identified new latch state: the
candidate/probe comparator-state vectors were not exported. No new simulation
was performed for this comparison and no current-budget relief is claimed.

The later slow differential completed: bandwidth 2.09740 MHz, only 97 kHz
above the requirement. Thus the proposed C50/R62 variant was **not run**:
further resistance alone could exhaust that margin (an inference, not a
simulated failure). The next bounded hypothesis instead combines main MIM
width 45 µm, length 23 µm, with main RZ length 62 µm, leaving the same MOS,
bias, buffers and interfaces unchanged. Plate area is 1035 µm² (−552 versus
original), resistor body adds 55.8 µm². The native mismatch area-law proof
uses 69/45 and is tested independently for both signs and wrong draws; no
card parameter is fitted. Exact source is
`b8912a862b61554266239634dd388ed0ffad229c0b0e48819ad129d589352e97`.
Slow differential passed gain 19.99847887 and bandwidth 2.231156 MHz; its
separate bounded cross-source comparison passed, while exact OP equality
failed. Nominal paired probes passed their own-source controls, phase margin
66.20580° and gain margin 18.24475 dB. Fast differential bandwidth is
5.02489 MHz, but both old-source DC comparisons failed again (approximately
421.122 µA core-current difference). Its separate saved-data own-source
baseline passed; this is not old-source equivalence. The slow paired loop
passed phase margin 75.53617° and minimum gain margin 19.68180 dB. Fast paired
loop analysis passed phase margin 60.42146° and minimum gain margin 16.67774 dB.
Thus these three selected source-held schematic screens pass, with only
0.42146° fast phase-margin headroom. This is not all-PVT/global-loop stability,
population acceptance or source adoption. Native placement and all affected
physical checks remain not run.

Read-only placement review finds that the original vertical RZ placement
cannot simply grow to 62 µm inside the existing main-OTA boundary. A rotated
native resistor could fit the unused device-bounding-box region to its right,
but this is not a route, tap-clearance or stock-check proof. Updated native
placement, source correspondence and all affected field checks are required;
the smaller total primitive area alone does not prove legal fit.

## Requalification boundary

Any adopted compensation change requires new affected-source dynamic,
settling, AC/stability, PSRR/CMRR, noise, calibration/decision, PVT and mismatch
evidence. The original source-bound population stays valid only for the
original source; it cannot silently be renamed or counted for the derivative.
DC-only reuse would need an explicit source-bound invariance proof for each
fixture and cannot justify dynamic reuse. Updated native MIM/resistor geometry,
source correspondence, unchanged-rule DRC/LVS, affected field/current checks
and the unresolved complete-PEX/model-attachment boundaries remain separate.
No population restart, canonical source substitution or full-chip adoption
has been performed.

## Built against

| Item | Pinned identity / establishment |
|---|---|
| PDK | IHP Open PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; each leaf compares every installed model-file hash with its reference fixture |
| ngspice | 46, creation 2026-07-27; exact version text and SPARSE solver held |
| OCI config | `ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`; verified by flow |
| OCI manifest | `5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`; reference provenance |
| Layout tools | not run for these source candidates |

The one-leaf runner, independent analyzer and negative controls are in
`../sim/run_loaded_compensation_candidate.py`,
`../sim/analyze_loaded_compensation_candidate.py` and
`../sim/test_loaded_compensation_candidate.py`.
Runtime bounds remain 120 seconds per analog child. Retained model warnings
and failed receipts must accompany any later portable evidence export.
