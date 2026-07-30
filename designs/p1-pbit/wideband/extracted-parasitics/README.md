# Extracted-parasitics rerun of the correlation measurement

The artefacts behind *The extracted-parasitics rerun* in [`../README.md`](../README.md).

```
run_detached_pex_wideband_sim.py   the runner: 17 x 1 us trnoise chunks, resampled at 7 intervals
p1_noise_gen_pex.spice             the extracted noise-generator netlist the runner includes
pex_corr_progress.log              the full log, one 7-rate table appended per completed chunk
```

The log is the whole run rather than its last table on purpose: the per-chunk history is what
shows the 4 GHz excursion shrinking from −0.00529 at 28,000 bits to −0.00411 at 68,000, which is
the reason that row is reported as a fluctuation and not as a bandwidth effect. A final table
alone would not let a reader check that.

Absolute paths have been rewritten — `$PDK_ROOT` for the PDK, `.` for the working directory — so
the runner will need those pointed at a real installation before it will execute. That
substitution is the only edit; the numbers are as the run produced them.

**The netlist is pruned, and the pruning is not recorded in it.** Small parasitics were dropped
before simulation; what survives here is 10 capacitors, the smallest 0.171 fF. Without that
pruning the solver chases sub-femtofarad couplings and the run does not finish in any useful
time. With it, 17 µs completed in **69.3 minutes**, a mean of **245 s per microsecond**
(03:55:52 → 05:05:09 in the log). The other half of that is the `maxstep` cap, which *is*
visible: `tran 100p 1u 0 0.5p` at line 66 of the runner.

A reader cannot recover the discarded elements or the threshold from these files. That is a
reproducibility gap and is recorded as one rather than left to be noticed.

**No seed is set.** ngspice reseeds `trnoise` per invocation, so re-running this reproduces the
method and not the bitstream — the same caveat the parent note records for its own decks.
