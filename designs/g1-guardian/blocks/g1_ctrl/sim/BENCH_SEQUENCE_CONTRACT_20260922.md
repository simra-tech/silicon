# Executable bench sequence RTL contract

Status: **passed**, simulated RTL only. Production RTL unchanged.

The external load-bus inhibit is a separate test-fixture input, not EN or a
chip register. With that inhibit asserted, EN may be raised to program/read
the serial interface without energizing the modeled load. EN low resets the
serial interface and configuration; the test proves an attempted write is
ignored and CHIP_ID serial read returns zero while reset is held. After each
EN cycle it reads the default values, explicitly reprograms, and verifies the
new values before applying the bus. A synthetic SENSE_OFS=+3 verifies retained
register state and effective-code arithmetic, **not analog calibration**.

The two persistent-fault scenarios use a 10 MHz ideal oscillator, 5 MHz serial
clock, HARD_N=4, MODE=0x02 (hard enabled, soft/FAST/retrigger disabled). The
behavioral hard comparator updates 1 ns after its falling decision edge; its
fault input stays asserted after trip. The analog latch input is tied low.

| Programmed INRUSH | Remaining masked clocks at bus application | Clocks from application/unmask to trip | Result |
|---:|---:|---:|---|
|0|0|11 after application|passed|
|8 (4096 clocks)|2840|7 after mask expiry|passed|

Programming does not restart the inrush timer. The measured residual mask is
therefore smaller than its programmed length. While masked, gate enable stays
high; afterward the persistent hard fault latches digital trip, disables gate
enable, and remains latched for the observed no-retry interval. Acceptance was
prospectively bounded at16 clocks after application/unmask. Both EN cycles,
serial checks, mask assertions and final isolation passed: **2888 checks,
0 errors**, simulated endpoint568.552 µs.

Evidence: [simulation record](campaigns/20260922T152333Z_4fd535fc/simulation.json),
[simulation log](campaigns/20260922T152333Z_4fd535fc/simulation.log),
[testbench](tb_bench_contract.v). The record hashes every production RTL source,
the testbench and runner. Icarus Verilog14.0 devel
`s20260301-328-geda9fdcd-dirty`, x86_64; simulated runtime0.351 s.
Pinned image config SHA256:
`ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`.
The flow also checks PDK commit84374023ee8b4b126bebbba67fcbada0a9c0ff0b;
this RTL test uses no analog PDK model.

After the completed run, runner argument validation was tightened to accept
only integer timeouts1..120 before creating output directories; the default
remains120. Host Python3.11 argument-only tests rejected0,−1,121,1.5 and a
non-numeric string with exit2 and no new campaign/build directories; boundary
values1/120 passed the validator. The first validation attempt used host
Python3.6 and failed in the test driver's unsupported `capture_output` API,
before invoking the runner; the Python3.11 check above completed successfully.
The completed RTL campaign retains its actual pre-validation runner SHA
`f1519be57c32e22a9c17441719ea769138f68a52ea2ff65bcb14fa4d057b2d48`;
the argument-validated runner SHA is
`575afadadce466e776a3fcd9ba16bd1a66da80c633209c948167f96f62fa771c`.
The RTL simulation was not rerun for this argument-only change.

Reproduce after an independent fresh resource gate and allocated CPU:

```sh
G1_CPUS=1 G1_CPUSET=6 G1_MEMORY=1g flow/run.sh timeout 60 python3 designs/g1-guardian/blocks/g1_ctrl/sim/run_contract.py --suite bench --timeout-seconds 25 --image-id sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2
```

The runner preserves each invocation in a unique campaign directory. Physical
external-inhibit effectiveness, bus transients, analog comparator/GATE/FET
behavior, oscillator startup, calibration accuracy, pad-inclusive response,
PVT/MC/PEX and silicon measurements: **not run by this contract**. This is not
a proof of single-fault tolerance or a new analog acceptance result.
