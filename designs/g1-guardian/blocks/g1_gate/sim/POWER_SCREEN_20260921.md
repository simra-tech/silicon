# Expanded power-sequencing screen

Simulated C-PEX GATE with detailed input/output pads,5nF/10Ω external stand-in and10kΩ pull-down. Original IO-first/missing-core electrical failures remain. These new campaigns test core-first power-up and IO-off-first shutdown only, EN held low. Each MOS corner covers−40/27/85/125°C, correlated core/IO rails1.08/3.0,1.2/3.3,1.32/3.6V and ramp-time scale0.1/1/10. The actual ramp durations are0.2/2/20µs with the original separation scaled equally.60s watchdog per case.

Baseline pad solver settings are retained; tighter numerical qualification is incomplete. No realFET or arbitrary ramp skew is qualified. Tool/PDK/model hashes and exact commands are in each campaign manifest.

| MOS | Attempted | Completed and electrical passed | Failed completion | Timed out | Campaign |
|---|---:|---:|---:|---:|---|
|ss|72|58|5|9|`20260921T154820Z_e7385473`|
|ff|72|46|10|16|`20260921T154835Z_0f95da25`|
|tt|72|52|7|13|`20260921T154835Z_5cc99b91`|

Failed/timed-out cases have electrical acceptance **not run**. Every completed case meets the fixture GATE/gfet<1V criterion; this does not close the missing cases or establish a supported allPVT power-sequencing contract. The historical runner returned exit0 after finishing a campaign loop even with incomplete cases; the per-case manifest is authoritative. New invocations now return nonzero if any case is incomplete or electrically fails.

## Tristate-pad replacement pilot

An unchanged `sg13g2_IOPadTriOut30mA` with `c2p_en` tied to core VDD does **not** fix startup. Nominal IO-first and missing-core cases complete but both raise GATE to3.28823V (`20260921T170457Z_17f0f348`). Core-first and IO-off-first complete/pass their EN-low checks; core-off-first times out90s (`20260921T170458Z_936f6193`). This isolated candidate is not adopted. Model cards remain unchanged.
