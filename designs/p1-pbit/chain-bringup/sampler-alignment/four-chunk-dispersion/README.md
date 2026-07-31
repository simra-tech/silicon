# Four-chunk sampler-correlation dispersion

This package compares the observed spread across the four retained noise seeds
at every measured sampler phase. It derives only from the published
[typical-corner](../typical-four-chunk/README.md) and
[cold-corner](../cold-four-chunk/README.md) campaigns; no new simulation was
run.

[`sampler_phase_four_chunk_dispersion_v1.tsv`](sampler_phase_four_chunk_dispersion_v1.tsv)
has 40 data rows: 20 phases from 0 through 190 ps at each of 27 °C and
-40 °C. Each row binds the four complete raw-file SHA-256 values and retains
the four chunk correlations, their mean, the mean bit probability, and two
uncertainty descriptions:

- the campaign's theoretical `1/sqrt(880) = 0.033709993123`;
- the sample standard deviation of the four chunk correlations, using
  denominator three, and its standard-error estimate for the four-chunk mean,
  `sample_sd/sqrt(4)`.

The four-chunk mean standard-error estimate ranges from
`0.014835448863` to `0.060285563118`. It is larger than the theoretical value
at 35 of the 40 phase/corner points. The largest ratio is approximately
1.788 at 27 °C and 110 ps.

This is a dispersion diagnostic, not a confidence bound. Four chunks are too
few to certify the absence of correlation, define a sampler window, or set an
alignment budget. The table contains no pass/fail classification. The source
native logs retain their previously published thermal-model warnings, so
engineering status remains unknown and no specification is evaluated.

The TSV is 16,394 bytes with SHA-256
`01c975a28f5a35b97effce630ee6016528ac6d229267f53b9b1de586a47b4c89`.
All eight raw digests were recomputed from the published campaign artifacts,
all 40 correlation rows match the independently recounted campaign tables,
and the derived mean, sample deviation, and standard-error values reproduce
within the 12-decimal serialization tolerance.
