# Remaining source-bound macro power feeds

The remaining-power inventory r2 passed 135 macro/pad source-PNL-to-OpenDB
bindings. Its inherited full-signal observation report still fails eight
analog-pad alias merges; the inventory does not relabel that result. A separate
native conductor audit r2 passed 21 prospective access points on 13 supply
terminals using physical metal/via connectivity, without text-based joins.
Point ownership is not an array-landing or current-capacity proof.

| Block/pin | Actual source net | Existing simulated current evidence | Qualified final envelope |
|---|---|---|---|
| BGR vdd/vss | VDDA/VSS | Source-held nominal VDDA 319.692 µA, VSS 315.558 µA | Not run |
| TRIP IOVDD/VDD/VSS | VDDA/VDD/VSS | Historical sampled VDDA peak 6.32035 mA; VDD 1.81295 mA | Not run |
| T2F vdd/vdd12/vss | VDDA/VDD/VSS | Selected final586 combined VDDA peak 1.61061 mA; VDD12 0.612802 mA | Not run |
| OSC VDD/VSS | VDD/VSS | OSC mean 110.682 µA, sampled peak 400.665 µA | Not run |
| GATE vdda/vdd/vss | VDDA/VDD/VSS | Historical sampled VDDA peak 1.50611 mA; VDD 0.684049 mA | Not run |

Historical TRIP/GATE figures use the old nominal integrated fixture, not an
updated source/PVT envelope or internal branch partition. The final586 T2F
rounded scalar VDDA means at −40/25/100/125°C are approximately
280.933/358.754/447.259/476.385 µA, but include BGR: adding a separate BGR
current would double-count it. Corresponding T2F VDD12 means are
0.190271/0.242597/0.305935/0.329860 µA. These are fout-rise8-to24 means, not
peak/RMS values or separate T2F analog-rail current.

Evidence-availability correction: an earlier worker statement that the
13-column final586 waves omitted current was incorrect. Both rail currents
are present. The subsequent read-only report
`t2f586-selected-supply-currents-20260923.json` (SHA256
`e1bf23b86f0f67f3bb72315c077cbd16800781503fba8915deff39b1b8f245f0`)
contains 19 completed waves from 21 attempts; the two watchdog failures remain
explicitly not run for statistics. Selected sampled maxima are 1.61060663 mA
combined VDDA and 0.612802405 mA T2F VDD12. These are ideal-rail fixture
observations, not isolated T2F analog current, complete corners or continuous
peak/current-capacity bounds. Original reports are preserved.

The OSC fixture's separate immediate clock receiver peak of 20.517 mA is not
OSC macro current and does not cover the complete digital load. No VSS
current partition is inferred from VDD. Shared VDDA trunk, core ring, pad,
wire, bond and package capacity remain independent unresolved gates.

## Implemented candidate progress

The following paragraphs retain the chronological scope of each partial
build. Later shared-bus and west-extension candidates supersede the earlier
unpowered-handoff state only when the root's combined-native integration
also passes; these isolated reports are not full-chip power signoff.

BGR r1 and r2 native screens failed before GDS write and remain preserved.
BGR r3 source-held additive overlay passed native/r4-PDN clearance, exact
native polygon/text preservation and physical connectivity in 58.861 s.
Its VDDA handoff remains unpowered; VSS reaches the root VSS ring. Overlay
SHA256 is `a164d870d685b91877f23ddcf5d9d7aeb725c60b7f54c330d4c3b0e04d1c269b`.
The 1.10 µm M5 dogleg is an explicit narrowing within the approved 1 mA
exploratory target, not a rule waiver.

Isolated BGR stock DRC passed with zero markers. All ten individual via-cut
removals retained connectivity; conditional via-only capacities are 2.8 mA
at the engineering half-table target and 2.1 mA after the worst one-cut loss.
The new M5 bridge's arithmetic target is lower, 1.10 mA. Actual distribution,
all internal necks, current crowding and lifetime remain unqualified.
The complete candidate core main DRC passed with zero markers in 96.716 s;
maximal DRC also passed with zero markers, total wrapper342.756 s. Frozen signal-route and SENSE feed overlays passed
conservative metal/cut interaction checks in 8.744 s. Root integration is
passed separately for the BGR ground connection; VDDA remains unpowered.

