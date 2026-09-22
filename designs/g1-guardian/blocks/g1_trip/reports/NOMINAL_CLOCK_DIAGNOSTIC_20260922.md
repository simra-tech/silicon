# Nominal-clock residual diagnostic — simulated

The selected seed71002 hot residual failure remains at nominal 5 MHz. At
125°C both comparator outputs are HIGH at the selected 24.5 mV lower point;
at 25°C both are LOW. This is a two-point diagnostic, not a new qualification
campaign or a reclassification of the preserved 10 MHz failure.

| Temperature | Preserved 10 MHz soft / hard | Fresh 5 MHz soft / hard | Fresh lower-point status |
|---|---|---|---|
| 25°C | LOW / LOW | LOW / LOW | passed |
| 125°C | LOW / HIGH | HIGH / HIGH | failed |

Both fresh leaves completed numerically (178.774 s room, 189.147 s hot), with
all 27 observed parameters exactly equal to their respective original leaves.
Frozen seed71002, soft/hard codes136/154, 24.5 mV input, source bytes, pinned
models, supply/load connections, SPARSE solver, tight Gear tolerances and
0.2 ns maximum step remained unchanged. The source is the gm4/comp3 candidate
SHA256 `baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`.
Tool identities are in the portable provenance: ngspice46, IHP SG13G2 commit
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, pinned image manifest
`sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`.

## Declared timing and observation changes

Clock width/period changed from 50/100 ns to 100/200 ns. Delay20 ns and
rise/fall0.2 ns did not change. The endpoint changed from0.52 to1.02 µs to
retain five full decisions and sample the same last three cycles. Measurement
times were mapped prospectively, not selected after reading the result.

Primary decisions use 20 ns after the measured0.6 V rising crossing of the
actual clock: top `clk` for soft and saved `xt.cmp_clk_n` for hard. Both leaves
have exactly five rising crossings per channel. The last-three primary
decisions agree unanimously with the retained mapped legacy sample times.
No majority vote or mixed-sample acceptance was used. Late hard samples were
approximately540.539/740.539/940.539 ns at room and540.549/740.549/940.549 ns
at hot; actual inverter delay is measured, not assumed.

Five additional saved vectors expose `xt.cmp_clk_n` and
`xt.xch.xp/xq/xn/yn`. Their hierarchy was verified against the frozen source;
13 finite waveform columns are required. At the hot hard evaluation edges,
all four frontend nodes are near1.2 V at edge−1 ns, then regenerate to
`xn` LOW / `yn` HIGH by approximately edge+0.5 ns. The retained hard output
alone would not establish this reset/regeneration behavior. At the third
hot edge, differential input is about−40.927 mV at−1 ns, −7.258 mV at the
actual clock crossing, −6.248 mV at+0.2 ns and−7.940 mV at+1 ns. Room at the
same relative offsets is approximately−45.136, −12.949, −12.410 and−14.419 mV.
These observations expose dynamic behavior but do not isolate a causal block,
replace loaded transient analysis with static differential sign, or establish
equivalence of the original unsaved internal clock timing.

## Reproduction and evidence

From `blocks/g1_trip/sim`, inputs were prepared with
`prepare_nominal_clock_probe.py --reference <reference> --run-id <fresh-id>`.
Reference leaves are `joint-gm4comp3-code204-s71002-20260922-a-s71002-p22`
(room) and `...-p26` (hot). Execution used
`run_nominal_clock_probe.py --run-id <fresh-id> --image-id <manifest-above> --timeout-s 600`
through the pinned flow, one CPU per leaf, optional new-wave gzip archival.
Fresh IDs are `joint-gm4comp3-s71002-5mhz-room-20260922-a` and
`joint-gm4comp3-s71002-5mhz-hot-20260922-a`.

The [strict comparison](resume-server-20260922/joint-gm4comp3-71002-nominal-clock-comparison.json)
passed its numerical, parameter, source and sampling contract while explicitly
retaining the hot electrical failure. Portable run directories under
`resume-server-20260922/portable-runs/` contain exact summaries, preparation,
declared deck differences, source/tool identities, runner snapshots and artifact
hash inventories. Both retained run directories total2,132,667 bytes; this is
observed output, not a statistical size bound. Six focused sampling tests and
35 existing SENSE/TRIP-related tests passed.

Full 5 MHz calibration, full temperature/guard coverage, statistical sampling,
additional shunt midpoints and candidate physical PEX qualification are **not run**.
The existing three-pilot 10 MHz campaign and its residual failure remain unchanged.
