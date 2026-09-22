# BGR source586: precision-stem and conditional metallic resistance

This is simulated linear, fixed-current metallization evidence, not measured
silicon, complete IR qualification, nonlinear electrical qualification, or
adoption. Canonical source586 and its 1036 compact-model devices are unchanged.
The separate resistor-field capacitance completeness failure remains open.

## Built against

| Item | Pin / establishment |
| --- | --- |
| IHP open PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, runtime COMMIT and bound decks |
| KLayout | 0.30.9, runtime API version |
| Native resistance engine | `klayout.pex.RNetExtractor`, installed binary SHA256 `99e5f8d32fbebe4e72c97c40d4190800f698cc93164251ef0d6b14e26ca5c3fb` |
| Source | SHA256 `586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b` |
| Nominal external-current ledger | SHA256 `2fee5fa86dd88c4d0c7b89a8a994ce406b7e0508f5853da7400d7d952eb32827` |
| Random seed | Not applicable to deterministic geometry / linear solves |

## Geometry milestone

The precision-stem candidate retains all 1036 native devices, placement,
hierarchy, recognition text, source CDL, nine ports and 55 source nets.
Two Via2 interfaces centered at (16,15.06) and (16,16.26) micrometres change
from two to four physical cuts each, and their connecting M2 stem widens
from 0.30 to 0.72 micrometres. Coincident hierarchical cuts were counted by
physical union, not counted twice.

Candidate GDS SHA256:
`71892e4308000401f857c88eda21c8590dc03c1d7534fecc4851104baec17383`.
Unchanged CDL SHA256:
`7f8e6e8c606b1e04321c5c9b20e94610d34d42055c8818d03d79352b3a4710b2`.

| Check | Status | Evidence |
| --- | --- | --- |
| Exact layer delta, native/text/hierarchy/source/port preservation | Passed | Candidate preparation |
| 55-net graph and seven independently removed star interfaces | Passed | Saved graph / star-cut reports |
| Pinned stock DRC | Passed | Zero violations, 39.697 s |
| Pinned strict stock LVS | Passed | 32 combined devices, 24 nets, nine pins, 8.029 s |
| Independent MOS junction AP/node audit | Passed | All 336 MOS represented by 20 groups |
| Whole-core adoption | Not run here | Coordinator evidence is separate |
| Changed-layout nonlinear electrical qualification | Not run | Source was not replaced |

## Physical access and model boundaries

All 76 selected functional ground-emitter accesses have eight actual Via1
cuts each (608 total). Their native emitter M1 intersects EmWind 33/0, not
generic Cont; a generic Cont resistance is therefore not assigned to this
emitter path. All 24 XR16 ground-side head accesses and the precision rail
were inspected. Their nominal current plus XQ56 current is 198.437498 uA.
After the stem change, its partial drop is 2.018440 mV under LEF values and
0.922073 mV under KPEX values. Including the actual precision rail and head
via stacks gives maximum XR16 partial drops 4.743332 and 3.183165 mV,
respectively. These partial values exclude the general global return.

The pinned R3CMC wrappers already include contact terms (`c1=c2=1`, `rc=rz`)
and the qualified npn13G2 wrapper uses VBIC level 9 with an explicit `re`.
Their calibrated electrode reference planes and native spreading ownership
are not established by an external-current ledger. No model subtraction,
post-layout switch, generic native-contact addition, or compact-model split
is made. Earlier informal HICUM terminology was incorrect for this wrapper.

The direct installed native R request prepares successfully but fails the
full physical-path coverage audit: of 3709 active extracted terminals,
2365 HBT/resistor terminals lack required geometry, 336 MOS body terminals
use unsupported well conductors, and only 1008 MOS S/D/G terminals have
supported geometry. Its preparation is not a successful full R extraction.

## Conditional full metallic network

