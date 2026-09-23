# Isolated SENSE dual-ended gate prototype

The isolated geometry, source-native audit, stock main/maximal DRC and strict
source LVS **passed**. This is not a canonical/fullchip change or complete
physical-model qualification. Source NGCON2, all 58 logical MOS identities,
835 channels, 48 shared diffusion strips and their mismatch identities stay
unchanged. No model card, rule deck, source parameter, pin or primitive is
changed.

| Check | Result |
|---|---|
| Original r8 gate-side inventory | 835 one-ended channels; model NGCON2 correspondence unresolved |
| In-memory clearance/source graph | Passed, 134 source nets and 229 physical components |
| Saved additive geometry | Passed, 835 opposite-end contacts; exact old polygon/text/hierarchy preservation |
| Independent native/source reference | Passed, 835 channels, 893 strips, 58 MOS, 98 resistors, three MIMs, nine ports |
| Stock main / maximal DRC | Passed, zero / zero markers; 10.229 / 9.945 s children |
| Strict source LVS | Passed, all circuit/device/net/pin pairs Match; 6.346 s child |
| Native/default and source-oriented stock A/P delta | Passed exact equality of all 58 records to r8 |
| Existing extracted per-node A/P annotations | **Failed**, unchanged 51 failures and seven passes |
| Intrinsic shared-junction and complete gate-resistance applicability | **Not qualified** |
| Zero-R parameter/wave parity; distributed-adapter runtime | **Not run** |
| Affected field coupling/current/electrical and fullchip checks | **Not run** |
| Canonical or fullchip adoption | **Not run** |

The new GDS SHA256 is
`498cf48b87160ef7086b62fc0f624a5c1214f9f2993178953c6c3bdd5716cda7`.
The unchanged source SHA256 is
`baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`.
The source-derived CDL remains byte-exact
`e3e3c22fa0e59c61f5acc79f3733833ec2a144fe3f133ed09f7922a395deec20`.
The saved build took 96.776 s including launcher; independent reference took
15.875 s. Exact commands, snapshots, hashes and child bounds are in the
[evidence manifest](evidence/dual-gate-20260923-r1/export_manifest.json).

## What changed and what remains unresolved

Each channel receives an opposite-end poly head, one 0.16 um contact, a
0.30 um M1 landing and a 0.16 um M1 bridge joining its existing gate contact.
Only drawing layers Poly, Cont and M1 change; no Via1/M2 is added. Added union
areas are 552.9, 21.376 and 1101.438 um² respectively. All Active/channel/
diffusion polygons, centroids, devices, labels and hierarchy remain exact.
This addresses physical availability of two connected gate ends, not every
condition of the compact model's internal gate-resistance network.

Pinned PSP source explicitly defaults XGW to 100 nm, described as the
contact-to-channel distance; the physical contact centers here are 330 nm
beyond Active. Contact-edge versus center convention and the calibrated
RGO/contact contributions are not established. No XGW/NGCON/card adjustment
is made. New M1 over gate channels also changes extrinsic fields; this must
not inherit an old capacitance qualification. The six shared-input logical
devices retain their independent intrinsic-junction applicability question.

The [distributed-terminal contract](SENSE_DISTRIBUTED_TERMINAL_CONTRACT_20260923.md)
describes a power-conserving, source-preserving adapter and fixed-linear-mesh
bounds as conditional diagnostics. It does not select an arbitrary contact,
split a logical MOS or replace its compact-model internal network. Exact
rational controls passed; runtime/electrical qualification is still not run.

## Built against

| Component | Pinned identity and verification |
|---|---|
| SG13G2 PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, live COMMIT plus unchanged stock-deck hashes |
| Runtime image | `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`, previously qualified image identity |
| KLayout | 0.30.9, runtime Python API assertion |
| Python | Pinned runtime Python 3.12 for geometry/stock; host JSON/algebra preparation only otherwise |
| ngspice | Not run for this prototype; prior pinned runtime is 46 |

All stock switches remain enabled except the separately scoped density,
antenna and precheck modes documented by the stock runner. The new macro is
not substituted into the final filled chip; that candidate's results remain
bound to its own unchanged source. Two read-only container-copy attempts
found already-completed containers and failed before inspection; those
failures were retained, with no simulation or stock rerun to recover them.
