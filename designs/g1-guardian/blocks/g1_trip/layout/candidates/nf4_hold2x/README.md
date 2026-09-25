# nf4_hold2x: 2x hold capacitors on the NF4 TRIP macro. UNADOPTED CANDIDATE

**This candidate is parked. It is not adopted.** The chip of record, the NF4 macro, its extraction
(`sim/postlayout/g1_trip_nf4_pex.spice`) and all PDK files are unchanged. Nothing here is in the chip.

## What it is

The NF4 TRIP macro as it sits in the chip of record, cut out as `g1_trip_nf4.gds` (sha256 `c8efefe3…d384`;
see `sim/postlayout/README.md`). `gen_hold2x.py` adds one 26x26 um `cmim` PDK PCell in parallel with each
hold capacitor:

| New cap | Net | MIM (um) | Existing cap | Over |
| --- | --- | --- | --- | --- |
| CHS2 | vth_soft | (97.5, 129.5)-(123.5, 155.5) | CHS (97.5, 158.5) | top of the soft DAC and the DAC gap |
| CHH2 | vth_hard | (161.5, 129.5)-(187.5, 155.5) | CHH (162.5, 158.5) | top of the hard DAC |
| CH2 | icmp | (59.06, 129.5)-(85.06, 155.5) | CH (59.06, 163.0; in g1_cond) | top of the soft DAC |

- The top-strip squares found earlier (x = 8, 129.5, 199 um) would lie over the soft and hard comparators.
  They were not used. `find_sites.py` picks the nearest 26x26 squares that are:
  - free of Metal5, TopMetal1, MIM, Via4 and TopVia1, in both the macro and the chip shapes over it (2.1 um margin);
  - outside the comparator boxes grown by 3 um;
  - below the IOVDD bar zone.
- **No new cap lies over a comparator or its input pair.**
- Connections:
  - a 3 um TopMetal1 bridge joins the new and existing top plates;
  - a 3 um Metal5 bridge joins the bottom plates (VSS);
  - there is no other routing.
- No-fill markers: Metal4/5 and TopMetal1/2, datatype 23, as `gen_trip_layout.py` does for the existing caps.
- The DAC areas under the new caps allowed Metal4/5 fill before. The chip-level filler would now leave them empty.

## Checks (2026-09-24; pinned image, PDK 84374023, KLayout 0.30.9, kpex 0.3.12)

| Check | Result | Evidence |
| --- | --- | --- |
| PDK DRC `run_drc.py --run_mode=deep --no_density` (tables main + sg13g2_maximal) | **passed**, 0 items, 48 s | `drc.log` |
| PDK LVS `run_lvs.py --topcell=g1_trip --run_mode=deep` vs `g1_trip_nf4_hold2x_lvs.cdl` | **passed** (extracted: CHS/CHH as m=2, CH2 m=1 at top + CH in g1_cond) | `lvs.log` |
| Negative control: same layout vs the unmodified NF4 CDL | failed, as expected | `lvs_negative_control.log` |
| Antenna, density | **not run** at block level | - |
| kpex 2.5D CC | run, rc 0, 1916 s (CPU shared with another job) | bulk `${BULK}/hold2x/pex/kpex_cc.log` |
| tt bracket on that extraction (`sim/postlayout/kick_threshold.py`, tag nf4h2) | hard 0xFE 254 - 26 LSB (-5.10 mV shunt), hard 200 200 - 23 (-4.51 mV), soft 153 - 0; equal to the x2 parallel-cap variant | `sim/postlayout/results_postlayout_nf4.txt` |

CDL edit (explicit): `g1_trip_nf4_hold2x_lvs.cdl` is `g1_trip_nf4_lvs.cdl` with a new first comment line and
these lines added after `CCHH` in `.subckt g1_trip`:
```
CCHS2 vth_soft VSS cap_cmim w=26u l=26u m=1
CCHH2 vth_hard VSS cap_cmim w=26u l=26u m=1
CCH2 icmp VSS cap_cmim w=26u l=26u m=1
```

Hashes: candidate GDS `ec43bbf9f54b93beea122b49837faa1471d4b4a4bf27e911c1fbbe87f7a4e801` (bulk
`${BULK}/hold2x/g1_trip_nf4_hold2x.gds`), CDL `afa6e55a0743092666a916e82abfc5cdc23da581eb7e4848ce8a976e4d19a7ab`,
`gen_hold2x.py` `96bc0b4cc322816c6ad6ef85680e38a99b54709cfa2ec9b51ebc3472f85ea7be`.

## Extraction

The layout-to-extraction input (`layout/pex_input.py`) removes the MIM, Metal5 and TopMetal1 layers, because
kpex 0.3.12 cannot model them. Every added shape is on those layers, so the extraction input of this candidate
is **identical** to the NF4 one: `pexin_xor.py` reports 0 differing layers.

The kpex run on it (raw netlist `4fab1bac…`) gives the same set of capacitance values and the same devices as
the NF4 extraction (compared as sorted lists). The named-net totals are identical too; only the numbering of
unnamed nets differs. `sim/postlayout/make_pex_netlist.py trip_hold2x` (a new config: the six 26 um caps put
back) writes `sim/postlayout/g1_trip_nf4_hold2x_pex.spice` (`a66b564e…`), with the same subckt and ports as
`g1_trip_pex.spice`.

The capacitance of the new plates to the DAC wiring under them is **not** in any extraction.

## Chip-level adoption: what it would take (estimate, not done)

1. **Parent build.** Adapt `blocks/g1_trip/layout/soft_inputpair4_build/prepare_soft_inputpair4_parent_r3.py`.
   That script replaced the soft-cell geometry inside `__rz_port_text_033_retained_g1_trip` and wrote
   `candidate.gds` and `candidate.cdl` with audited deltas. Here it would add the three caps, bridges and no-fill
   shapes to that cell, with the same invariants: other cells, root shapes, fill and pins exact. The CDL gets the
   three lines above in `g1_trip`.
2. **Chip fill.** Remove the chip-level fill that overlaps the new plates: 78 Metal5 fill shapes (894 um2) and
   71 Metal4 fill shapes (574 um2) (`chip_fill_overlap.py`). There are 6 drawn chip Metal4 shapes (243 um2)
   under the plates; they stay, with coupling to the VSS plate. Then rerun density.
3. **Chip netlists.** Update `blocks/g1_padring/netlist/g1_chip_top_1414.cdl` and
   `g1_chip_top_1414_projected_ref.cdl` with the three caps.
4. **Sign-off**, per `blocks/g1_padring/reports/signoff-1414-20260924/README.md`, with the recorded wall times:
   - main DRC: 253 s;
   - `flow/signoff/1414/run_maximal.py`: 559 s;
   - density: 31 s;
   - antenna: 116 s;
   - projected LVS: 146 s;
   - canonical LVS: 111 s;
   - `rename_top.py` / `verify_rename.py` and `block_xor.py`.

   That is about 20 minutes of compute on one CPU each, and up to 1 hour with the parallel runs pinned.
5. **Re-simulate:** the macro LEF (TopMetal1 obstructions) and the loaded-chain/system qualification.

Engineering estimate: about half a day to adapt and audit the parent build, plus sign-off and re-simulation.
None of this has been started.
