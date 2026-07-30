# Typical-corner four-chunk sampler campaign

This package preserves the first bounded, four-seed sampler-alignment
measurement for the candidate-2 P1 p-bit chain at the typical corner. It
contains every executed deck, complete native log, and ASCII raw file, plus the
exact preamplifier dependency and the generator/parser source used for the
campaign.

This is simulation evidence, not signoff evidence. All four ngspice processes
completed, but every log retains a thermal-model warning. Engineering status
therefore remains unknown.

## Configuration

- IHP SG13G2 models: `hbt_typ`, `res_typ`, `cap_typ`, `mos_tt`
- Temperature: 27 °C
- `VCC = 2.50 V`, `VDD = 1.20 V`
- Candidate-2 shunt: `XRFB`, `rppd`, `w=1.0um`, `l=18.5um`
- Output threshold used only by the raw parser: `Vtrip = 0.593 V`
- Seeds: 42, 43, 44, and 45 for chunks 0 through 3
- Per deck: 500 PWL points from 0 through 99.8 ns at 200 ps, followed by
  22,000 points from 100 through 143.998 ns at 2 ps
- Transient command: `tran 2p 144n 100n 2p`

Each linearized raw has 22,001 rows and four variables. Every raw contains
88,004 finite numeric values and a strictly increasing time vector from 100 ns
through 144 ns at 2 ps.

## Measurement

For each phase from 0 through 190 ps in 10 ps steps, the parser selects 220
bits per chunk. Lag-one correlation is computed inside each chunk, never
across a chunk boundary, and the four correlation values are averaged. The
reported resolution is `N = 880` bit pairs per phase and
`se = 1/sqrt(880) = 0.033709993`.

The independently recounted values are in
[`phase-correlation.csv`](phase-correlation.csv). A strong correlated band is
detected from 20 through 70 ps, with mean rho peaking at `+0.581285253` at
40 ps. From 110 through 160 ps, no correlation is detected at this
resolution. That observation is not a valid/invalid classification and does
not establish a certified sampler-alignment budget.

## Execution record

| Chunk | Seed | Exit | Elapsed (s) | Resistor `vmax` lines | Thermal event | Dynamic gmin |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| 0 | 42 | 0 | 161.53 | 12 | one NaN line plus one heat-sink line | 1 start / 1 complete |
| 1 | 43 | 0 | 161.33 | 8 | one NaN line plus one heat-sink line | 1 start / 1 complete |
| 2 | 44 | 0 | 158.85 | 9 | one NaN line plus one heat-sink line | 1 start / 1 complete |
| 3 | 45 | 0 | 163.30 | 12 | one NaN line plus one heat-sink line | 1 start / 1 complete |

No log contains an error, fatal, timestep-too-small, or singular-matrix line.
An exit status of zero establishes process completion only; it does not clear
the retained warnings or establish a circuit specification.

## Files and provenance

- `tb_chunk*_27c.cir`, `log_chunk*_27c.log`, and `raw_chunk*_27c.raw` are the
  complete deck/log/raw triplets.
- `p1_noise_amp.spice` is the exact preamplifier export included by the
  executed decks.
- `sweep_4chunk_campaign.py` preserves the generator and fail-closed parser.
  Its `__main__` block emits chunk 0 only; the four executed decks are retained
  here rather than reconstructed.
- `SOURCE-HASHES.sha256` records hashes of the frozen workstation artifacts
  before publication sanitization.

Publication rewrites absolute PDK paths to `$PDK_ROOT` and workstation paths
to local paths. Consequently, the published decks, logs, generator, and
preamplifier export do not hash to the source values in
`SOURCE-HASHES.sha256`. Raw files contain no private paths and remain
byte-identical to their source hashes.

To replay a deck, install a compatible IHP SG13G2 PDK, set `PDK_ROOT` to its
root, run from this directory, and invoke ngspice directly, for example:

```sh
ngspice -b tb_chunk0_27c.cir > log_chunk0_27c.replay.log 2>&1
```

The exact open-source simulator build used for these retained raws identifies
itself in each raw header as ngspice 46. Reproduction can establish whether a
new environment agrees with this evidence; it does not turn this package into
foundry signoff.
