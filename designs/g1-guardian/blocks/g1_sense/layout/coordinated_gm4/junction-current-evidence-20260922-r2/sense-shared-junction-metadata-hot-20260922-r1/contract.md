# Bounded shared-junction applicability diagnostic

Scope is the six canonical PMOS input devices XM1/XM2 in XOTA/XBUF/XREF,
source SHA `baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`.
Cards, compiled OSDI and design geometry remain unchanged. This is a diagnostic
of necessary model conditions, not a new compact model, fitted A/P, source
adoption or electrical acceptance campaign.

Stage1 is one room-temperature, output-only replay of the already qualified
representative monitored OP fixture. It adds saved internal vectors and native
`show` metadata for the six devices, preserving source bytes, solver settings,
seed and the two original OP commands. The complete original printed parameter
sequence and original OP/current/monitor voltage data must be exact. Runtime
is bounded120 s, one CPU7, output≤32 MiB. Warnings remain explicitly inventoried
against the reference. Missing internal voltages/charges are **not run**, never
replaced with external-node or static-current assumptions.

Only after availability and parity pass may a corresponding hot replay run.
An explicit equal-internal-bias/common-model control and a deliberately
different-internal-bias negative control must preserve all canonical model
parameters. Such fixtures may change declared independent bias sources, but
must not tie hidden internal PSP nodes, rewrite junction cards or use stock
averaged A/P. The control implementation and observed vector identities must
be frozen before launch. No automatic statistical sweep, transient expansion
or substitution into the accepted design follows.

Potentially available PSP `vsb` is not assumed to be the junction's SI–BS
voltage; source equations and actual internal-node identities must agree.
Junction capacitance is not silently labelled charge. If charge state is not
exposed by supported interfaces, report that boundary and request direction
on a separately justified observation method.

The existing source-level additivity condition requires common internal
junction voltage, geometry-normalized model coefficients, temperature and
limiting regime. Physical allocation has already passed; this diagnostic
cannot prove silicon truth merely by constructing an arbitrary shared model.
All earlier 51 stock A/P annotation failures and whole-core r6/r7 failures stay
preserved independently.

## Corrective room replay r2

The original room run completed in119.097s with all23078 printed original
values exact, but `.save all` changed the default OP scale from clk0 to
vdda3.3. All17 nonscale physical values were exact; the original full-byte
gate remains **failed**. A new output-only replay may explicitly issue
`setscale v(clk)` before the original three `wrdata` commands. Nothing else
in source, solver, random realization or timeout is changed. The original
120s child limit remains; a timeout does not authorize a watchdog ladder.

Naive raw internal-node interpretation also **failed**: pinned OSDI0.4 has
13descriptor nodes, but RSE/RDE collapse produces11 nodes named by compact
indices in ngspice46. Source-derived reconstruction passed independent
channel-voltage checks at native `show` precision. That is not a live-instance
mapping observation, a charge measurement or an applicability pass. The
corresponding raw-label failure and initially incorrect r1 interpretation
are preserved. No hot replay before the corrective room exact-byte gate.
