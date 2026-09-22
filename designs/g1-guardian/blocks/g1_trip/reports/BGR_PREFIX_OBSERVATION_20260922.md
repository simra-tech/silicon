# Hot BGR prefix: failed fixture, retained observations — simulated

The 219 ns prefix fixture **failed** because eight inherited measurements
requested later times. Its original summary and exported failure are unchanged.
A separate read-only audit establishes finite saved vectors and complete
parameter inventories, not a retroactive fixture pass or late-state result.

| Property | Result |
|---|---|
| Original runner/fixture contract | failed, eight out-of-interval measurements |
| Watchdog | completed in 249.454 s, within the 300 s cap |
| Saved transient observations | 1,400 finite 18-column rows through 219 ns |
| Non-BGR 8,670 parameters before/after | exact versus the original hot OP inventory |
| BGR 2,842 nominal parameters before/after | exact versus retained nominal reference |
| Original 24 non-BGR anchors | exact |
| First actual-edge versus legacy samples | LOW/LOW, both policies agree |
| Three late-cycle decisions | not run |
| Physical qualification | not run; inherited fidelity gate failed |

Run ID: `joint-bgr586-hot-prefix219ns-20260922-a`. It retains seed 71002,
125°C, nominal BGR source `586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b`,
24.5 mV shunt, fixed codes 136/154 and all original source/card/clock/solver
settings. The only normalized deck change is
`tran 0.2n 1.02u 0 0.2n` to `tran 0.2n 219n 0 0.2n`, plus run paths.
Deck SHA256 is `5895da655a38ce05727d908873413f5b1cf4161f4598ab5e4d64c179de037261`.
All 21 input bindings and pinned ngspice 46/image/PDK/model identities passed.
There was one simulation, no rerun, timeout extension or settings change.

## Measurement failure and command order

The preparation overlooked inherited measurement times outside the shortened
interval. Their exact FIND requests were:

| Measurement | Vector | Requested time |
|---|---|---:|
| `ds_pre` | `ds` | 819.8 ns |
| `ds_kick` | `ds` | 821 ns |
| `ds_sample` | `ds` | 840 ns |
| `qs_sample` | `v(cmp_soft)` | 840 ns |
| `dh_pre` | `dh` | 920 ns |
| `dh_kick` | `dh` | 921.2 ns |
| `dh_sample` | `dh` | 940.2 ns |
| `qh_sample` | `v(cmp_hard)` | 940.2 ns |

The literal sequence was: BEFORE inventories → TRAN → AFTER inventories →
`let ds/dh` → eight failed FIND measurements → legacy 27 parameter prints →
`wrdata` → `QUALIFICATION_END`. No reset, alter or new circuit analysis occurs
after TRAN. FIND measurements and derived `let` vectors do not modify circuit
state. The simulator process returned zero, but the strict runner rejected the
eight error lines and exited one. There were no other classified errors.

The [independent observation audit](resume-server-20260922/joint-bgr586-prefix219ns-failed-fixture-observation-audit.json)
records exact commands/line order, errors, complete ordered parameter groups,
saved-vector hashes and the preserved failed-summary hash. The first trajectory
reader rejected the failed fixture as designed; its explicit separate-audit
mode requires those live hashes and never rewrites the original acceptance.
The future preparer now rejects out-of-window measurements before allocating
a run; no silent deletion or remapping was added. The original preparer snapshot
and failed deck remain retained, including the oversight.

## First evaluation-pair observations

This covers the first soft/hard evaluation pair, not the full 20–220 ns period.
Actual 0.6 V clock crossings are 20.100 ns soft and 120.549416 ns hard.
At 20 ns after those edges, the saved hot output samples are respectively
3.024 µV and 0.194 µV: both LOW and in agreement with separate fixed-phase
40/140.2 ns samples. Comparator differentials are −3.773 mV soft and
−39.509 mV hard at the corresponding decision samples. These are not the
missing three-late-sample acceptance results.

At the first hard edge, `xp/xq/xn/yn` were near 1.2 V one nanosecond before
evaluation. At edge+0.5 ns, hot `xn` is 1.200261 V and `yn` is 0.745 mV,
with hard output 1.174 mV; by edge+1 ns, hard output is 0.249 µV. The finite
saved internal trajectories show this first evaluation transition, not repeated
late-state stability or a physical device-voltage qualification.

The [matched-phase trajectory analysis](resume-server-20260922/joint-bgr586-prefix219ns-trajectories.json)
compares the same nominal-BGR source at room/hot temperatures, with all full
before/after parameter groups equal. It retains all 18 vectors at actual-edge
offsets −1/0/0.2/0.5/1/20 ns, with explicit interpolation brackets and fractions.
Quiet hot-minus-room VREF is −1.437 mV, VREF_BUF −1.121 mV, pedestal −1.876 mV,
ISENSE +1.225 mV and conditioned input +0.610 mV. IPTAT pin voltage changes
−27.915 mV; this is not output current. Quiet soft/hard differential motion
is +1.439/+1.478 mV. At each channel's first actual-edge+20 ns sample,
differential motion is +3.845 mV soft and +4.265 mV hard.

The nominal-ratio algebraic decomposition reconstructs every sampled
differential within 1.67×10⁻¹⁶ V. Its residual terms are descriptive accounting,
not isolated block causality. Across this source substitution the reference
nominal level also changes; no new calibration or waveform parity against the
original BGR is claimed.

All 14,560 resistor voltage-limit warnings occur during OP/transient
initialization: 7,280 before the BEFORE inventory and another 7,280 after it,
before `Initial Transient Solution`, plus one initial temperature-limiter NaN.
No warning is printed after the initial transient solution. Warning-associated
initialization excursions are not evidence of positive-time node violations.

## Retention and limits

The portable failed-run export includes the unchanged summary, source/runtime
provenance, original preparer/runner snapshots, endpoint diff and all artifact
hashes. Bulk wave/log/progress data remain retained. Reproduce the read-only
checks with `audit_failed_bgr_prefix.py --output <fresh JSON>`, then
`analyze_bgr_prefix_trajectories.py --failed-prefix-observation-audit <that JSON>
--output <fresh JSON>` from `blocks/g1_trip/sim`.

The original [full-hot 600 s timeout](BGR_SUBSTITUTION_TRANSIENT_20260922.md),
earlier electrical failures and [SENSE physical-fidelity failure](../../g1_sense/layout/coordinated_gm4/README.md)
remain unchanged. Further simulation, late-state recovery, new calibration,
statistical expansion and physical adoption are **not run** by this work.
