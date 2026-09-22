# Isolated SENSE source-faithful geometry gate

Inherited source-to-physical fidelity is **failed**. This folder holds diagnostic controls and isolated contact prototypes, not adopted layout. The original audits saved no GDS; the subsequent bounded prototype gate generated only a separate candidate GDS, preserving canonical geometry. Exact source is gm4comp3 SHA-256 `baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`; delivered GDS remains `38c1d6d13bbfee4ed0e3c01477742c3d2d28317d9215d9e5bd9a35551285ae59`.

Latest isolated milestone: [complete nine-port SENSE assembly](ASSEMBLY_RESULTS_20260922.md)
passes independent58MOS/835-channel geometry and stock DRC/LVS within385×240µm.
It is unfilled and unadopted. Stock per-node junction attribution fails51/58
records; intrinsic shared PSP applicability, new PEX and whole-chip fit remain
not run. Earlier proposals and failed controls below remain historical evidence.

## Evidence and scope

| Check | Status | Evidence |
|---|---|---|
| Original OTA generator reproduction | Passed: zero nontext polygon XOR on every layer | [Inventory r2](inherited-fidelity-20260922-r2.json) |
| All19 logical MOS W/L/ng, all three source OTA bindings | Failed inherited geometry fidelity | [Inventory r2](inherited-fidelity-20260922-r2.json) |
| Actual gate/drain/source terminal net partition | Passed368 probes,16 source nets, no opens/shorts | [Terminal nets](terminal-nets-20260922-r1.json) |
| Source-native junction geometry versus pinned automatic model defaults | Passed for all38 baseline/candidate logical MOS records | [Junction audit](junction-defaults-20260922-r1.json) |
| Delivered junction geometry versus source defaults | Failed bias devices and aggregate shared input pair | [Junction audit](junction-defaults-20260922-r1.json) |
| Six isolated source-native/contact prototypes | Passed scoped native and terminal gate, including independent saved-GDS repeat | [Prototype manifest](native-prototypes-20260922-r1/manifest.json), [saved-GDS audit](native-saved-audit-20260922-r1.json) |
| Isolated assembly DRC and six strict stock LVS | Passed: zero markers, only Match statuses | [Seven-check stock summary](native-stock-20260922-r1/summary.json) |
| Stock-written per-node junction A/P versus source defaults | Failed for all10 MOS, identically in split and independent controls | [Attribution audit](stock-junction-attribution-20260922-r1.json) |
| New source-faithful routed buffers/main/full SENSE, stock DRC/LVS | Passed isolated scope; new PEX not run | [Assembly results](ASSEMBLY_RESULTS_20260922.md) |
| Whole-chip well/substrate isolation, model matching, extracted electrical performance | Not run | Separate required gates |

The first inventory invocation failed on an omitted PCell origin argument; [r1 failure](inherited-fidelity-20260922-r1-failure.json) is retained. The fresh r2 invocation uses explicit origin(0,0). The independent terminal audit copies polygons into a separate in-memory layout and connects actual channel-subtracted Activ/GatPoly/contact/six-metal geometry. Labels are sampled as terminal anchors, never used to merge nets.

## Exact inherited mismatches

Both XBUF and XREF instantiate the baseline source `g1_ota`; their electrical source is unchanged, but the existing physical cell is not source-finger faithful:

| Device in each OTA | Source W/L/ng (µm) | Delivered W/L/ng (µm) |
|---|---|---|
| MB2, MB6 | 8/1/2 | 8/1/1 |
| MB3, MB5 | 16/1/4 | 16/1/2 |

The inherited main OTA shares these four discrepancies, in addition to the eight intended gm4 device resizes. Existing `spice2cdl.py` explicitly drops `ng`; a total-W/L stock LVS match does not certify these fields.

All OTA MOS omit AS/AD/PS/PD. Pinned unchanged `sg13g2_moshv_mod.lib`, SHA-256 `58ce3084c253f2d3753c3b95386e8f4b81dcadfed4f4503dce56862a556c3328`, defaults these parameters to zero and calculates them using W/ng and z1=.34µm/z2=.38µm. Source-native full rectangular diffusion areas/perimeters match those equations. This is direct geometry/default-parameter evidence, not new simulated performance.

