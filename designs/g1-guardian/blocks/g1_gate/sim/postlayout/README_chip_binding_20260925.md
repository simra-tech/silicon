# GATE: binding of the post-layout netlist to the chip cell (2026-09-25)

Question from the evidence audit: is `sim/postlayout/g1_gate_pex.spice` (used in the chip-level decks)
extracted from the geometry that is actually in the chip? The existing extraction
`reports/pex/cc/g1_gate_k25d_pex_netlist.spice` (`e136c884…`) was made from `build/g1_gate_lay/g1_gate.gds`.
That file no longer exists; its `build/` directory now holds only DRC runs. So nothing tied it to a hash.

**Result: bound.** The GATE cell in the chip is geometrically identical to `layout/g1_gate.gds` on all non-fill
layers, with identical labels. A fresh kpex extraction of the chip cell equals the existing extraction, element
for element.

## Steps (pinned image, PDK 84374023, KLayout 0.30.9, kpex 0.3.12; bulk `${BULK}/gate-chip-binding-20260925-r1`)

1. **Cut the cell.** `chip_binding_20260925/cut_and_xor.py` reads the chip of record
   `g1_padring/layout/g1_chip_top_1414.gds` (`629d303a…`, read only). Its only cell matching `g1_gate` is
   `retained_g1_gate` (parent `g1_chip_top`, placed r90 at (781.65, 545.0) um). The script copies that cell's
   subtree into a top cell named `g1_gate`, with geometry unchanged: `g1_gate_chip_cut.gds`, `efdf5057…`.
2. **XOR the cut against the block GDS files.** Flattened, merged, per layer (`chip_binding_20260925/cut_and_xor.log`):
   - vs `layout/g1_gate.gds` (`ddf2c44a…`): 0 of 34 layers differ except fill. The chip cell carries
     Activ/GatPoly/Metal1-3 fill (datatype 22) that the block file does not. All 145 texts are identical.
   - vs `layout/g1_gate_filled.gds` (`ba9d1311…`): 0 non-fill layers differ, and texts are identical. The
     filled file has Metal4/5 and TopMetal1/2 fill that the chip cell does not.
3. **Block LVS on the cut cell.** `run_lvs.py --topcell=g1_gate --run_mode=deep --no_series_res` against
   `layout/g1_gate.cdl` (`27548c03…`), the same options as `reports/lvs/`: **passed** (netlists match),
   `chip_binding_20260925/lvs_chip_cut.log`.
4. **kpex, same command as the original** (`kpex --pdk ihp_sg13g2 --gds <gds> --cell g1_gate --schematic
   layout/g1_gate.cdl --2.5D --mode CC`), run on both the chip cut and a copy of `layout/g1_gate.gds`. Both exit
   with 0 in about 35 s each. Raw netlists: chip cut `e0714fe9…`, block `83b2ee50…`. The bytes differ from
   `e136c884…` only in the date header and in element order and numbering.
5. **Compare the extractions.** `chip_binding_20260925/canon.py` compares element multisets, with unnamed nets
   abstracted and named nets, models, W/L/AS/AD/PS/PD and capacitor values kept. Both new extractions are
   **equal** to `e136c884…`: 633 elements (78 MOS, 555 capacitors) and the same subckt port list. kpex reads
   datatype 0 only, so the fill difference does not enter.

## Hash chain

`g1_chip_top_1414.gds` `629d303a…` → cell `retained_g1_gate` → cut `efdf5057…`
→ (non-fill geometry and texts identical) → `layout/g1_gate.gds` `ddf2c44a…`
→ (kpex on both = the same element multiset) → `reports/pex/cc/g1_gate_k25d_pex_netlist.spice` `e136c884…`
→ (`make_pex_netlist.py`, unchanged) → `sim/postlayout/g1_gate_pex.spice` `e91617f5…`.

Consequence: `g1_gate_pex.spice` stays as it is. No `g1_gate_chip_pex.spice` was written, and the
post-layout checks were not rerun, because the netlist they use is shown to be the chip cell's extraction.

Limits: fill is not in any extraction (same as before). The filled variant differs from the chip cell in its
upper-metal fill; that does not matter electrically here, because kpex ignores fill. Wiring resistance is not
extracted (kpex RC mode is unusable at this version).
