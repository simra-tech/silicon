# Current-steering trim: 33-point analog-control curve

This package samples the 780 uA differential current-steering experiment at
33 requested base-difference settings from -200 mV through +200 mV. It is a
27 C, typical-corner, static DC experiment. Each of the 33 retained raw files
contains 601 input-sweep rows.

An independent recount linearly interpolated the zero crossing of
`v(xcomp.c_p) - v(xcomp.c_n)` directly from every raw file:

| result | independently recounted value |
| --- | ---: |
| threshold at sampled control 0 | -40.692257 mV |
| threshold at sampled control 16 | +0.029690 mV |
| threshold at sampled control 32 | +40.707065 mV |
| authority relative to sample 16 | -40.721948 / +40.677374 mV |
| minimum adjacent threshold step | 46.412 uV |
| maximum adjacent threshold step | 7171.746 uV |
| median of 32 adjacent threshold steps | 1449.601 uV |

The 33 sampled thresholds are strictly increasing. This is evidence about a
coarsely sampled **analog base-voltage control**, not evidence that a
physically implemented DAC has no missing codes. The threshold steps vary by
about 154.5:1, so the sampled control transfer is strongly nonuniform.

The requested control spacing was 12.5 mV, but the deck formats each source to
four decimal places. The actual adjacent base-difference increments retained
in the raw files are 12.4, 12.5, or 12.6 mV. The measurements above use the
actual retained stimulus values.

The experiment's original reporting script crossed the emitter-follower nodes
while naming a collector crossing and selected one of the two middle sorted
steps rather than averaging them for the even-sized median. The former changes
these thresholds by at most 0.025 uV; the latter produced an incorrect reported
median of 1736.57 uV. That script is not used as authority in this package.

This package does not establish a realizable digital code mapping, 10-bit
resolution, mismatch, dynamic behavior, PVT coverage, yield, architecture
selection, a gate disposition, or signoff.

## Reproducing

From this directory, with `PDK_ROOT` set to the IHP SG13G2 PDK root:

```sh
ngspice -b tb_current_steering_33point.cir > log_current_steering_33point.log
```

The retained log contains 33 completed 601-row analyses and no error, fatal,
abort, or NaN message. The published deck differs from the executed deck only
by replacing machine-specific model, include, and output paths with
`$PDK_ROOT` and repository-relative paths.
