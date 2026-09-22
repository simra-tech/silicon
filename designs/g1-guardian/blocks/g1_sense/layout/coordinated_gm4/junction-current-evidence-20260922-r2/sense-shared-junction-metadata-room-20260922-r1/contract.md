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
