# Exploratory RTL state faults — 2026-09-21

`sim/campaigns/20260921T152058Z_96dc7531` records796 passing behavioral assertions in the actual256-stage plain/128-stage triplicated monitor configuration, Icarus14 development build in the pinned EDA image. Command: `G1_CPUS=1 G1_MEMORY=2g flow/run.sh python3 designs/g1-guardian/blocks/g1_ctrl/sim/run_contract.py --suite fault --image-id sha256:5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0`. Source/version hashes and exact compile command are retained.

Passing assertions confirm these observations; they do **not** establish fault-tolerant control:

- All384 single-copy monitor-stage locations mask a one-bit upset and correct it on the next clock; correction count384, uncorrectable count0.
- A two-copy same-stage fault corrupts the majority value and subsequently increments the uncorrectable count.
- One selected monitor counter-copy upset is masked and rewritten.
- Each of the8 hard-DAC configuration-bit upsets changes the effective code and persists until rewrite/reset. Configuration registers are not triplicated.
- An OSC_EN configuration upset persists. A stopped oscillator prevents clocked digital recovery; the test separately demonstrates asynchronous EN reset.
- With FAST disabled and the clock absent, a hard comparator high does not cause a digital trip in the2µs observation window; the digital gate-enable monitor remains high. This is a dangerous fault condition, not a passing safety requirement.

Not run: exhaustive counter/voter/common-cause faults, synthesis/physical-node injection, analog output-pad response to clock/reset faults, charge-to-LET mapping, radiation cross sections or irradiation. The separate analog current-pulse campaign is exploratory and must retain its own scope.