OSC construction passed41.105 s under the separate frozen
[OSC contract](OSC_INTERFACE_CONTRACT.md), isolated stock and56cut-open gates
passed21.219 s, and core main/maximal passed0/0 in425.089 s. Exact oldsignal,
SENSE and BGR overlay context passed8.379 s. These remain isolated proofs;
the root owns actual full-native integration and final signal routing.
The [BGR contract](BGR_INTERFACE_CONTRACT.md) records exact
reserved coordinates, rejected alternatives and current-limit scope.

T2F partial core-rail construction passed56.306 s, isolated stock plus56cut
opens passed18.634 s, and full candidate core main/maximal passed0/0 in
381.098 s. Its native M4 source landing conflicts with the older signal route
SHA03473e0d at x1043.42–1043.62/y1046.95–1048.25:0.260 µm² overlap. That
context check remains failed; future rerouting is not a waiver. Actual final
post-route clearance is required. VDDA remains separate and unpowered.

T2F also fails the newer intermediate signal route SHA38d70806 with
0.220 µm² M4 overlap. Both failures are retained pending actual rerouting.

GATE partial core-rail construction passed58.402 s, isolated stock plus all
56 cut-open checks passed18.900 s, and core main/maximal passed0/0 in357.400 s.
The intermediate38d70806 signal context failed:0.480 µm² M4 overlap and
0.10545 µm² new-Via3 capture of a foreign signal. Neither partial candidate
qualifies full return current or analog-rail distribution. No obsolete-route
failure is waived by a proposed future reroute.

## Conditional shared-pad collector diagnostic

The native pad head has nine 176 µm M2 rails (total width13.57 µm), a 1 µm
M2 header, 60 individual Via2 cuts and a 0.29 µm M3 collector. A finite-resistance
ladder used those dimensions, without assuming equal rail/cut currents.
For a provisional10 mA total pad load, the native collector failed all six
cases (two feed centers times three paired tabulated resistance scenarios).
A proposed6 µm collector passed that conditional model and each of its60
individual cut-loss cases. At feed center393.49 µm, baseline worst Via2
utilization was0.875 of the engineering half-table target. Off-center387.3 µm
reached5.321 mA in the collector against a6 mA arithmetic target.

This is not complete pad-current qualification. The 10.2 µm feed window and
nine lower rail ends were ideal voltage boundaries; lower-stack distribution,
2D spreading/crowding, feed-window voltage gradients, load partition and hot
EM remain not run. The three paired sheet/via resistance scenarios are not
all independent extrema. The proposed collector's physical clearance and
stock legality require separate checks. Existing narrow SENSE routing remains
a branch and must never carry the aggregate in series.

Subsequent straight geometry screens r1–r4 failed actual TM1 ring or staggered
lower-PDN landing interactions. The full-width stepped M3 alternative passed
the native-only screen, then exact saved additive/native-text and flattened
scoped domain checks in159.130 s. Its10 µm collector and392.04 µm feed center
were independently checked: all three paired-resistance head cases and180
individual Via2-loss trials passed, worst baseline Via2 utilization0.871689.
None of this removes the full-pad lower-stack/2D/current qualification gaps.

DUT and DOSE VSS-only builds passed62.481/60.989 s. Each isolated stock and
all28 new-cut-loss checks passed22.573/22.486 s. Candidate core main/maximal
checks passed0/0 in366.523/362.414 s; final signal-context checks remain not run.
Reporting correction: their original
generic build metadata inherited a1.1 mA `minimum_new_bridge_half_table_mA`
scalar although these candidates add no bridge, only local stacks/landings.
That scalar is not applicable and supplies no wire-capacity evidence; original
metadata is preserved. The corrected generator emits null for VSS-only feeds.
The independent checks used actual via graphs, not that unused scalar.

Shared VDDA isolated stock and all148 new-cut removals passed21.302 s. The
initial exact native-context pair hit240 s watchdogs without final reports;
both failures are retained. One matched600 s recovery completed in
347.875/318.929 s. Baseline and candidate each retain exactly60 Pad.fR markers
(24 TM1/36 TM2), with zero added/removed category/cell/value records. The
relative comparison passes; absolute stock acceptance remains failed.

