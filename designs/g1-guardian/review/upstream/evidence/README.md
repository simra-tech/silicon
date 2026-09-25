# Evidence: canonical LVS failure of the IO-cell references (check-only runs, 2026-09-25)

These files support the canonical-LVS status of the chip of record
(`blocks/g1_padring/layout/g1_chip_top_1414.gds`, SHA-256 `629d303a…`) and the
upstream draft [`../ihp-io-lvs-issue-draft.md`](../ihp-io-lvs-issue-draft.md).
They are check-only runs: no design file, rule deck or model card was changed.
The runs were made in a local scratch directory; its path is written as `${W}`
in the copied logs and scripts. The large `.lvsdb` and extracted-netlist
outputs are not committed (local only, not inventoried).

## Built against

| Item | Value | How established |
| --- | --- | --- |
| KLayout | 0.30.9 | "Your Klayout version is" line in every log below |
| Pinned PDK | IHP SG13G2 `84374023`; `sg13g2_io.gds` SHA-256 `4281a855…` | repository pin; `sha256sum` of the copy used |
| IHP `dev` library | `sg13g2_io.gds` at `dev` `4fd47c5e`, SHA-256 `25ecbd87…`; `sg13g2_io.cdl` (dev) SHA-256 `d0175a0b…` | `sha256sum` of the copies used; commit from the fetch recorded in the upstream draft |
| IHP `dev` LVS deck | `run_lvs.py` SHA-256 `436d912e…`, `sg13g2.lvs` SHA-256 `866c32c8…` | `sha256sum` of the copy used |
| `.GLOBAL sub!` variant | dev `sg13g2_io.cdl` with one added first line `.GLOBAL sub!` (SHA-256 `e53ecb9f…`); reference-only, not a proposed PDK change | `diff` against the dev CDL |
| Container | `tapeoutbench-eda`, `sha256:ddeb6957…` | `flow/run.sh` image identity check |

## Results

| Check | Files | Result |
| --- | --- | --- |
| XOR, stock `sg13g2_io.gds` pinned `84374023` vs `dev` `4fd47c5e` | `xor/xor_result.json`, `scripts/xor.py` | only 128/0 PolyRes differs: 1 body (2.0 µm²) in `sg13g2_SecondaryProtection`, 26 bodies (520 µm²) in `sg13g2_RCClampResistor`; two via cells renamed with identical shapes; `IOPadOut30mA`, `IOPadVss`, `IOPadIOVss`, `Filler200`, `Corner` identical |
| XOR, design-local IO copies in the chip vs stock cells | `xor/chip_vs_dev.json`, `scripts/cmp_chip.py` | `g1_io_secondary_polyres_r1` (and `_alias1`) identical on every layer to `dev` `sg13g2_SecondaryProtection`; `g1_io_rc_polyres_r1` (and `_alias1`) identical on every layer to `dev` `sg13g2_RCClampResistor`; against the pinned cells both differ only on 128/0 (the PolyRes added upstream by PR #1223) |
| Cell-level LVS, stock cells: pinned deck, `dev` GDS, pinned CDL; `IOPadAnalog`, `IOPadIn`, `IOPadVdd`, `Filler200` (flat, `--top_lvl_pins`) | `cell_lvs/pinneddeck_*`, `cell_lvs/xref_devcdl_and_pinnedcdl.txt` | **failed** (4/4) |
| Cell-level LVS, stock cells: `dev` deck, `dev` GDS, `dev` CDL; same four cells | `cell_lvs/devdeck_devgds_devcdl_*`, `cell_lvs/xref_devcdl_and_pinnedcdl.txt`, `scripts/cells.sh` | **failed** (4/4). Residual mismatches: one local `SUB!` net per reference sub-instance, ptap and diode pairing; the RPPD is extracted and the `IOPadIn` dummy PMOS pairs |
| Cell-level LVS, `dev` deck, `dev` GDS, `.GLOBAL sub!` CDL; above four plus `IOPadOut30mA` | `cell_lvs/devdeck_devgds_globalsub_*`, `cell_lvs/xref_globalsub.txt`, `scripts/glob.sh` | **failed** (5/5); mismatch counts fall (e.g. `IOPadIn` 8 nets/6 devices to 4/3) |
| Full chip `629d303a…`, `dev` deck, canonical CDL `g1_chip_top_1414.cdl`, deep, `--top_lvl_pins` | `chip_lvs_devdeck/*`, `scripts/chip.sh` | **failed**: the same 14 NoMatch IO sub-cells as with the pinned deck (`sg13g2_Clamp_{N15N15D,N20N0D,N2N2D,N43N43D4R,N8N8D,P15N15D,P20N0D,P2N2D,P8N8D}`, `DCNDiode`, `DCPDiode`, `LevelDown`, `LevelUpInv`, `RCClampInverter`); 34 circuits match |

The pinned-deck arm of `scripts/cells.sh` was run with the pinned deck path;
the committed script keeps only the `dev` arm. The command of each run is in
the header of its log (layout, netlist, top cell, options).

## Conclusion drawn in the design records

Canonical LVS of the chip of record: **failed**. Cause: substrate/tap/diode
netlist semantics of the IO-cell reference in the PDK (`sub!` local in every
`sg13g2_io.cdl` subcircuit, ptap and antenna-diode pairing). It reproduces with
stock cells and with IHP's latest `dev` deck and library. The design-local IO
copies match IHP's `dev` library on every layer (PR #1223). Upstream issues
[#1218](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/1218) and
[#1130](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/1130).

Not established by these runs: a reference or deck change that makes the IO
cells pass (the `.GLOBAL sub!` test did not reach a match), and an XOR of the
whole IO ring of the chip against stock cells (only the two PolyRes cells were
compared). The comparison of the chip's pinned-deck canonical run is
[`signoff-1414-20260924/lvs_canonical/pair_counts.json`](../../../blocks/g1_padring/reports/signoff-1414-20260924/lvs_canonical/pair_counts.json).
