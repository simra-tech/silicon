# One frozen mismatch draw — harness qualification

Prospective **not run**. Source586ffb58 has completed nominal34-temperature,
fast-ramp startup, single20us-maxstep slow-ramp and matched100nA load controls.
Original coarse-step startup failures and model/rating/physical-fit exclusions
remain. This stage tests the new2842-parameter harness, not population yield.

Exactly five sequential leaves: enabledseed44001 forward, exact repeat, reverse;
disabledseed44001 and44002. The latter are no-mismatch invariance controls,
not additional random samples. Use the retained nominal deck with only seed,
enabled mismatch libraries/source, and reverse sweep direction changed.
All other source/init/model/temperature/rail/load/tolerance bytes are frozen.
MM-enabled source is identical except explicitmm_ok=1 on each XM/XR/XQ line;
reverse stripping must reconstruct the exact original source. No unit selection
or coefficient fitting depends on this draw.

Require exactly2842 unique finite named parameter observations before and after
each34-point -40..125 C sweep, exact same-instance values, same-draw values
across forward/repeat/reverse and exact repeat waveform bytes. Disabled seeds
must match retained nominal waveform bytes and each other's full parameters.
Report exact normalized reverse-wave equality separately. Prospectively allow
at most1uV for voltage columns and1nA for two current columns when comparing
forward/reverse solves; these are numerical-direction consistency bounds, not
performance allocations. Neither tolerance can turn strict byte equality into
a pass. Report one-drawTC<=50ppm/C separately from harness qualification.

One CPU6,120 seconds per leaf, fresh0.25GiB HOME growth gate and8GiB reserve.
Nominal20.6 seconds suggests roughly100–200 seconds for five; no guarantee.
Stop at numerical/parameter failure; retain remaining leaves as **not run**.
No automatic retries. A numerical/TC failure is not a reason to replace seed.
Source-realized geometry/whole-chip PEX, broad MC, reliability, actual downstream
load and production adoption remain **not run**. Physical measurement is
**not applicable** to this simulation harness check.
