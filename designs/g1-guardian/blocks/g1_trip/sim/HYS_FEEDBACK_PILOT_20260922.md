# Loaded one-LSB hysteresis feedback pilot — simulated

The scoped mechanism passed, but the existing1 µs settling-interval contract
failed. Correct decisions in this one large-margin test do not qualify general
hysteresis operation, threshold accuracy, routed timing or physical safety.

The actual unchanged trip timer/synchronizer drove the physical eight-bit DAC
inputs in original SENSE/TRIP transistor-level sources with the flagged BGR CPEX
source, both comparators and actual passive/hold loading. Static configuration
was soft128/hard240, HYS1, SOFT_TIME1, symmetric decay, no inrush/hard/FAST/retry.
Ideal10 MHz oscillator drove the actual divide-by-two comparator clock. The
imposed shunt profile was10→35→10 mV at1.2/1.6 µs with1 ns edges.

| Check | Status | Simulated evidence |
| --- | --- | --- |
| Full3 µs mechanism | passed |29 frozen gates;24139 finite rows with61 saved vectors;606.312 s within900 s watchdog |
| Prefix identity | passed |6412 rows on0–0.85 µs: original60 columns and time grid numerically AND decoded-byte exact, including formatting/newline; new hard-clock column explicitly projected away |
| Seed/source/runtime | passed | Seed71001;27 post-transient parameter values exactly match reference; unchanged source/VVP/model identities |
| Same-instance pre-transient parameter query | not run | Direct transient uses its internal initialOP; no separate query is claimed |
| Actual timer/DAC major carry | passed |128→127 at1.621281 µs,127→128 at2.321281 µs; all8 physical bits switched each time |
| Counter and synchronizers | passed | All24 counter bits observed; peak4, correct up/down recurrence, recovered0; no trip latch |
| Guarded decisions | passed |12 soft and12 hard decisions correct under prospective5 mV actual-input differential guard; soft HIGH observed on two fault evaluations |
| Initial decision classification | not run | Three pre-0.6 µs evaluations retained but excluded from guarded classification |
|1 µs settling interval | failed | Next soft evaluation100 ns after first carry and simultaneous with return carry (0 ns) |
| Model-warning resolution | not run |18 initial voltage-range warnings and one temperature-limiter NaN diagnostic retained; subsequent complete waveform was finite |
| HYS2/offset-carry/PVT/route-skew/physical qualification | not run | No follow-on campaign authorized by this result |
| Serial/FAST/GATE qualification | not applicable | Excluded from this isolated static-configuration mechanism study |

The code changes disturb the real loaded reference and DAC threshold. Over each
declared carry window (2 ns before through200 ns after bit midpoints), the
simulated node extrema were:

| Carry | VREF-buffer range | Soft-threshold range |
| --- | --- | --- |
|128→127 |1.00750–1.06034 V |0.70550–0.80048 V |
|127→128 |0.88100–1.07677 V |0.67656–0.77511 V |

These are sampled transient extrema, not allocated error budgets or proof of
settling. Every actual soft-clock rise/internal hard-clock rise, differential,
raw decision20 ns later, synchronized state, counter and code event is retained
in the compact [full result](../reports/hys-feedback-20260922/hys-feedback-full-20260922-r3/full_check.json).
The large stimulus margin can tolerate transients that a near-threshold case
cannot; no near-threshold or adverse-PVT claim follows.

## Preserved predecessor failure

The first0.9 µs fixture explicitly ranOP thenTRAN. Its Icarus instance could not
be reused: input/output counts became4/0 and47/0, all RTL outputs stayed0 and
the checker failed despite a finite analog endpoint and exact54 parameter
observations. That100.030 s failure remains separate. The reviewed direct-TRAN
revision removed only explicitOP and its pre-query block; its0.9 µs prefix
passed20 gates in170.134 s. Digital lifecycle controls and compiled-VVP replay
were byte-identical to the original passed digital control.

## Built against and reproduction

| Item | Identity established |
| --- | --- |
| PDK | IHP SG13G2 `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; actualCOMMIT/model/OSDI hashes checked |
| Simulator | ngspice46, SPARSE1.3, tight Gear; unchanged pinned runtime/version compared before launch |
| RTL simulator | Pinned Icarus14 development runtime; compiled VVP hash `41b82c937707bf9753f10c27cf3541af2750ddbc6e49b1e7fe36f8ca2f7fda45` bound to passed byte-identical digital control |
| SENSE source | `8880157bd2a88c92a248c4865fc79b9242954d1920ce6e3834b776cae6eee57f` |
| Consumed TRIP source | `f49e17db24fc85f4f62aab3cc98dce996d027567417ad80cfea13d11609ba2e1`; existing grounded substrate mapping |
| BGR source | `944aaf94b9a005718abd0ebd92956acc99e8cb7a23ec8556d406736f4e8ef6f9` |
| New extraction/layout checks | not run; no physical changes made |

See [prospective contract](HYS_FULL_FEEDBACK_CONTRACT_20260922.md),
[checker](check_hys_full.py), [launcher](run_hys_full.py) and
[source/output bindings](../reports/hys-feedback-20260922/bindings.json).
The additional exact decoded-byte gate was frozen before launch and is retained
in the full run's prospective addendum. No model card or production RTL changed.
From the repository root, with the pinned runtime and frozen qualification
inputs available, the executed full-leaf command was:

```sh
G1_CPUS=1 G1_CPUSET=0 G1_MEMORY=4g flow/run.sh python3 designs/g1-guardian/blocks/g1_trip/sim/run_hys_full.py run --run-id hys-feedback-full-20260922-r3
```

The launcher refuses to overwrite a completed leaf. Prepare a fresh ID only
under a newly reviewed resource/acceptance contract; do not overwrite evidence.
