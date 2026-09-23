# Joint corner, supply and common-mode coverage

The current typical 300-sample campaign uses typical process sections,
VDDA/VDD = 3.3/1.2 V and SHN grounded. Consequently its actual input mean is
half the differential shunt voltage, not a fixed zero common mode. Its frozen
25 °C calibration and −40/125 °C endpoint checks do **not** close supply,
process-corner, or the specified −0.1 to +0.3 V true-common-mode coverage.
Standalone SENSE grids and separate T2F ensembles cannot substitute for joint
BGR/SENSE/DAC/comparator evidence.

The reviewed [prospective contract](qualification/joint586-adverse-preparation-20260923-a/contract.json)
preserves the full 11,512-parameter/3,500-instance population, 27 legacy anchors,
original binary calibration, signed correction, saturation, threshold guards,
and 0.5 mV residual tests. Only declared process sections and fixture inputs
change; model cards and canonical sources are unchanged.

| Required scope | Status at this checkpoint |
|---|---|
| Slow and fast six-control operating-point qualification | Passed both full 11,512-parameter gates, changed draws, exact repeat/disabled/return controls |
| Same-corner transient repeat/disabled/temperature return | Slow ten-control independent audit passed; fast controls in progress |
| Actual SHN append-only observation, exact original-18-column parity | Slow passed: 6,710 rows, exact original-18-column projection and actual mean/differential; fast pending |
| Six required rail/common-mode fixtures per corner | Slow in progress after its own gate; fast dependent gate pending |
| Thirty slow samples, seeds 77101–77130 | Not run |
| Thirty fast samples, seeds 78101–78130 | Not run |
| Crossed extreme common mode with cold/hot and rails | Not run; explicitly separate deterministic coverage |

Each prospective corner sample retains its original room/nominal-rail
calibration and applies its fixed codes to ten conditions: original room/cold/hot
inputs; cold/hot at tied low/high rails and true common mode zero; and room
nominal-rail true common modes −0.1, 0 and +0.3 V. Code and clock HIGH amplitudes
track VDD. The existing fixed 0.6 V decision and clock-crossing rules remain
unchanged. An actual SHN observation will verify input mean and differential;
they will not be inferred solely from the deck declarations.

Expected work is about 70 transient leaves per sample. Extrapolating only from
the completed typical first twenty gives approximately 512 CPU-hours and
34.5 GiB for both thirty-sample cohorts, plus about 17.6 CPU-hours of separately
declared deterministic common-mode interactions and qualification overhead.
This is a planning estimate, not a measured adverse-corner throughput guarantee.
The original 1,200-second leaf caps permit a much larger 1,400 CPU-hour total.
No corner population launches before its own source/parameter/harness gate.

The [slow transient audit](qualification/joint586-slow-transient-qualification-20260923.json)
passed all twelve checks. Its four-phase temperature-return control completed
in 1,637.069 seconds of simulation wall time with exact initial/final room waveform
bytes and all 11,512 parameters unchanged. Compact portable receipts are retained
under [slow qualification evidence](qualification/portable_evidence/joint586-slow-transqual-20260923/).
This qualifies the stated model-level fixture, not physical parasitic adoption.

The additive [staged scheduling contract](qualification/joint586-adverse30-contract-20260923-b/contract.json)
leaves the original serial contract intact. Binary calibration remains sequential.
After its codes and full parameter vector are frozen, the exact original 40 guard
and 20 residual leaves may run as independent one-thread processes. Every deck is
prehashed, each leaf owns a distinct directory, and only the final assembler writes
the ordered parent ledger after all children are terminal. Fifteen software tests
passed, including all 120 held-out deck comparisons across both corners,
unchanged watchdog/analysis calls, missing and duplicate rejection, and failed-leaf
retention. These tests are not analog simulation results. First-sample strict audit,
then first-twenty and final-thirty disposition, remain required.

The typical campaign's missing 100-sample scheduling boundary was corrected
prospectively: already-running samples continue, exact unclaimed seeds resume
only through 73100, then the full fixed-100 audit precedes 73101–73300. No valid
simulation was interrupted, no failed seed was replaced, and no electrical
failure is removed from the denominator. The original failures, including
[73044's 1,200-second failure](qualification/joint586-s73044-p03-failure-analysis-20260923.json),
remain failures. Its full BEFORE inventory matches, while AFTER, legacy output
and waveform completion are **not run**.
