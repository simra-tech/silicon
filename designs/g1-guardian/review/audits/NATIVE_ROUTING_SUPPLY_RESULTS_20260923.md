# Native routing, supply integration and fill checkpoint

The 40 nm M5 routing-obstacle halo removes the three new stock M5 spacing
violations. This is **not full-chip DRC closure**: 60 inherited pad markers
remain. Independently checked digital, shared analog, DUT and DOSE feeds now
join their intended native domains in an additive intermediate assembly.
Remaining supply branches, final routing and full device-aware verification
are not complete. No canonical electrical source or PDK rule was changed.

## Built against

| Item | Identity and evidence |
| --- | --- |
| IHP SG13G2 | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; installed COMMIT plus per-file rule hashes before/after |
| KLayout | 0.30.9; runtime Python assertion and stock tool logs |
| OpenROAD | 26Q1-1024, image LibreLane installation; route/import receipts |
| Image manifest | `5fd78498e578c6e9ec10828c248ca3790fc88250ff6caf545521b29e448ea3c0` |
| ngspice | Not applicable to these geometric checks; electrical campaigns recorded separately |

All runs use one CPU. Large native GDS objects remain hash-bound bulk evidence;
the portable evidence includes reconstruction sources, compact overlays,
reports, exact commands and original/exported hashes. Only declared host-path
tokens are normalized. A passing scoped helper is never full-chip signoff.

## Routing and actual terminal binding

The earlier 20 nm obstacle halo still left three 230 nm native-to-route M5
gaps where the stock rule requires 240 nm. Their original 63-marker results
are retained. A 40 nm halo changes routing reservations only, not PDK rules or
native device geometry. Global/detail routing completed with zero router
markers; the saved native streamout is
`bcbd08cd03d2efcd25feacb7a9aef58135e80f743b5c1fa4e94aa2988f862517`.

Its stock main run completed in 338.534 s (327.407 s deck execution), with
24 `Pad.fR_TM1` and 36 `Pad.fR_TM2` markers and no M5 spacing markers.
Exact category/cell/value comparison against the earlier native baseline
passes, with no added or removed pad markers. All 60 remain **failed**, with
no recommended-rule waiver.

A repeated-cell control found that hierarchical `(circuit name, cluster ID)`
keys can alias disconnected instances. The new disposable flattened
metal/cut view holds every polygon exactly and uses no label joining.
Four controls reproduce the original alias error, distinguish disconnected
copies, require an explicit conductor bridge, and require a via for a
cross-layer connection. Existing correct-root decap joins are not invalidated.

R6's actual 10,222-terminal audit completed in 256.544 s. Its raw eight pad
aliases initially report failure; an independent unchanged-library assignment
audit accepts exactly those eight aliases. No off-metal probes, signal splits
or unexpected merges remain. Genuine supply components are VDD 8, VDDA 8,
VSS 9 at this pre-additional-feed snapshot. Complete PDN and device-aware LVS
remain **not run**. Original hierarchy-derived lower supply counts are not
substituted for these instance-resolved observations.

An independent flat-geometry external-port audit passed in 105.773 s: all
22 logical ports and 24 complete physical pad rectangles are covered by actual
metal and connected to their corresponding native bondpad terminals. This
does not imply all supply terminals are joined or device-aware LVS passes.

## Digital and shared-feed integration

Two 2.2 um TM1 extensions and three TV2 cuts each join the published native
digital VDD/VSS rail windows to the corresponding root TM2 rings. Native
functional geometry, texts, instances and saved roundtrip pass; no foreign
contact or VDD/VSS merge is permitted. Candidate core hash:
`e10e6ec241f8deab410bf47219e6a34b5534b8ec38fac910f8bae0c5bbb191b2`.
Its stock main and maximal checks both have zero markers, completing in
439.122 s combined. Six independently removed cuts retain connection; the
ideal-metal via-only half-table capacity is 15 mA nominal and 10 mA after
one cut loss. The 8 mA branch target is prospective sizing, **not an established
current envelope, equal-sharing proof, wire IR, hot EM or lifetime signoff**.
An initial cut-audit import-path failure is retained; corrected r2 passed.

The later additive intermediate assembly combines this overlay with the
independently checked shared VDDA, DUT and DOSE overlays and previous BGR,
OSC, T2F, GATE and SENSE feeds. Hash:
`4e034eda528d4bfa3c00accf1f619fe0569b07471b6bece6697466eb9877a87e`.
The 288.372 s merge passes source-bound foreign-contact checks, saved
geometry/text/4,904-instance preservation and flat actual joining:

- Native digital VDD joins root VDD.
- Digital, DUT and DOSE VSS join root VSS.
- Native BGR, SENSE and the analog supply pad share VDDA.
- VDD, VSS and VDDA remain distinct.

The earlier 9,324 decap pin-pair proof is preserved by unchanged native
geometry and no-foreign-contact checks. The shared overlay's matched native
stock comparison adds no markers but still has the 60 inherited pad failures;
original 240 s watchdog failures are retained separately. New combined-context
stock checks, core-to-IO feeds, remaining macro branches, final signal routing,
all-terminal PDN closure and electrical/current qualification are **not run**
at this checkpoint.

## Sealring, density and antenna: failures retained

The saved additive native sealring assembly preserves all 4,904 native
instances plus the signal-route instance. Its actual 39/4 boundary is
1414 x 1414 um, area 1,999,396 um2. There is no substitution of the old die area
or macro outline. This assembly uses the earlier R5 signals, not R6.

| Check | Status and scoped result |
| --- | --- |
| Sealring additive geometry, text and roundtrip | Passed, 181.204 s |
| R5 sealed stock main | Failed, 60 pad plus three M5 markers |
| R5 sealed maximal | Failed, four unchanged `Pad.d1R`, 769.455 s |
| Unfilled stock density | Failed, 19 markers |
| Unmodified stock fill generation | Passed, 340.277 s; only additive filler changed |
| Stock-filled density | Failed, one `GFil.g`: 14.43% versus 15% minimum; other global/local checks passed |
| R5 sealed antenna | Failed, nine markers: three each M5/TM1/TM2, protected ratio above 20,000 |
| Additional conservative poly-fill r1 | Failed, 480 s watchdog during filtering; no candidate produced |
| Final filled R6 main/maximal/antenna and fill-sensitive extraction | Not run |
| Physical measurement or tape-out acceptance | Not run |
| Model-card/rule-deck modifications | Not applicable; held unchanged |

The stock-filled GDS is
`7cb67330445e1a2e57d7aea5c0d9669d2e3bf61a18c91b873e1c66831b900e61`.
Functional polygons, original filler, texts and original instances are held.
Supplemental fill and antenna remedies require separate saved-layout stock
and electrical checks; no density or antenna failure is waived by this report.

## Reproduction entry points

The [portable milestone evidence](native-routing-supply-evidence-20260923-r1/manifest.json)
binds exact commands, completed receipts, sources and reports. Reconstruction
order is local feed integration, obstacle export, global/detail routing,
native streamout, instance-resolved terminal audit and source-alias audit.
Sealring/fill are explicitly a separate R5 branch. Representative commands:

```sh
python3 export_core_routing_obstacles.py --help
python3 audit_native_terminal_connectivity.py --help
python3 run_core_candidate_drc.py --help
python3 merge_verified_supply_feeds.py --help
python3 run_native_stock_fill.py --help
python3 run_native_aux_checks.py --help
```

Use the recorded immutable inputs and complete receipt arguments, not a
similarly named latest file. Full LVS/PEX/STA/current IR/EM and all affected
final electrical campaigns remain required.
