# R0.95 physical-CPEX selected PVT trim screen

All 80 simulated cases passed the saved-artifact audit: five selected PVT
tuples, each with all 16 trim codes. Every curve decreases strictly and
brackets 10 MHz. This is not full Cartesian PVT or full-chip qualification.

| MOS / R / C corner | Supply | Temperature | Simulated frequency span | Nearest-code error |
| --- | --- | --- | --- | --- |
| tt / typ / typ | 1.20 V | 27 °C | 7.530659–13.548485 MHz | −0.983% |
| ss / wcs / wcs | 1.08 V | −40 °C | 5.892707–10.548691 MHz | +0.382% |
| ss / wcs / wcs | 1.08 V | 125 °C | 5.834326–10.447513 MHz | −0.572% |
| ff / bcs / bcs | 1.32 V | −40 °C | 9.768411–17.598817 MHz | +0.263% |
| ff / bcs / bcs | 1.32 V | 125 °C | 9.612261–17.254386 MHz | −1.345% |

The unchanged protocol uses a 6 µs transient, one solver thread, an original
300 s watchdog per case, mismatch disabled, and a 50 fF stand-in output load.
Four independent shards cover exactly 20 cases each. All 80 deck bytes match
the previous PVT protocol; only the included physical CPEX contents changed.
The source contains four 55.575 µm resistor segments, without a second 0.95
resistance scaling. Prior-source results were not transferred to this source.

| Check | Status |
| --- | --- |
| Exact source, deck, model and runtime bindings | passed |
| All 80 finite full-length waveforms and clean numerical logs | passed |
| Five all-code monotonic curves and 10 MHz coverage | passed |
| Source/protocol controls (9), saved-artifact corruption controls (4) | passed |
| Earlier failed checks in other campaigns | failed; retained, not reclassified by this screen |
| Full Cartesian PVT, actual receiver/clock-tree load, physical jitter | not run |
| Hardware measurement | not applicable to this simulation screen |

## Built against

| Component | Identity and establishment |
| --- | --- |
| Public IHP SG13G2 PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; runtime COMMIT and model-file hashes |
| ngspice | 46; executed version output retained in each shard manifest |
| Image config | `ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`; container identity check |
| Image amd64 manifest | `5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0` |
| KLayout / KPEX | 0.30.9 / 0.3.12 for the separately qualified source extraction |
| xschem / LibreLane / CACE | not applicable to this screen |

Physical CPEX SHA256:
`8efd7a09faf173da8604a219f73fd3ea5ec2508618d8361a050770c099d8b1c5`.
The unchanged saved audit is
[`osc_r095_newpex_pvt80_exact_audit_20260924_r1.json`](../../sim/qualification/osc_r095_newpex_pvt80_exact_audit_20260924_r1.json),
SHA256 `4aff34e13a79e6204725dc6c9dec2a8098d57cdefa030c493bd8947dbd82695f`.
It binds all four original manifests and every deck/waveform, and includes
per-case values and acceptance results. Bulk waveforms are retained separately,
not duplicated in Git. The audit ran as one unpinned host process, not a solver.

## Exact commands and reproduction

From `blocks/g1_osc/sim/qualification` in the pinned runtime, the executed
scientific command for each `SHARD` in `0 1 2 3` was:

```sh
python3 run_trim_newpex_pvt.py \
  --run-id "osc_r095_newpex_pvt80_20260924_r1_shard${SHARD}" \
  --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0 \
  --pex-source "${PEX_SOURCE}" \
  --pex-sha256 8efd7a09faf173da8604a219f73fd3ea5ec2508618d8361a050770c099d8b1c5 \
  --shard-index "${SHARD}"
```

`PEX_SOURCE` must identify the hash-matched physical CPEX. The host launcher
used `flow/run.sh`, four disjoint one-CPU affinities, 4 GiB memory reservations
per shard, and external bulk results storage after a fresh resource check.
Run IDs are exclusive: these commands reject existing output, not overwrite it.

The saved-only audit command was:

```sh
python3 audit_trim_newpex_pvt.py \
  --output osc_r095_newpex_pvt80_exact_audit_20260924_r1.json
```

For an independent saved-data recheck, select a new audit output filename;
retain the hash-matched shard directories and qualified nine-case source
manifest/analysis required by the auditor. No waveform or model change is
permitted by this report. Source GDS and full-chip physical checks are recorded
separately in `../r095_fullchip_physical_20260924`.
