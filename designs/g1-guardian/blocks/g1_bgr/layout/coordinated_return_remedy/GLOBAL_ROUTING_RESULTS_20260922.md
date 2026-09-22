# Source586 global routing: bounded physical remedy

The selected candidate passes stock DRC, strict LVS, all 336 MOS junction-field
checks, the complete 55-net metallic graph and seven star-separation checks.
Its simulated fixed-current metallic drops improve substantially. This is
**not nonlinear circuit qualification, complete IR/CC qualification or adoption**.

Final candidate: `bgr-assembly-signalbypass-20260922-r1/bank.gds`, SHA256
`6d86b9d40333958cb8186d486d29db1532a816e302871e11d07e0f1d999cfc04`.
Unchanged source CDL SHA256:
`7f8e6e8c606b1e04321c5c9b20e94610d34d42055c8818d03d79352b3a4710b2`.
All original 1036 devices, source parameters, native placement/centroids,
recognition text, hierarchy, nine M3 port markers and 420-by-354 um bounds
remain unchanged. No TopMetal1 or TopMetal2 is added or changed.

## Built against and scope

| Item | Established pin |
| --- | --- |
| IHP open PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, runtime COMMIT / unchanged stock-rule hashes |
| KLayout | 0.30.9, runtime API |
| R engine | Installed `klayout.pex.RNetExtractor`, SHA256 `99e5f8d32fbebe4e72c97c40d4190800f698cc93164251ef0d6b14e26ca5c3fb` |
| Source586 | `586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b` |
| Source-bound nominal current ledger | `2fee5fa86dd88c4d0c7b89a8a994ce406b7e0508f5853da7400d7d952eb32827` |
| Model-card changes / new analog simulation | Not run; models and canonical electrical source unchanged |
| Random seed | Not applicable to deterministic geometry and linear fixed-current solves |

The exact metallic boundary, separate LEF/KPEX resistance tables and unresolved
native-contact/compact-model ownership remain those in
[the metallic contract](METALLIZATION_R_CONTRACT_20260922.md).
The original 3355 point positions, source-terminal identities and nominal
currents, and all 55 net-reference definitions are exactly preserved in each
comparison. Geometry changes deliberately; engine, solver and resistance tables
do not. Component identifiers are recomputed rather than treated as net names.

## Changes and retained failures

1. `globalwide-r1`: widened the general ground collector, east M5 ground trunk,
   M4 VDD trunk and M3 VDD link. Stock LVS/AP passed; DRC **failed** two M3.e
   markers because the long VDD link had 0.21 um spacing, below the 0.24 um rule.
2. `globalwide-r2`: changed only that link from 0.48 to 0.40 um width, leaving
   0.25 um spacing. Stock DRC/LVS/AP and both fixed-current scenarios passed.
3. `globalrails-r1`: further widened the general collector and four existing
   M2 return columns; enlarged four east ground via interfaces from two to
   eight cuts; added a parallel M5 VDD bridge with M4 access and redundant
   vias; slightly widened the precision rail upward. Its first read-only
   precision-rail proposal **failed** clearance near one signal landing;
   the implemented upper edge retreats to 16.85 um. All stock and numerical
   gates passed on the implemented candidate.
4. `signalbypass-r1`: added only c2/VBE M5 bypasses and their M4/Via4 access,
   and widened those existing MOS-side M4 columns. The first read-only proposal
   **failed** two clearances. The implemented revision doglegs the VBE east
   riser around supply landings and narrows the c2 escape. Its 41 proposed
   shapes passed exact-net and mutual-added-net preflight checks before build.
   Native/source/port and stock/numerical gates then passed.

No failed candidate or preflight is erased. Intermediate GDS files remain
hash-bound in the export manifest; the compact public package carries the
final native GDS and frozen intermediate generators/audits.

| Final candidate check | Status | Result |
| --- | --- | --- |
| Exact additive layer ledger / all other-layer XOR / native text and hierarchy | Passed | No original polygons removed |
| Source, placement, nine port markers and macro bounds | Passed | Unchanged |
| Full source-node graph / seven star cuts | Passed | 55 source nets, no new joins |
| Stock DRC, density disabled | Passed | Zero violations, 35.836 s |
| Strict stock LVS | Passed | 32 combined devices / 24 nets / nine pins, all Match, 6.412 s |
| Independent source MOS W/L/AP/node audit | Passed | 336 MOS, 20 combined groups |
| TopMetal1/2 relocation | Not applicable | Neither changed nor used by the remedy |
| Density / antenna / new whole-core verification | Not run here | Separate integration gates |

## Fixed-current comparison

All values below are simulated linear diagnostic values, not measured silicon.
The starting point is the previously stock-qualified precision-stem candidate
`71892e43...`, not an ideal zero-resistance circuit.

