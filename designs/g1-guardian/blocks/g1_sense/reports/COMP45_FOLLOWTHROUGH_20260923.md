# C45/R62 loaded noise and settling

Source `b8912a862b61554266239634dd388ed0ffad229c0b0e48819ad129d589352e97`
changes only main XCC width 69→45 µm and main XRZ length 6.2→62 µm.
These are simulated, source-held nominal actual-BGR586/full-TRIP loaded
diagnostics, not post-layout qualification or population transfer.

The five analog leaves completed with the pinned runtime, candidate source,
full 11512 before/after parameters and 27 legacy observations. The changed
native capacitor mismatch scaling is explicitly checked; 11511 other
fingerprints remain exact. Both step initial nine OP and seven observation
values are exact against their own candidate noise anchor.

| Diagnostic | Simulated result | Disposition |
|---|---:|---|
| Input-referred noise, 1 Hz–2 MHz | 36.217661 µV RMS | finite spectrum/integration controls passed |
| Output noise, 1 Hz–10 MHz | 1.157653466 mV RMS | finite spectrum/integration controls passed |
| Rising step, final 1% entry | 207.879078 ns | characterization; no allocated timing acceptance |
| Falling step, final 1% entry | 217.668736 ns | characterization; no allocated timing acceptance |
| Rising/falling overshoot | 1.687629% / 2.457977% | independent final-DC targets |

Rise/fall gains are 19.9590006 and 19.9576034. Final targets come from
independent DC leaves, not fitted waveform endpoints. Saved-point settling
is not a continuous-time bound.

The first noise analyzer failed its exact final-frequency comparison:
the saved endpoint was 9999999.999999788 Hz. That original failed summary
is retained. A separate saved-data-only recovery restores the established
relative 1e-12 endpoint check and clips integration to the saved frequency
range; no analog rerun or numerical setting changed.

Native simulator integrated totals and independently integrated spectra do
not agree exactly. The output discrepancy is −0.0011312%; the input discrepancy
is +1.704895%. Both are retained; no integrated-total equivalence is claimed.
The input stimulus is one-sided and therefore also changes common mode.
Clock is frozen at DC zero. Boxcar-window results are sensitivity diagnostics,
not an assertion that decision latency is a noise filter. Allocated noise
acceptance, cyclostationary noise, candidate population, complete extracted
fields and physical adoption are **not run**.

## Built against

| Item | Identity |
|---|---|
| IHP SG13G2 PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` |
| ngspice | 46, creation 2026-07-27, SPARSE; exact version/model-file hashes in provenance |
| OCI manifest | `5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0` |
| OCI config | `ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` |

Reproduction uses `run_comp45_followthrough.py` for the five bounded leaves,
`recover_comp45_noise.py` for the separate original-failure-preserving analysis,
and `analyze_comp45_settling.py` for independent DC/step composition. Models,
rules, circuit loading and original acceptance criteria are unchanged.
