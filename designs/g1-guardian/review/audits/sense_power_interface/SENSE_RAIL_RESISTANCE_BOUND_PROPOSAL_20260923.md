# Weight-free SENSE metal-rail resistance screen

Completed actual graph bound **passed**, with no physical IR acceptance.
Ten analytic method controls passed. This screen locates a routing resistance bottleneck
without choosing compact-model contact weights, a single physical injection
point, or an equipotential pin polygon. It is not an IR acceptance gate.

## Exact domain

Use the completed all-Cont r8 metal graph: 44,733 reduced nodes, 45,087
positive edges, 134 components, exact source `baab6183...` and GDS
`8060e30a...`. Select the VDD and VSS components by the audited source
observations, not by an arbitrary circuit-local identifier. Bind the exact
nine-port support inventory separately. No geometry/model/card change or
ngspice run is proposed.

This is the existing fixed ordinary-metal/via graph, not a continuous-field
bound. Contact, Poly, Active, substrate, MIM/Vmim and model-owned resistance
remain excluded. A bound for this graph is not an upper bound for omitted
positive physical resistances. Future fullchip attachment/remeshing must be
checked independently.

## Conservative coefficient with no selected current distribution

For a connected passive graph, construct a spanning tree from **actual
positive edges**, removing the other edges. Float shortest-path calculations
may choose the tree, but every reported tree path sum uses exact rational
values of the original binary64 resistances. No fitted edge is introduced.
Its exact resistance diameter `D_tree` bounds every effective resistance in
the original graph from above by Rayleigh monotonicity.

For any complete, balanced injection vector `i`, let
`I_plus = sum(max(i_k, 0)) = sum(abs(i_k))/2`.
Decompose it into nonnegative source/sink pairs. Reciprocity and the
resistance-metric Cauchy inequality give an absolute transfer resistance no
greater than the maximum effective resistance. Consequently:

`max(v) - min(v) <= D_tree * I_plus`.

This includes **all internal and external injections**, with arbitrary signs
and contact allocations at graph vertices. The computational tree root is
not a selected device or supply attachment. A reported “per 1 mA of complete
positive-current budget” coefficient is a unit scaling, not an assumed
operating current. Currents at unrepresented continuum locations and any
subsequent physical network changes are outside this graph statement.

If only internal absolute current `J = sum(abs(j_k))` is known, one may use
`I_plus <= J` **only after** separately establishing that the external feed
is a one-direction return of the internal signed sum, with no additional
circulating-current source. Otherwise the external absolute current needs
its own bound. No such external-feed assumption is accepted here.

## Bottleneck localization and failure meaning

Enumerate bridge cuts in the multigraph, preserving parallel native edges.
For a bridge between two internally connected partitions, the exact parallel
cut resistance `1/sum(1/R_edge)` is a lower bound on graph resistance
diameter. Retain actual edge/node geometry and enumerate which proven contact
supports lie on each side. This gives a concrete narrow connection to inspect,
without assuming that a device's current enters one chosen contact.

A large upper coefficient is **inconclusive**, not a design failure. A large
bridge lower bound proves the existence of a sensitive graph transfer, not
that the actual nonlinear circuit drives that transfer. A layout change is
justified only after source-bound current/cut ownership and physical geometry
identify the offending required path. Main/maximum DRC, strict LVS, intrinsic
ownership, affected field and electrical checks remain required for a change.

## Available current evidence and a specific missing bound

The existing representative room/hot 1.02 us fixtures have separate source
and body observations. Source-ledger inspection shows all VDD-connected MOS
terminals are 21 S and 33 B. Summing their individual sampled absolute maxima
gives 1.115460171 mA at room and 1.509411442 mA at hot. These are conservative
over the **saved samples of those fixtures only**, not startup, continuous
time, PVT, mismatch or physical worst-case bounds. They are not substituted
for a declared complete-current budget.

The VSS data are insufficient even for the corresponding all-terminal
absolute bound: 19 S and 25 B are separate, but the 95 resistor-bank BN
terminals and one resistor endpoint are represented by one **signed
aggregate**. Three OTA resistor BN currents are separate. The sum of
individual peaks plus that aggregate is 1.050769043/1.446727386 mA room/hot,
but cancellation inside the aggregate is unknown. Those numbers are **not**
VSS absolute-current upper bounds. No VSS=VDD equality or uniform resistor
current partition is inferred.

The exact public current summaries are the room/hot records under
`g1_trip/sim/qualification/portable_evidence/sense-rail-terminals-20260922/`,
with SHA256 `6bf83812e322aaf9db504b0b297589ec213dc7dc5a8b9ce309adb9ba9fd24bea`
and `07075e3ec54d5a9967a836a9296316429f3559e8893f8787240dce714724eb4e`, respectively.

## Completed bounded operation

The source-held graph operation completed in 10.745 s including the wrapper
(2.099 s computation). Exact binary64-rational tree diameter coefficients
are 437.9339968393318 ohm VDD and 774.7850249879037 ohm VSS. These are graph
upper coefficients, not predicted voltage drops or a complete physical
resistance bound.

The leading actual bridge edges are four 0.4 um Metal2 source feeders:
XM14/XM11, 214.82 um and 55.31615 ohm each; XM4/XM3, 198.50 um and
51.11375 ohm each. Each isolates all 575/483 proven source contacts of its
one logical device and no other contact/source witness. Their coordinates
and exact cut partitions are retained in the result. This supports a
focused source-held metal remedy without selecting contact current weights.
The isolated remedy has a separate prospective contract; no geometry or
electrical adoption follows from this graph result.

## Original prospective operation (retained)

After review and an explicit runtime lease, one at-most-120-second process
can validate hashes/positive edges/components, compute VDD/VSS tree upper
and bridge lower coefficients, and output at most the leading twenty bridge
geometry records plus counts. Prospective output is below 0.1 GiB. No source
current is injected or compact model connected. Stop on missing nodes,
unbalanced domain interpretation, nonpositive edges, incomplete source
membership or failed analytic controls. No automatic sensitivity campaign,
new numerical coupon or geometry change follows.