An independent native metallic-R diagnostic includes the complete pad metal
net and new feed, not just the nine-rail ladder. All2194 cuts were individually
bound to cross-layer resistor edges. Under a10 mA point-source/sink and the
pinned LEF resistance scenario, simulated linear drop is43.4702 mV
(4.347015 Ω); every cut is below the engineering half-table target, worst
TopVia1 at0.626781/0.7 mA. This excludes the existing parallel SENSE branch,
device/ESD loads, bond/package and source-boundary convergence. Wire-section
capacity, cut-loss redistribution, PVT/current crowding and lifetime are not
qualified by this result. The12 analytic single/parallel-via controls passed
before the native solve, including actual top-via cut dimensions.

Exact saved-network replay then passed418 selected single-cut-loss cases in
32.794 s, including every new cut and the native head Via2, Via3, Via4 and
top-via cuts. Worst remaining-cut utilization was0.960787 of the declared
half-table target; ten actual M2 cross-sections at x1150 µm reached0.745800.
Worst linear drop was45.3081 mV. The other1776 cut-loss cases were not run.
These conditional point-boundary results do not qualify all wire cross-sections,
crowding, boundary/mesh convergence, actual load partition, temperature or lifetime.

## Remaining corridor decisions

The three-instance LS revision2 passed source-held saved geometry and flat
connectivity in74.979 s, isolated stock and all74 new-cut-loss checks in21.579 s,
and core main/maximal0/0 in360.559 s. Nine distinct initial supply components
became exactly the intended three domains; its shared VDDA handoff remains
unpowered pending the separate west extension. Revision1's actual-PDN
clearance failure remains preserved. See [LS contract](LS_INTERFACE_CONTRACT.md).

The subsequent west extension passed saved-native construction, isolated
stock/all46 cut losses and core main/maximal0/0 in383.498 s. It joins the
three LS analog feeds and GATE VDDA to the shared-bus handoff while passing
below the SENSE VSS flyover on TM1, with no cut at that crossing. Actual
combined-native root integration remains a separate gate.

- TRIP's distributed external headers passed the corrected native geometry
  screen and saved additive/flat graph checks. The 450-cut overlay passed
  isolated stock DRC and every cut-loss check in30.760 s. Core main/maximal
  passed0/0 in419.950 s. The exploratory targets2/8/9 mA for VDD/VDDA/VSS are not actual
  internal partitions. Native0.6 µm M4 rails and lower accesses remain a
  separate required remedy. A source-held DAC bypass build preserves80
  source access points and the unchanged source reference. Strict source LVS
  passed, but main DRC failed two metal-gap and43 fill-spacing markers;
  maximal was not run after failure. That internal geometry is not qualified
  for integration. Comparator/VSS access and contact currents remain
  unresolved; no external parallel-stack pass qualifies them.
- T2F VDDA's M3 escape at x1048 crosses the existing VDD12 M4 feed without
  a cut, then reaches TM2 below the north core-VDD ring. Native screen and
  saved additive/flat graph checks passed; the30-cut isolated overlay passed
  stock DRC and all cut losses in22.028 s. Core main/maximal passed0/0 in
  408.970 s; final combined-native integration remains pending.
  Its1 mA target is exploratory, not a qualified
  source or return-current bound.
- A proposed shared VDDA TM2 axis at x1060 must have no via stack across the
  core VDD TM1 side ring x1054.42–1069.42. The completed shared geometry
  physically joins same-VDDA SENSE routing at x1048, but the SENSE-only leaf
  is not the series aggregate path. A provisional10mA total-pad layout target is
  authorized as an engineering assumption, not an operating/worst-case bound.
  Native pad wire and cut proof must precede acceptance; the existing12mA
  half-table via-only minimum does not establish wire/current-sharing margin.
- All further screens must use actual r4 lower PDN landings, not just spine
  axes. An earlier root SENSE merge failed because a lower VDD landing touched
  SENSE's M3 VDDA bridge; that failure is retained and root r4 relocated two
  feeders. SENSE's later exact full-native merge passed separately.

No primitive, source model, rule deck or logical port is changed. Full-chip
LVS, complete field PEX, IR/EM, final current qualification and adoption are
not run for these new feed candidates.
