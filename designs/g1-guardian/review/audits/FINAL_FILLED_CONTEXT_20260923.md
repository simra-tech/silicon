# Final filled routing context — 2026-09-23

The final filled candidate passes stock antenna and its six critical analog
routes pass direct native-GDS centerline coverage. A selected VREF/oscillator
clock midpoint clip passes paired extraction, independent capacitor-network
checks and the existing transverse-context criterion. These are scoped results,
not fullchip LVS, whole-route RC or electrical acceptance.

The companion [fill review](sense_power_interface/FINAL_FILL_REVIEW_20260923.md)
records density passing with zero markers and the unchanged **60 main / four
maximal pad violations**. Those absolute failures remain unwaived.

## Built against

| Item | Identity / evidence |
| --- | --- |
| Filled native GDS | `4d3907c50f07946ef27a6d53402cf319264499a21379d2de80e9c4f1adbae299`; unchanged throughout these checks |
| Detailed DEF | `348dba8bc4db2f4aeefb9233f7aa5fb60512e7132963628dce7df5a0bfb2b612`; zero-marker router output |
| IHP SG13G2 | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; unchanged pinned runtime/decks |
| KLayout | `0.30.9`; runtime assertions and antenna version output |
| KPEX / ngspice | `0.3.12` / `46` in the previously identity-verified immutable runtime; one thread per process |
| Image manifest | `5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0` |

## Check disposition

| Check | Status | Scope |
| --- | --- | --- |
| Filled stock antenna | Passed | Zero markers, 128.716 s wrapper; input and rule hashes held |
| Original top annotation diagnosis | Passed | All 22 expected external labels already present at audited physical ports; no labels changed |
| Initial strict DEF parser | Failed, retained | It supported `USE SIGNAL` but rejected the real serial-clock `USE CLOCK` record before geometry work |
| Corrected DEF inventory | Passed | All 68 NETS records, 57 routed nets, 424 segments; endpoint extensions, 35 RECT patches and via records retained separately |
| Parser positive/rejection tests | Passed | Five test methods; coordinate inheritance, patches, vias, clock use, count/duplicate and unsupported-token rejection |
| Final critical-route geometry | Passed | All 42 segments across SENSE P/N, ISENSE, IPTAT, VREF and buffered VREF; 22.982 s wrapper |
| Local clip preparation/extraction | Passed | Exact saved metal/via polygon XOR at 12/24/48 µm context, actual-fill and no-fill variants |
| Independent capacitor-network AC | Passed | All 24 checks; original absolute matrix-entry comparison threshold `1e-25 F` |
| Transverse context | Passed | Existing every-entry 1% relative criterion from 24 to 48 µm; maximum `5.7297115061e-6` relative |
| Full device-aware LVS | Failed on the unfilled source; not run anew here | Separate original deep mismatch and flat extraction timeout remain unresolved |
| Whole-route / longitudinal convergence | Not run | A 20 µm midpoint does not represent endpoints, branches or outside-clip connectivity |
| Actual-source electrical coupling and complete RC | Not run | No source/load, switching response, current-capacity or accuracy claim from this network check |
| Stochastic seed | Not applicable | Deterministic geometric and capacitor-network checks |

The exact parser inventory identifies 289 same/adjacent-layer parallel
centerline overlaps within 20 µm of six critical analog nets. This is a
geometric candidate list, not a ranking by coupling and not complete crossing,
via or macro-internal coverage. Actual widths are sampled separately; one
VREF sample hits the sampling-window limit, so no whole-net resistance is
claimed from its partial geometric square estimate.

## Selected VREF / clock context

The current VREF route and oscillator clock share a Metal3 horizontal interval
from x=760.32 to 936.00 µm, at y=947.52 and 947.94 µm. Their centerline
separation is 0.42 µm and overlap is 175.68 µm. The extracted clip is only the
central 20 µm. Earlier-layout interface coordinates and results do not transfer
to this new geometry.

At 48 µm transverse context, the simulated two-port capacitance matrices in fF
are:

| Boundary | Cpp | Cpn = Cnp | Cnn |
| --- | ---: | ---: | ---: |
| No fill | 8.757273778 | −4.306170000 | 5.074831574 |
| Actual metal fill, grounded | 9.290416086 | −4.306170000 | 6.149552140 |
| Actual metal fill, floating | 9.250291875 | −4.373010675 | 5.970731305 |

Other clipped conductors and substrate are explicitly grounded in this
diagnostic. “Floating” means zero small-signal net charge, not a leakage model.
Active/poly fill, devices and below-M1 geometry are excluded and their omitted
fill areas are recorded. These matrices must not simply be multiplied by the
full-route/clip length ratio or adopted as a full physical capacitance model.

The 24 µm run took 20.880 s including launch overhead; the sequential 12/48 µm
runs took 36.868 s. Numeric graph agreement and transverse convergence do not
establish the existing total threshold, temperature-error or power targets.

## Reproduction and evidence

[Portable evidence](final-filled-context-evidence-20260923-r1/export_manifest.json)
binds original/exported hashes, commands, source snapshots, extraction logs,
capacitor networks, matrices and independent checks. Host-path tokens are
declared projections only. Full native GDS is not redundantly repackaged.

The public helpers are [route inventory](final_route_context/route_inventory.py),
[GDS audit](final_route_context/audit_geometry.py),
[clip preparation](final_route_context/prepare_clip.py) and
[context checker](final_route_context/check_context.py). Clip preparation
feeds the unchanged `run_fill_clip_pex.py`, `analyze_interface_clip.py` and
`check_fill_clip_ac.py`; all eight expected AC decks are required per width.
No geometry, PDK model or rule deck was modified by this milestone.
