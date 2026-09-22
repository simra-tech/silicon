# BGR native CC recovery and domain audit

The unchanged installed numerical engine completed with an output-only reporter
adapter: **979 unpruned capacitance entries**, 396.037 s worker time and 411.466 s
bounded-launch time. This is a simulated/extracted diagnostic, not adopted PEX.
Raw `VSUBS` remains unbound in the exact result.

Built against the pinned amd64 image `ddeb69576f28…`, KLayout 0.30.9, KPEX 0.3.12
and IHP PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, established by the prior
runtime identity checks and this run's package/technology hashes. Source586,
all 1036 model records, fixed native geometry and stock decks remain unchanged.
Extraction coverage remains **1027 extracted + nine separately proven grounded
dummy HBTs**, not 1036 extracted devices.

## Recovery and numerical controls

The original representation's 300/900 s timeouts remain failed. The first union
run failed with SIGSEGV at 502.101 s; its last trace was report-shape output.
Observed RSS reached about 4.07 GiB, but no OOM cause was established. Rootless
memory settings were reservations, not enforced limits.

The new reporter retains a valid original RDB container/save but replaces four
diagnostic marker callbacks with counters. Installed result accumulation and all
geometry/math remain untouched. The small 34-HBT control passed all 21 binary64
net-pair/value matches, exact JSON SHA `f65b6a2c…`, and historical rounded-CSV
parity. Original versus adapted runtime was 12.285 versus 6.530 s. The full run
recorded 36,319 overlap, 315,587 sidewall and 888,490 fringe report callbacks.

Raw result SHA: `1d34c6ac28199eee080ca7077071dc71004d7c64eb6b521830ce953f7131533d`.
Its summed entries are approximately 11.233321 pF, including 4.785963 pF incident
on `VSUBS`; these are sums of network elements, not a single effective port C.

The derived diagnostic view replaces exactly the 329 historical `Cext` entries
with all 979 new entries. It preserves every original device/model line, including
all nine grounded HBTs, and retains one self-connected capacitor after the
explicit assumed `VSUBS→generalVSS` mapping. It does not subtract guessed intrinsic
capacitance or change `postsim`, W/L, model cards or source calibration.
Its SHA is `d4ba36a19edee8e4be5be381b95401358acb1a61983f556e6acb3ad48d32086f`.
The old-cap reconstruction is byte-identical source586; the zero-new-C control is
the cap-free 1036-device skeleton, **not** equivalent to original 329-C source586.

## Physical substrate and model scope

Pinned LVS connectivity and property-bound regions establish that `pwell_sub`
(147709.8 µm²), `pwell` (134343.836 µm²) and `ptap` (5024.398 µm²) are exclusively
physical VSS. All 292 extracted HBT substrate terminals, 399 resistor substrate
terminals and 101 NMOS bodies match VSS. The 235 PMOS bodies preserve six separate
nwell/ntap domains: d1–d5 and VDD. The nine dummy physical terminals remain covered
by the earlier independent proof. Thus general VSS is a **node-consistent choice**
for the synthetic reference, not proof of an ideal equipotential substrate plane,
finite substrate resistance, internal HBT `s1`/thermal equivalence or field accuracy.

The contact inventory has 1568.0272 µm² drawn contact area, of which 486.2336 µm²
is in typed contact layers. The remaining 1081.7936 µm² comprises 929.1264 µm² in
taps and 152.6672 µm² uniquely within the 301 pinned HBT footprints (0.5072 µm²
each). This classifies physical ownership, not individual electrical terminals.
The unrecognized emitter-window layer is also retained in the original database.

The installed CC engine's field calculation uses poly/metals plus a synthetic
substrate rectangle; contacts/vias are not independent CC conductor layers.
Consequently complete source/native connectivity is **not** a full material-field
coverage proof. Diffusion/nwell-specific fields, contact/emitter-window fields,
finite return resistance and model/extrinsic ownership still need qualification.

Two process entries reference M5 GDS 67/0. Although raw repeated region count is
15→30, native merged polygon-neighborhood controls passed identically for 15 M5
inside/M4-secondary, 462 M4 inside/M5-secondary and 15 M5 self-neighborhood rows.
No full numerical alternate-engine rerun or engine patch was made.

Blackbox true/false gives zero geometry delta for all 24 present BGR layers. The
pinned rule already derives `poly_con` by excluding resistor markers; therefore
the presence of intrinsic resistor area/perimeter C does **not** demonstrate
whole resistor-body double counting. Access-head/gate and other compact-model
domain ownership remains unqualified; toggling blackboxing is not a demonstrated
remedy. No empirical subtraction is permitted.

| Check | Status |
|---|---|
| Original full 300/900 s attempts | failed: preserved timeouts |
| First full union attempt | failed: preserved SIGSEGV |
| Reporter 21-value exact binary64 control | passed |
| Full 979-entry raw generation / finite values / input hashes | passed |
| Replacement-only / 1036 records / exact-decimal conversion | passed |
| Physical general-VSS substrate-node ownership | passed |
| First substrate-proof parser | failed: preserved wrong resistor terminal-key assumption |
| Corrected source-terminal proof | passed |
| M5 tested merged polygon neighborhoods | passed |
| Full intended material/compact-model domain qualification | not run to completion |
| Finite return/substrate R, current cuts and IR error | not run to completion |
| Diagnostic-view electrical/stability qualification | not run here |
| PEX adoption / signoff | not run |
| Random seed for deterministic geometry/CC checks | not applicable |

## Reproduction

Scripts and completed receipts are in `evidence/cc-recovery-20260922-r1`; the
export manifest maps every original/exported hash and discloses text-only host
prefix redaction. Launch with `run_cc_api.py` using a fresh resource-gate JSON,
results root, single-CPU affinity, `--reporter original` and `count-only` for the
small controls. Run `check_cc_reporter_parity.py`; the full `--full --parity`
launch requires that exact passed receipt and unchanged worker hash. The bounded
full run allows 900 s + 5 s kill grace, 8 GiB unenforced RAM reservation and 2 GiB
external growth. `prepare_native_cc_views.py` requires explicit `--substrate-node
vss` and never overwrites the canonical source. Exact executed commands are in
the launch receipts; the raw/grounded diagnostic views remain non-adopted.
