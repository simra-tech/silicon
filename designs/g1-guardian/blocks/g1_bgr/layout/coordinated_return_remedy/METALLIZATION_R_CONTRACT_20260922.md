# Conditional metallic-network resistance diagnostic

This scope is **not complete physical IR qualification**. It starts at the
source-bound native M1 access locations and ends at the unchanged nine macro
ports. All drawn M1–M5 and Via1–Via4 union geometry is preserved. Native
substrate/well paths, semiconductor/internal contact resistance, calibrated
VBIC `re`, R3CMC `rc`, electrode-reference-plane ownership and device-internal
spreading are outside this domain and remain not qualified.

No generic Cont resistance is added to the compact models. The pinned R3CMC
wrappers already set `c1=c2=1`, `rc=rz`, `postsim=0`; changing that partition
or appending another native-contact resistance is not authorized here.

The prospective preparation checks are exact source586/current-ledger binding,
1036 source IDs, all 3346 geometrically represented terminal accesses, explicit
exclusion of the 399 resistor substrate terminals (all inferred zero only at
this nominal operating point), unique layer/point/net ownership, preservation
of the 55-net metallic connectivity graph and nine macro-port locations, and
zero union XOR for every included conductor/via layer. HBT E is observed on
native M1 at the existing emitter coordinate, including its native eight Via1
cuts above that boundary; its EmWind/semiconductor interface is not assigned
an invented resistance. MOS and HBT body currents enter their existing native
M1 guard-access locations as a conditional lumped boundary, not a substrate
resistance model. Coincident access points are explicitly coalesced with all
source identities and summed currents retained.

The numerical method uses the installed KLayout resistance engine directly,
with its square-counting conductor algorithm and no network simplification.
All network elements are retained; zero-ohm edges, if produced, must be
explicitly coalesced, not discarded. Negative/nonfinite resistance, ambiguous
port ownership, missing ports, new conductive shorts, disconnected current
injections and numerical singularities fail the diagnostic.

Separate LEF and KPEX resistance tables remain separate scenarios; neither is
a process corner or an uncertainty bound. Analytic rectangle and parallel-via
controls precede the first full network. The first full metallic diagnostic
is bounded to 600 seconds on one assigned CPU, with a fresh resource gate and
bulk-output reserve. Actual time/RAM/output growth are recorded. Numerical
KCL, terminal coverage and finite results are reported independently from the
unresolved physical-model boundary.

The injected currents are the nominal 27 °C model-inferred external-port
ledger, not a new nonlinear circuit solution. Internal source nets may retain
the original tiny ledger KCL residual; any balancing/reference current is
reported explicitly rather than hidden. Each of the nine exported nets uses
its actual macro pin as voltage reference. Other net offsets are arbitrary
and must be labelled as such. There is no canonical electrical-source
insertion, recalibration, PVT, transient, lifetime or adoption claim.