The separate explicit boundary contract starts at native M1 access points,
preserves all drawn M1–M5 and Via1–Via4 unions, and includes actual macro
M3 pins. It contains 3346 represented source-terminal incidences plus nine
macro pins, 3355 distinct points, and 55 connected components. MOS/HBT body
currents are lumped at existing M1 guard accesses, not propagated through
a qualified well/substrate model. The 399 resistor BN currents are omitted
only because the source-bound nominal ledger infers zero at this operating
point; this is not a general substrate-current assertion.

The current ledger applies common wrapper mappings qualified with 22
representative external probes; it is not 1036 individually metered devices.
Its existing maximum aggregate source-node residual is approximately 1.296 pA.
The same fixed currents are used for both resistance assumptions.

| Assumption | M1 ohm/square | M2–M5 ohm/square | Via1–4 ohm/cut |
| --- | ---: | ---: | ---: |
| Pinned LEF table | 0.135 | 0.103 | 20 |
| Pinned KPEX table | 0.110 | 0.088 | 9 |

These are separate diagnostic scenarios, not a chosen signoff corner.
The native API uses via resistance in ohm-square-micrometres: per-cut value
times the measured 0.19-by-0.19 micrometre cut area. Five analytical controls
per scenario cover three rectangular widths, one via, and two vias including
the actual intervening metal spreading. All ten pass for the final worker.

The full unpruned network has 39803 nodes and 48938 edges; 6218 exact-zero
edges are explicitly contracted to 33585 solve nodes. Original raw edges,
all point mappings and solved voltages are retained. Nine external nets use
their actual macro pin as reference. The other 46 nets have arbitrary voltage
offsets; their spans, not absolute reference values, are meaningful.

| Full r2 result | LEF | KPEX |
| --- | ---: | ---: |
| Maximum nominal VSS rise from actual macro pin | 51.840542 mV | 37.545541 mV |
| Total fixed-current metallic dissipation | 43.628044 uW | 32.750388 uW |
| Independent free-node KCL maximum | 1.857e-14 A | 2.155e-14 A |
| Independent power difference using compensated sums | 0 W | 0 W |
| Bounded launcher duration | 5.198 s | 4.830 s |
| Saved numerical/connectivity audit | Passed | Passed |

The KPEX diagnostic identifies approximately 12.705 mV along the long M3
general-ground collector, 11.852 mV along the east M5 ground trunk, and
12.335 mV along the M3 VDD external link. These support routing improvement;
they do not establish nonlinear circuit behavior with those voltage drops.

## Preserved failures and controls

- Native-request r1: failed before launch due to an incorrect database path;
  corrected r2 preparation passed, physical coverage still failed as above.
- Metallic control r1 and instrumentation-only r2: failed due to a helper
  Laplacian diagonal sign error. Original workers and outputs are preserved.
- KPEX full r1: passed, including independent saved-network audit.
- LEF full r1: failed the prospective relative power gate of 1e-9 (observed
  about 2.9e-9), despite a small nodal residual. No gate was relaxed.
- A fixed three-step, long-double edge-residual numerical refinement was
  added without changing the network, resistance values or source currents.
  All ten analytical controls then passed; both full r2 runs and independent
  edge-current/connectivity/power audits passed the original gates.

The launcher limits full leaves to 600 seconds plus five seconds kill grace,
two GiB output, one CPU and a 16 GiB memory reservation. Actual affinity is
enforced; the memory value is a reservation, not a claimed cgroup limit.

| Remaining check | Status |
| --- | --- |
| Full native contact/electrode/model ownership | Not run / not qualified |
| Finite substrate and well resistance | Not run |
| Resistor-field CC completeness | Failed, prior retained audit |
| Self-consistent nonlinear R-network insertion | Not run |
| PVT, mismatch, transient current and electromigration limits | Not run |
| Whole-layout electrical adoption or tapeout signoff | Not run |
| Random-seed parity for deterministic linear extraction | Not applicable |

Portable evidence and exact reproduction commands are in
`evidence/metallization-20260922-r1/`; the export manifest distinguishes
original and host-normalized hashes and records any bulk artifacts omitted
from the compact export. Canonical source/model/deck bytes are unchanged.
