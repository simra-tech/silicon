# Failed mixed-signal execution on the receiving host

The original assessment's `completion=passed` is invalid as a mixed-signal
completion claim. It is preserved as evidence of the runner defect.
The log says `Unable to open input file` for the lowercased RTL executable
path and reports XSPICE/co-simulator counts7/0 and48/0. Ngspice reached4µs
without loading the RTL; electrical acceptance is **not run**.

The source directory contains uppercase timestampT/Z while ngspice lowercases
`sim_args`. This worked on the previous case-insensitive filesystem, but fails
on the receiving host. No circuit/model/solver modification resolves this;
the runner now creates lowercase paths and rejects these co-simulator errors.
Strict archived-host replay already failed (1606versus2429points), correctly
preventing qualification. Recovery requires a fresh run and complete comparison.
