# Native integrated-prefix diagnostic

The ngspice47 ARM64 pilot `stream_20260921T225435Z_82a34598` timed out at
180.014s after3.085294µs of its required4µs. Numerical completion and native
qualification are **not run to completion**. Source, model cards, included
netlists and RTL match the archived legacy reference; architecture-specific
OSDI binaries and simulator/runtime differ as recorded in the manifests.

`native_prefix_contract_20260921.json` declares endpoint,1mV maximum analog
comparison and1ns digital-edge agreement before launch. A separate
`native_prefix_endpoint_followup_20260921.json` allows a new360s endpoint
attempt based on measured progress; electrical limits remain unchanged.

The first incomplete assessment incorrectly computed differences beyond the
candidate's observed endpoint by clamping its last value. Its large reported
analog differences and edge-count mismatch are **not valid runtime parity
measurements**. The original JSON remains, with this disposition. Corrected
`native_prefix_incomplete_20260921_r2.json` rejects the incomplete endpoint
before comparing waveforms. Diagnostic interpolation over the common observed
prefix alone has maximum analog discrepancy393nV across the declared vectors;
that partial-prefix result does not qualify the missing endpoint.

The follow-up `stream_20260921T225954Z_51cc3ec6` also timed out, at360.041s
after3.326902µs. Its endpoint comparison remains not run; the failed
qualification assessment is `native_prefix_followup_incomplete_20260921.json`.
This ladder is stopped. Runtime under concurrent workloads varied substantially;
neither attempt establishes a speedup. The legacy runtime remains selected for
integrated anchors. No general native-runtime or full fault-response qualification
follows from these startup pilots; the separately qualified native T2F scope is
unchanged.
