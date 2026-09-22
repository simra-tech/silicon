# Extracted up-shifter mismatch screen

Simulated using ngspice 46 and IHP SG13G2 commit
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, immutable EDA image
`ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`.
Source CPEX SHA256
`087bdf16283f0aad73d940ef5c5a8d577764622ab243580bb77766d35a9da293`:
eight native MOS instances and 32 extracted capacitors. Only explicit `mm_ok`
flags are appended in isolated simulation copies; native geometry, model cards,
and canonical source are unchanged.

`run_mismatch.py` qualified repeated seed56001, changed seed56002, two disabled
controls, and 27→125→−40→27°C without reset/reseed between temperatures. All
eight devices' W/L/DELVTO/FACTUO were read before and after every transient.
Repeated-seed and disabled-control waveforms were byte-identical; changed seed
varied all eight devices; disabled DELVTO=0/FACTUO=1; return-temperature waves
were byte-identical. Qualification passed; receipt SHA256
`48c6c714c05226590f5cc6d65a95c561568b97c842a9b7083496826db5091167`.

The qualified fixed-load screen comprises seeds56101–56200, 100 distinct
32-parameter vectors, 400 completed temperature transients, 1.2/3.3V supplies,
20fF output load, 900ns duration and 100ps maximum step. Each simulation uses
one thread. Aggregate simulation wall time across samples: 433.998s; samples
were distributed across three independent processes. All original bulk results
are retained outside Git; [independent audit](screen100-audit-20260922.json)
binds each manifest, contract, analysis and waveform to exact hashes.

| Check | Status | Simulated result |
| --- | --- | --- |
| 100 samples / 400 temperature transients | passed | All completed, finite and endpoint checked |
| Frozen parameters, unique draws, temperature return | passed | 100 distinct draws; full before/after equality |
| Settled low ≤0.33V / high ≥2.97V | passed | Worst low 0.197µV; minimum high 3.299999832V |
| Exactly one rising and falling output edge | passed | All 400 waveforms |
| 50%-crossing timing characterization | passed | Rise delay 0.622–0.757ns; fall delay 0.830–1.212ns |
| Pulse-width characterization | passed | 300ns input; output 300.185–300.488ns |
| Current characterization | passed | VDDA peak draw ≤681.342µA; VDD ≤85.506µA |
| Settled current characterization | passed | VDDA ≤0.379nA; VDD ≤6.416nA |
| Acceptance against allocated timing/current limits | not run | Values above are descriptive; no new limits adopted |
| Actual receiver mismatch / adverse power order | not run | Separate required work; fixed20fF screen is insufficient |
| Physical measurement | not applicable | This is a simulation campaign |

Reproduction, from repository root in the pinned runtime, using a fresh output
directory for each command (the results directory must be mounted):

```sh
python3 designs/g1-guardian/blocks/g1_ctrl/ls/sim/qualification/run_mismatch.py --mode qualify --output "$RESULTS_ROOT/ls-mismatch-qualify-20260922-r1"
python3 designs/g1-guardian/blocks/g1_ctrl/ls/sim/qualification/run_mismatch.py --mode screen --qualification "$RESULTS_ROOT/ls-mismatch-qualify-20260922-r1/qualification.json" --seeds "$SEED_CSV" --output "$FRESH_OUTPUT"
python3 designs/g1-guardian/blocks/g1_ctrl/ls/sim/qualification/audit_screen100.py --results-root "$RESULTS_ROOT" --output "$FRESH_AUDIT_JSON"
```

Exact shard names and ranges: `ls-screen20-shard0/1/2-20260922-r1`
use56101–56107/56108–56114/56115–56120;
`ls-screen100-shard0/1/2-20260922-r1`
use56121–56147/56148–56174/56175–56200. Script identity is
`8de2466e9f5819551c684744bd988cb860f8b9091d8ca238b43b49964f340963`.
V16 remains incomplete: actual route resistance/receiver loading, adverse
conditions, supply sequencing and back-powering are not closed by this screen.