For MB2/MB6 the delivered-minus-source-default changes are AD +1.2µm², PS −.68µm, PD +7.92µm (AS unchanged). For MB3/MB5 they are AS +1.2µm², PS +7.24µm, PD −.76µm (AD unchanged).

The delivered common-centroid pair contains32 gates on one shared Activ chain, with16 gates per logical M1/M2. Its total tail-source diffusion is38.28µm²/216.76µm perimeter, versus40.08µm²/229.36µm from the two independent source defaults: **−1.8µm² and−12.6µm**. Aggregate drains agree. Physical net probing confirms the shared tail strips and individual fn/fp drains. Sharing cannot be hidden by double-counting a physical strip or silently fitting AS/PS in the golden source. Individual shared-source ownership is not uniquely defined; the aggregate mismatch alone establishes failure.

## Proposed next bounded implementation gate

Preserve the exact source and baseline controls. First implement isolated native/contact prototypes for the four corrected bias geometries and an input-pair alternative, with independently copied pre/post polygon snapshots. No full macro or canonical layout change precedes their review.

For MB2/6 use two4µm fingers; for MB3/5 use four4µm fingers. Existing rails at an8µm device-row height require explicit extensions, and every alternating source/drain strip must connect. Changing the generator specification tuples alone is insufficient. Keep native PCells, same W/L, legal gate/diffusion contacts, and source/bulk identities; compare actual W/L/ng and diffusion A/P with the immutable source defaults in addition to stock LVS.

For the pair, two independent complete16-finger native arrays preserve per-device defaults unambiguously, but side-by-side or stacked placement loses the old ABBA common centroid. A segmented ABBA alternative may restore aggregate tail geometry while preserving16 gates per logical device; **aggregate matching is not yet proof of individual model-junction applicability**. Neither alternative is selected or electrically qualified. Matching and default-junction fidelity must be resolved together, without a model-card or source-parameter waiver.

[Split-chain accounting proposal](split-pair-accounting-20260922-r1.json) now makes the second option concrete: two16-finger chains for a buffer, or two64-finger chains at the existing r4 main-pair native reservations. Complementary ABBA/BAAB assignments keep both logical gate centroids coincident in x and y. Every physical source strip is counted once globally; equal allocation between adjacent gate owners reproduces the exact per-logical default A/P, and aggregate node A/P equality does not depend on that allocation. This is a consistent prospective assignment, not intrinsic ownership or established mismatch-model applicability. Buffer Activ gap2.4µm reserves one L2 dummy with0.2µm clearance on each side. Corrected row arithmetic predicts a100.61µm buffer width, +2.76µm versus the inherited bbox; actual contacts, well/guard, terminal mapping, DRC and routed fit are not run.

The r4 local385×240µm SENSE envelope has room to review enlarged buffers: the main reservation ends at y169, the resistor bank begins at x247, and the buffer region can prospectively span x5–235/y175–240. Two approximately≤110×65µm reservations could fit that region with a10µm central gap. This is a geometric budget only; actual new bbox, guard/feed routing and stock spacing must be demonstrated. Earlier97.85×51.2µm buffer reservations are not a source-faithful fit claim.

After native prototypes pass, generate source-derived CDL plus a separate finger/junction/net-membership manifest, then one isolated routed buffer and stock hard/recommended DRC/LVS. Only then extend to gm4 main/SENSE integration, same-source geometry accounting, well/substrate ties, capacitor contacts, feeds and actual ring obstruction. PEX, fill/density, coupling/current, extracted electrical matching and whole-chip retained-PDN legal fit remain not run; no broad MC or adoption follows from these controls.

## Completed isolated native/contact gate

[Builder](build_native_prototypes.py) and [frozen contract](native-prototype-contract-20260922-r1.json) generated bias_n2, bias_p4, complementary split/control16 and split/control64, all in [separate GDS](native-prototypes-20260922-r1/native_prototypes.gds), SHA-256 `dfef42cc9384e44c7ad1d8851d0fd4cfa057ee61b700911859252d3557114db4`. Native snapshots are explicit polygon copies before mutation. Actual channel count/W/L and diffusion polygon A/P match source-native values; native channel XOR is zero after contacts and separately accounted nonzero body-tap additions. Every intended terminal probe maps to one correct physical net, with no opens/shorts. The saved-GDS repeat independently passed all six cells. Per-device shared-junction applicability remains not run.

