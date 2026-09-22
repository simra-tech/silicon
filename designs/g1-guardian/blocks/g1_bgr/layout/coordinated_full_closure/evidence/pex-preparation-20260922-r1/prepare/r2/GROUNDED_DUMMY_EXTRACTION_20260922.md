# Grounded HBT extraction disposition

The first unsimplified KPEX-deck LVS export **failed** against the unchanged
1,036-device reference: 1,027 device pairs matched and nine reference-only HBT
devices did not. The failure is retained; this is not a strict 1,036-device
extraction pass.

## Exact scope

The nine source instances are XQ55, XQ57, XQ58, XQ59, XQ61, XQ63, XQ64, XQ65,
and XQ66. Each has `C B E bn = vss vss vss vss`, model `npn13G2`, and unchanged
`we=0.07u le=0.9u Nx=1 m=1`. The canonical source remains SHA-256
`586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b`.

The saved full-layout graph proves all 36 physical C/B/E/S terminal observations
belong to the same general-VSS component. Flattening retained all native polygons
and annotations, including these devices. No conductor or native device geometry
was removed.

## Pinned extractor behavior

The installed KPEX 0.3.12 SG13G2 `rule_decks/rfmos_model_mapping.lvs` invokes
`target_netlist.purge_devices` and then `purge` unconditionally, on the layout
side. This happens before the optional simplification controls; passing
`no_simplify=true`, `purge=false`, and `combine_devices=false` does not suppress
this earlier call. Its SHA-256 is
`9cba1b823a1b805bb82dacb31cc5f18b3135da44db1b87f683b248713cde8584`.

KLayout 0.30.9 removes a device during this operation when all its defined
terminal nets are equal. The installed API control on an in-memory copy of the
reference removed exactly the nine above, leaving 1,027 devices. No original
database was changed. See the [pinned KLayout implementation](https://github.com/KLayout/klayout/blob/v0.30.9/src/db/db/dbCircuit.cc#L773-L803).

## Thermal and electrical boundary

The canonical model is the four-external-port `npn13G2 c b e bn`, not the separate
five-port `npn13G2_5t`. The layout's substrate terminal S maps to external bn.
An external thermal terminal is therefore **not applicable**. Internal model
nodes `s1` and thermal `t` are **not** claimed to be physical VSS: the model has
its own substrate network and thermal network. Their behavior was **not run**
in this proof. The pinned HBT model-library SHA-256 is
`ae9288f885dd30fab24b07ed1e7e02e69eac9154022a0a6da576985183b0bd79`.

Any approved derived 1,027-device reference is extraction-only. All nine model
instances must remain in the canonical and electrical 1,036-device source;
geometry and conductor parasitics must also remain. This proof does not authorize
discarding thermal behavior or adopting an extracted electrical netlist.

## Checks

| Check | Result |
|---|---|
| Original unsimplified 1,036-reference LVS | Failed: exactly nine reference-only grounded HBTs |
| Exact nine source records and 36 physical terminals | Passed |
| Saved native polygon and annotation flattening parity | Passed |
| Installed purge API control, 1,036 to 1,027 | Passed: exact nine IDs |
| Proof reporter r1 | Failed: trailing-space model-header parser; retained |
| Proof reporter r2 | Passed: whitespace-only parser correction |
| Derived extraction-reference LVS | Not run; semantic review pending |
| Conductor capacitance extraction and electrical qualification | Not run |
| Internal thermal behavior | Not run |
| External thermal layout port and random seed | Not applicable |

The read-only checker is `prove_grounded_dummies.py`; its passed revision SHA-256
is `8b2355415393dcb88a7ae0f7a40785a7cb19d13cac316e9e0ee8d3c948d6b908`.
Original raw proof JSON SHA-256:
`0d146e08578604904e2cde5cb0af641d6c5b8ffbe1ed9d8a0c566ee6edf7ba67`.
The raw receipt includes host paths and remains outside public Git pending a
separately hashed path-redacted export.
