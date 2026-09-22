# Nominal BGR source-substitution diagnostic — simulated

The room-temperature controlled comparison passed. The hot comparison failed
its unchanged 600 s watchdog; it does not establish a hot electrical result.
Original 10 MHz and 5 MHz hot failures remain unchanged.

| Check | 25°C | 125°C |
|---|---|---|
| Numerical endpoint 1.02 µs | passed, 273.972 s | failed, watchdog at 600.236 s |
| Non-BGR 8,670 parameters before TRAN | exact | exact |
| New BGR 2,842 nominal parameters before TRAN | exact | exact |
| Both complete inventories after TRAN | exact | not run |
| Original 24 non-BGR legacy anchors at completion | exact | not run |
| Last three actual-edge/legacy decisions | both LOW, agreement passed | not run |
| New physical qualification | not run; inherited gate failed | not run; inherited gate failed |

The two run IDs are
`joint-bgr586-nominal-substitution-room-20260922-a` and
`joint-bgr586-nominal-substitution-hot-20260922-a`.
They retain seed 71002, 24.5 mV shunt, fixed codes 136/154, all SENSE/TRIP
sources, body connections, cards, loads, 5 MHz clocks and tolerances.
There was no recalibration. Only the BGR source changes from the original
mismatch-enabled source to nominal
`586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b`.
The full draw inventories are required because the new source changes the
number of devices; equal seeds alone were not accepted as realization parity.
The [separate room and hot OP prerequisite](BGR_SUBSTITUTION_DRAW_AUDIT_20260922.md)
established complete same-temperature non-BGR baseline inventories.

Four explicit parameter-print blocks surround TRAN. Removing those blocks and
normalizing only run labels reconstructs the archived 18-vector clock fixture
exactly. Source/deck diffs and twelve live input bindings per leaf are retained.
The 18 outputs retain all original hard internal nodes and bias observations.
Primary decisions are sampled 20 ns after measured 0.6 V actual clock rises,
with all three late samples required to agree with the retained legacy samples.
The room waveform passes that contract; source substitution does not imply
waveform parity. Its nominal reference level also changes, so a passed selected
point is not calibration accuracy or candidate adoption.

## Hot numerical diagnosis

The last reported hot simulation time was 0.620200 µs, versus the required
1.02 µs. No `.dat` file was produced because the deck exports it after TRAN.
The full log, progress samples and timeout receipt are preserved; there is no
recoverable exported partial waveform or qualified late decision sequence.
The AFTER groups were not reached. BEFORE equality cannot replace them.

Slowness was already visible before the first 20 ns clock edge: one-second
progress samples span at least 8.79 wall seconds over 0–19.9 ns, versus 1.08 s
at room temperature. The first 20–20.2 ns edge spans at least 9.91 s hot versus
3.28 s room. Subsequent narrow clock-edge windows repeatedly span roughly
8–12 s; broad between-edge windows also progress slowly. This is not evidence
of a single startup stall. Sampling only bounds printed progress: it cannot
identify accepted timestep counts or establish a causal device mechanism.

The corrected warning inventory contains 14,560 hot resistor voltage-limit
warnings: 5,216 in BGR, 8,560 in TRIP and 784 in SENSE, plus one initial
temperature-limiter NaN warning. There are 1,567 distinct affected device
instances, plus the unclassified temperature warning. Both warning families
begin before the first printed transient progress value. Room has 30 SENSE
voltage-limit warnings and one temperature warning. The unchanged-source hot
observation completed in 190.767 s with 193 warnings. Neither numerical
completion nor fewer warnings establishes model validity.

All hot voltage-limit warnings finish before `Initial Transient Solution`:
7,280 occur before the BEFORE inventories and another 7,280 between
`BGR_BEFORE_END` and that initial-solution marker. No voltage-limit warning
is printed during positive-time TRAN progress. These warnings therefore
document OP/transient-initialization excursions, not observed late-clock
voltage-limit violations, and cannot establish the cause of recurring TRAN
slowness. The last preceding progress value for each warning family is zero.

The original runner's retained warning arrays contain 63/14,577 lines: its
substring search also captured 32/16 finite parameter lines whose valid
instance names contain `xmnan`. Those original arrays and the initial reader
output remain unchanged. The [corrected read-only r2 inventory](resume-server-20260922/joint-bgr586-substitution-outcomes-r2.json)
separates these false positives and retains exact warning families/instances,
progress windows and original-reference comparisons. The unversioned initial
`joint-bgr586-substitution-outcomes.json` is superseded for warning classification,
not for the unchanged numerical outcome. No model or simulator setting changed.

## Scope and next diagnostic

The inherited [SENSE physical-fidelity gate](../../g1_sense/layout/coordinated_gm4/README.md)
is failed: bias-device gate-count mismatches and shared-input diffusion
area/perimeter differences remain. These are controlled existing-model-level
diagnostics, not new physical qualification or broad mismatch statistics.

A possible next bounded diagnostic is a fresh exact-source hot prefix ending
at 219 ns, after one complete soft/hard evaluation, with a 300 s cap,
the same settings and complete
before/after inventories, to export finite bias/internal-node trajectories.
It would test numerical behavior and actual node trajectories, not
qualify the missing late-cycle outcome. This is **not run** and requires review;
no timeout extension, retry, setting change, additional midpoint or MC was run.

Reproduction uses `prepare_bgr_substitution_transients.py` followed by
`run_bgr_substitution_transient.py --run-id <id> --image-id <pinned-manifest>
--timeout-s 600` only after the required same-temperature OP audit.
The exact command, pinned ngspice 46/image/PDK/model hashes and source identities
are in both portable exports. `analyze_bgr_substitution_outcomes.py --output
<fresh JSON>` performs only read-only diagnosis. Both successful and failed
run exports retain compact summaries, full source/deck difference declarations,
parameter inventories, input bindings and hashes of all separately retained logs.

The later [219 ns prefix observation report](BGR_PREFIX_OBSERVATION_20260922.md)
preserves a separate fixture failure from eight inherited out-of-interval
measurements. Its explicitly separate saved-waveform/inventory audit does not
recover this full-hot timeout or establish missing late-cycle acceptance.
