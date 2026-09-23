# IO tap source alternatives: no equivalent replacement established

The strict tap A/P failure remains open. This source-only follow-up rules out
two apparent alternatives; it does not correct or waive the original failure
documented in [the pinned audit](RESULTS_20260922.md).

The pinned IO README identifies the [published generator v0.0.4](https://gitlab.com/Chips4Makers/c4m-pdk-ihpsg13g2/-/tree/v0.0.4),
but also documents the later 18 June 2026 layout/CDL changes and regenerated
CDL/SPICE. The exact old generator commit is
`03db2a692d3969b29128c15b0ec02c6ff605087f`, with its own IHP dependency
`b749a799daa0eba693a4ea3b2b4e65be9ffb322f`, not the installed PDK
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`.

Read-only AST inspection of its exact flexio dependency
`1072d3240273f8ef43486a40712ca264687bb05b` proves that
`_LevelUpInv._create_circuit` explicitly instantiates eight MOS devices and
connects all four NMOS bulk terminals directly to VSS. The current pinned
CDL instead contains eight MOS plus `XR0 vss sub! ptap1 A=1.051p P=4.1u`;
the NMOS bodies connect to `sub!`. Using the old generator as a replacement
would remove an explicit substrate resistor and change that circuit boundary.
It is not an equivalent strict-LVS reference or a source-only A/P repair.
No downloaded generator code was imported, installed, or executed.

The installed `.spi` and `.spice` files are byte-identical. The VACASK view
explicitly identifies itself as converted from the ngspice PDK view and gives
electrical R values, not independent physical A/P values. It contains 65 tap
records rather than the CDL's previously audited 63; whole-library equivalence
was not established. Neither this count difference nor a conversion of R into
an assumed square supplies the missing source geometry intent.

| Check | Result |
|---|---|
| Exact generator/dependency commits and selected source hashes | Passed |
| Eight explicit generator MOS and direct VSS bulk connections | Passed |
| Current nine-device LevelUp source and separate `sub!` node | Passed |
| Installed SPI/SPICE byte equality | Passed |
| Original audit assertion that VACASK also had 63 taps | Failed; preserved r1, actual count 65 |
| Corrected read-only audit with actual 65-record inventory | Passed, r2 |
| Old generator as equivalent current reference | Failed: substrate circuit differs |
| VACASK as independent physical A/P source | Failed: electrical R-only conversion |
| Consistent independently sourced current native IO reference | Not run; none established |
| New LVS, generator execution, repin, source/model/deck/layout changes | Not run |
| Analog simulator/seed | Not applicable |

The [portable audit](upstream-evidence-20260923-r1/r2/summary.json) contains exact
source hashes, AST line locations, original current source records, and all
65 VACASK tap records. The [manifest](upstream-evidence-20260923-r1/manifest.json)
binds original/exported bytes and retains the original failed assertion.
The failed assertion was recovered into a separate receipt because it occurred
before that first audit created an output directory; it is not a successful run.

Required next authority remains an independently documented, mutually
consistent IO source/native revision or an explicitly reviewed source-interface
correction with intended tap geometry and substrate semantics. Copying native
extraction A/P into the golden source, deleting taps, or relaxing comparison
would not establish that consistency. No upstream message was sent.