| Quantity | KPEX before | KPEX final | LEF before | LEF final |
| --- | ---: | ---: | ---: | ---: |
| Maximum VSS rise from actual macro pin | 37.5455 mV | 9.6247 mV | 51.8405 mV | 14.6884 mV |
| Maximum VDD drop from actual macro pin | 25.4831 mV | 7.5913 mV | 31.5553 mV | 9.8514 mV |
| VBE terminal voltage span | 24.7046 mV | 9.4087 mV | 33.1714 mV | 13.0349 mV |
| c2 terminal voltage span | 23.7005 mV | 8.6440 mV | 31.7933 mV | 11.9376 mV |
| Total fixed-current metallic power | 32.7504 uW | 15.5585 uW | 43.6280 uW | 21.4077 uW |

The final unpruned network has 39937 nodes, 49142 edges and 6287 explicitly
retained/contracted exact-zero edges. All 3355 points and 55 connected components
are present. Both independent saved-edge audits passed: maximum free-node KCL
residual is 5.883e-15 A for KPEX and 4.826e-15 A for LEF; compensated edge/source
power sums agree. Final bounded launcher durations are 4.843 and 4.917 s.
Full leaves were limited to 600 s plus five seconds grace, one CPU and two GiB
output. Memory was reserved, not claimed cgroup-enforced. Fresh resource gates
and unchanged-input receipts are retained.

This is not a zero-drop result. For example, pcasc still spans 20.5801 mV under
KPEX values and 26.7688 mV under LEF values; those routes were outside the final
two-net screen. No acceptance threshold or circuit improvement is inferred from
lower linear drops alone. Additional metal changes electrostatic coupling;
the full resistor-field CC completeness blocker has not been resolved.

## Exactness control, separately classified

Comparing the earlier KPEX precision-stem r1/r2 extractions after exact-zero
contraction passes node-signature, zero-group, positive-topology, point-map
and count checks, but **fails binary64 resistance equality on six edges**.
The maximum difference is 2.220446049250313e-16 ohm. No exact-replay waiver or
proven cause is asserted. The original failed LEF raw network was separately
replayed byte-identically through the refined solver, without a new extraction:
it passed the original numerical gates and independent audit. Its terminal
values differ from the regenerated refined result by at most 1.0843e-19 V.

## Reproduction and remaining gates

Run with the pinned server-side runtime, a fresh resource-gate JSON,
`G1_RESULTS_ROOT` set to a writable results directory, and one assigned CPU.
For the final build, the frozen preflight JSON is an input, not a new routing
decision. Representative final commands are:

```sh
G1_CPUS=1 G1_CPUSET=1 G1_MEMORY=4g flow/run.sh timeout --kill-after=5 180 python3 designs/g1-guardian/blocks/g1_bgr/layout/coordinated_return_remedy/build_signal_bypass.py --output "$G1_RESULTS_ROOT/bgr-assembly-signalbypass-20260922-r1" --resource-gate "$RESOURCE_GATE" --preflight "$G1_RESULTS_ROOT/bgr-signal-bypass-preflight-20260922-r2.json"
G1_CPUS=1 G1_CPUSET=1 G1_MEMORY=4g flow/run.sh python3 designs/g1-guardian/blocks/g1_bgr/layout/coordinated_full_closure/run_stock.py --candidate bgr-assembly-signalbypass-20260922-r1 --kind drc --resource-gate "$RESOURCE_GATE"
G1_CPUS=1 G1_CPUSET=0 G1_MEMORY=4g flow/run.sh python3 designs/g1-guardian/blocks/g1_bgr/layout/coordinated_full_closure/run_stock.py --candidate bgr-assembly-signalbypass-20260922-r1 --kind lvs --resource-gate "$RESOURCE_GATE"
```

The launcher-recorded stock/extraction commands and frozen preparation,
independent-audit and comparison scripts are retained with their input hashes under
`evidence/globalrouting-20260922-r1/`. The manifest distinguishes original
and host-normalized export hashes; no host-specific path is required publicly.

| Remaining check | Status |
| --- | --- |
| Complete native-electrode/contact/model ownership | Not run / not qualified |
| Finite substrate/well resistance | Not run |
| Complete resistor-field capacitance | Failed, retained prior audit |
| Nonlinear metallic network insertion / OP / stability / transient | Not run |
| New calibration / PVT / mismatch / lifetime qualification | Not run |
| Canonical electrical adoption / tapeout signoff | Not run |

The separate [nonlinear diagnostic contract](NONLINEAR_METALLIC_DIAGNOSTIC_CONTRACT_20260922.md)
is preparation only. It explicitly requires disposition of possible native
electrode double counting and of historical capacitor landing points before
any corresponding electrical qualification claim.
