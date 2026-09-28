# Full-chip waveforms, r4 candidate, characterisation phase 2 (`r4c`)

Every waveform and every number in these figures is **simulated** (ngspice-46 with the Icarus d_cosim, IHP SG13G2 open PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`). No run was repeated to draw them. The PNGs come from the waveforms and logs of the runs recorded in [`../../FULLCHIP_CDL_R4_PHASE2_20260927.md`](../../FULLCHIP_CDL_R4_PHASE2_20260927.md).

## Generator

The generator is `sim/campaigns/plot_fullchip_waves.py` (SHA-256 `6843322f39424d1349f3cf00a57229bb52d804e125f1bea1fe095c3f1d68e0d1`), run with matplotlib 3.3.4 (Agg). Command, from the repository root:

```
python3 designs/g1-guardian/blocks/g1_top/sim/campaigns/plot_fullchip_waves.py \
  --glob 'cdl_*_r4c*' \
  --record designs/g1-guardian/blocks/g1_top/sim/FULLCHIP_CDL_R4_PHASE2_20260927.md \
  --out designs/g1-guardian/blocks/g1_top/sim/figures/fullchip_r4c
```

Inputs:
- the waveforms `sim/results/waves/<tag>.txt` (gitignored; 20 ns `linearize` grid);
- the logs `sim/logs/<tag>.log`, drawn before the logs moved to the retention store (record, "Retention and figures").

Only runs whose log says `# run status completed` are drawn, 41 in all. 39 were drawn at 04:45 CEST. The two hard_pulse `--tstop 20` runs completed at 05:28; they were drawn afterwards with the same generator, `--glob` set to each tag, and merged into `index.json`. The runs that did not complete are listed in `index.json` under `skipped`, with their log status, and in the record's run table.

## Reading the status field

`index.json` takes each figure's status from the record's run table. The six tt −40 °C and tt 125 °C figures (two and four) show "not in record". The plotter's matcher only accepts ss/ff corner labels in a record row, so it cannot match a tt row at a temperature other than 27 °C. Their status in the record is **passed**; see group C.

For the DAC-rewrite figures (`dac_rw180`, `dac_rw190`), the load event marked in the figure is the 0.90 × step at 16 µs. The step to 1.03 × is at 25.5 µs. In `dac_rw180`, the short `cmp_hard` pulse at 20.9–21.1 µs is the single hard decision at code 180 described in the record, finding 4.
