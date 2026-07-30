# Candidate-2 comparator offset mismatch campaign

This package preserves a 200-point HBT-mismatch campaign for the published
candidate-2 `P1_COMPARATOR`. It contains the executed decks, native logs,
selected and retry raw files, an import- and CLI-inert deck generator, separate
point and attempt manifests, and a raw-data recount script.

This is warned native simulation evidence, not signoff evidence. Engineering
status is unknown. No comparator-offset or trim specification was evaluated.

## Frozen configuration

- Comparator body SHA-256:
  `17abf08251f7cb0cb284b4e770a1c1012d1a41359e34e31b3ffbfbf56b41fb08`
- PDK/model sections: `hbt_typ_mismatch`, `res_typ`, `cap_typ`, `mos_tt`,
  and `dio_tt`
- Variation scope: ten `npn13G2` calls with `mm_ok=1`; resistor and MOS
  mismatch are disabled
- Seeds: 2001 through 2200 inclusive
- Temperature: 27 °C
- Supplies: `VCC_HBT = 2.500 V`, `VDD = 1.200 V`
- Common-mode input: `1.440 V`
- Frozen track clock: `CLK_P = 1.200 V`, `CLK_N = 0 V`
- Equal analog trim: `TRIM_P = TRIM_N = 0.800 V`
- Sweep: differential input from -60 mV through +60 mV in 0.1 mV steps
- Offset scalar: the linearly interpolated input where
  `v(xcomp.c_p) - v(xcomp.c_n) = 0`

Every complete raw has 1,201 rows and six `wrdata` columns. The first, third,
and fifth columns are repeated scale vectors; the retained signals are
differential input, differential collector voltage, and HBT-supply current.

## Point and attempt accounting

The frozen population is 200 points:

- 199 points are complete, each with a finite, strictly monotonic raw and
  exactly one collector crossing.
- Seed 2145 is unknown. Its retained second attempt exits 1 after dynamic-gmin,
  true-gmin, source-stepping, and transient-operating-point recovery fail at
  the initial -60 mV point. It has no raw.

[`comp_mc_campaign_n200_points_v4.tsv`](comp_mc_campaign_n200_points_v4.tsv)
contains one disposition per seed. The point manifest selects the first
complete seed-2001 attempt and retains seed 2145 as unknown.

[`comp_mc_campaign_n200_attempts_v4.tsv`](comp_mc_campaign_n200_attempts_v4.tsv)
contains 202 launch records. Seed 2001 has two retained same-seed attempts;
their raws are byte-identical, while their logs differ in warning/progress
interleaving. Seed 2145 was inadvertently run twice after the first
fail-closed stop. Attempt 1 was overwritten and is explicitly unavailable;
attempt 2 is the retained native failure. The self-heating-off control is a
different model experiment and is not counted as a campaign retry.

## Conditional measurement

Run:

```sh
python3 analyze_offsets.py
```

The script revalidates all selected raws and writes
[`offset-summary.csv`](offset-summary.csv). Conditional on the 199 complete
points:

- mean `VOS = -0.326264281 mV`
- sample standard deviation `7.586947467 mV`
- standard error of the conditional mean `0.537824446 mV`
- median `-0.154999440 mV`
- empirical 2.5th/97.5th percentiles
  `-15.527562240 mV / +12.755751308 mV`
- observed minimum/maximum
  `-22.435466072 mV / +19.543175074 mV`

These are conditional statistics over the complete points. The unknown sample
remains in the 200-point denominator and may be informative; it is not silently
discarded to improve a yield or specification result. The sample standard
deviation is not a trim-coverage claim, and no normality or silicon-yield claim
is made.

## Retained diagnostics

All 200 retained physical-model logs contain one thermal-limiter NaN event.
Among the 199 complete points, 85 logs contain resistor `vmax` warnings, with
1,756 warning lines in total and a per-seed range of 0 through 91.

Of the complete points, 198 finish dynamic-gmin stepping. Seed 2051 records a
dynamic-gmin failure followed by successful true-gmin stepping and still
produces a structurally valid raw. Seed 2145 records 208 resistor `vmax`
warnings before every solver-recovery path fails.

The separate `selft0` seed-2001 control disables self-heating on the same ten
HBT calls. It clears both the thermal warning and dynamic-gmin recovery, but
changes the interpolated offset from `-5.354270990 mV` to
`-6.738081366 mV`, a `-1.383810376 mV` shift. Because silicon self-heats, this
control is causal diagnostic evidence, not a replacement measurement.

## Provenance and replay

`SOURCE-HASHES.sha256` records all frozen workstation artifact hashes before
publication sanitization. Published decks and the generator replace the
workstation PDK root with `$PDK_ROOT` and raw-output paths with local paths, so
their published hashes differ. Native logs, raws, and V4 manifests are
byte-identical to their source copies.

Earlier reducers produced three rejected manifests:

- V1 SHA-256
  `3a377f2647fbbf2685d02b6025b5c24059bc7a28860afce52c1102f66c93f5a1`
- V2 SHA-256
  `16c24bee3fb145d8c4a0811e6427b5664eb8a2d6d368bf76d8bb0f42d8ef0614`
- V3 SHA-256
  `317b5d7c14787690ee4723b4e226ee34035fe872745d45ec16e7c8cb9f1fc047`

They are not included as evidence because they collapse or fabricate attempt
lifecycle fields. V4 supersedes them without erasing the correction record.

To reproduce one point, install a compatible IHP SG13G2 PDK, set `PDK_ROOT`,
and run from this directory, for example:

```sh
ngspice -b tb_comp_mc_seed2002.cir > log_comp_mc_seed2002.replay.log 2>&1
```

The decks use native PDK includes, OSDI loading, and `.control`/`wrdata`
commands. They are outside the self-contained shared OpenADA
`circuit.simulate` profile. Process completion, raw validity, measurement, and
specification satisfaction remain separate claims.

Signoff is not claimed.