The pair64 prototype places its two chains side by side and is318.84µm wide including guards: **it does not fit the230µm r4 main-OTA width**. It is an isolated contact/control structure only. The proposed actual main placement instead stacks the two153.86µm native chains in existing r4 rows; complementary half-A/half-B assignment preserves centroid arithmetic under that transform, but new row collectors, contacts/wells/guards and spacing must be proven. Prototype legality is not stacked-macro fit evidence.

[Source-derived references](native-prototype-cdl-20260922-r1/manifest.json) retain all source parameter bytes except the declared standard CDL ng/mm_ok conversion; no extracted netlist was used. [First stock contract](STOCK_PROTOTYPE_CONTRACT_20260922.md) freezes assembly DRC then conditional six strict LVS checks. This first device gate excludes density; density, antenna, full macro and broad PEX are not run. Any stock failure stops that gate, with no warning or tap-reference waiver.

The frozen stock gate completed: assembly DRC zero markers in27.24seconds, then all six LVS checks passed in approximately19.3seconds combined. Every circuit/device/net/pin/subcircuit status was strictly Match. Stock decks, actual live source, GDS and source-CDL bindings were unchanged; output was1.37MB. No tap-disabling flag or extracted-to-golden adjustment was used.

The follow-up [stock-written A/P attribution audit](stock-junction-attribution-20260922-r1.json) **failed for all10 MOS**. After correctly mapping any D/S reversal, split and independent control16 both write19.14µm²/108.38µm to each source/drain node, rather than tail20.04µm²/114.68µm and drain18.24µm²/102.08µm. Split/control64 both write73.86µm²/414.62µm to each node instead of tail74.76/420.92 and drain72.96/408.32. Biasn2 and p4 are also symmetrized. This is a failure of **stock-extracted per-node parameter annotation**, not a reversal of the independently passed physical native/default geometry control. The independent-array control has identical stock-written parameters, so the observation is not split-specific.

[Actual saved class metadata](stock-compare-fields-20260922-r2.json) confirms L/W/rfmode are primary comparison fields, AS/AD/PS/PD are nonprimary, and ng is absent. Therefore even strict Match cannot qualify those junction parameters. The stock writer prints stored values; the observed symmetrization already exists in its saved database. The exact internal extraction-versus-combination step is not yet isolated. Original failed inspection r1 (unused registered opposite-polarity class) is retained separately; r2 distinguishes active from unused classes. No cards/decks or golden values were altered. Source-preserving mapped-parasitic extraction would require a separate explicit mapping contract, not a silent replacement of these failed annotations.

## Built against and reproduction

KLayout0.30.9 and PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` were checked through the pinned flow runtime. Initial geometry-only audit commands below use one CPU and a60-second bound and launched no ngspice or PEX; subsequent stock LVS extraction is recorded separately above. Script/source hashes are recorded in each JSON.

```sh
G1_CPUS=1 G1_CPUSET=7 G1_MEMORY=3g flow/run.sh timeout 60s python3 designs/g1-guardian/blocks/g1_sense/layout/coordinated_gm4/audit_inherited_ota.py --output build/scratch/ota-fidelity-fresh.json
G1_CPUS=1 G1_CPUSET=7 G1_MEMORY=3g flow/run.sh timeout 60s python3 designs/g1-guardian/blocks/g1_sense/layout/coordinated_gm4/audit_ota_terminal_nets.py --inventory build/scratch/ota-fidelity-fresh.json --gds designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top.gds --output build/scratch/ota-terminals-fresh.json
python3 designs/g1-guardian/blocks/g1_sense/layout/coordinated_gm4/audit_junction_defaults.py --inventory build/scratch/ota-fidelity-fresh.json --model designs/g1-guardian/blocks/g1_bgr/sim/qualification/runs/bgr_terminal_corners81_20260922_01/sg13g2_moshv_mod.lib --output build/scratch/ota-junctions-fresh.json
```

The retained model copy is hash-identical to the qualified unchanged stock model; no model is rewritten. Outputs must be fresh. Resource authorization remains separate from these reproduction commands.
