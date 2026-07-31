# Comparator Core Latch Lineage Audit V4 for Custom CML Divide-by-2 Stage

> **Publication disposition: CURRENT STATIC LINEAGE RECORD.** The original source artifact is
> 9,621 bytes with SHA-256
> `944a4aa0a147ef1a1898b6119f1ba41f91cacf271cff19531adea33210a914c1`.
> This audit contains no circuit implementation or electrical result.

## 1. Authority & Evidence Source Mapping

| Item | Authority Classification | Source Citation / Artifact | Source context | Status |
|---|---|---|---|---|
| 1 | [CONFIRMED_IMPLEMENTATION_EVIDENCE] | Top V3 Netlist b8ac8271... Lines 130--150 | Current comparator core CML track/latch stage devices and netlist literals | CONFIRMED |
| 2 | [SOURCE_REQUIREMENT] | Requirements V4 README.md (baa1e17d...) | Divided-clock monitor specification requirements | CONFIRMED |
| 3 | [ARCHITECTURE_DECISION] | Architecture Proposal V3 (4db0a8e7...) | Standalone DIV2 contract and CML master-slave topology direction | CONFIRMED |
| 4 | [LINEAGE_ONLY_IMPLEMENTATION_EVIDENCE] | Comparator Core Latch Netlist Literals | Device models, transistor parameters, and load resistor parameters in lines 130--150 | CONFIRMED |
| 5 | [PROVISIONAL_ROLE_INFERENCE] | Functional Role Interpretations | Topology role interpretations not stated directly in SPICE netlist text | PROVISIONAL |
| 6 | [PROVISIONAL_SEED] | Retained Track/Latch Structural Seed | Candidate mapping of retained comparator track/latch as initial structural starting seed | PROVISIONAL |
| 7 | [UNKNOWN_TOP_DECISION] | Custom CML Divide-by-2 Parameters | Slave stage sizing, tail current, swing, common mode, reset, load, PVT, power bounds | UNKNOWN |

---

## 2. Line-by-Line Device Audit: Top V3 Netlist `b8ac8271` Lines 130--150

| Line | Instance Name | Exact Netlist Literal | Parsed Pins / Connection Nodes | Model Name | Parsed Explicit Parameters | Functional Role Interpretation [PROVISIONAL_ROLE_INFERENCE] |
|---|---|---|---|---|---|---|
| 130 | `XRC1` | `XRC1 VCC_HBT c_n sub! rppd w=1.0u l=0.838u m=1 b=0 mm_ok=1` | `VCC_HBT c_n sub!` | `rppd` | `w=1.0u l=0.838u m=1 b=0 mm_ok=1` | Retained CML Collector Load Resistor N |
| 131 | `XRC2` | `XRC2 VCC_HBT c_p sub! rppd w=1.0u l=0.838u m=1 b=0 mm_ok=1` | `VCC_HBT c_p sub!` | `rppd` | `w=1.0u l=0.838u m=1 b=0 mm_ok=1` | Retained CML Collector Load Resistor P |
| 132 | `XQ1` | `XQ1 c_n IN_P e_track sub! npn13G2 Nx=1 mm_ok=1` | `c_n IN_P e_track sub!` | `npn13G2` | `Nx=1 mm_ok=1` | Retained Comparator Track Differential Pair HBT P |
| 133 | `XQ2` | `XQ2 c_p IN_N e_track sub! npn13G2 Nx=1 mm_ok=1` | `c_p IN_N e_track sub!` | `npn13G2` | `Nx=1 mm_ok=1` | Retained Comparator Track Differential Pair HBT N |
| 134 | `XRBLEED_TRACK` | `XRBLEED_TRACK e_track e_tail sub! rppd w=1.0u l=0.50u m=1 b=0 mm_ok=1` | `e_track e_tail sub!` | `rppd` | `w=1.0u l=0.50u m=1 b=0 mm_ok=1` | Retained Track Stage Emitter Bleed Resistor |
| 135 | `XRBLEED_LATCH` | `XRBLEED_LATCH e_latch e_tail sub! rppd w=1.0u l=0.50u m=1 b=0 mm_ok=1` | `e_latch e_tail sub!` | `rppd` | `w=1.0u l=0.50u m=1 b=0 mm_ok=1` | Retained Latch Stage Emitter Bleed Resistor |
| 136 | `XQ3` | `XQ3 c_n ef_p e_latch sub! npn13G2 Nx=1 mm_ok=1` | `c_n ef_p e_latch sub!` | `npn13G2` | `Nx=1 mm_ok=1` | Retained Cross-Coupled Regenerative Latch HBT P |
| 137 | `XQ4` | `XQ4 c_p ef_n e_latch sub! npn13G2 Nx=1 mm_ok=1` | `c_p ef_n e_latch sub!` | `npn13G2` | `Nx=1 mm_ok=1` | Retained Cross-Coupled Regenerative Latch HBT N |
| 138 | `XQCLK_TRACK` | `XQCLK_TRACK e_track CLK_P e_tail sub! npn13G2 Nx=1 mm_ok=1` | `e_track CLK_P e_tail sub!` | `npn13G2` | `Nx=1 mm_ok=1` | Retained Clock Steering Differential Pair HBT (Track) |
| 139 | `XQCLK_LATCH` | `XQCLK_LATCH e_latch CLK_N e_tail sub! npn13G2 Nx=1 mm_ok=1` | `e_latch CLK_N e_tail sub!` | `npn13G2` | `Nx=1 mm_ok=1` | Retained Clock Steering Differential Pair HBT (Latch) |
| 140 | `XMP1_COMP` | `XMP1_COMP c_p1_comp c_p2_comp VCC_HBT VCC_HBT sg13_hv_pmos w=20.0u l=1.0u ng=1 m=1 mm_ok=1` | `c_p1_comp c_p2_comp VCC_HBT VCC_HBT` | `sg13_hv_pmos` | `w=20.0u l=1.0u ng=1 m=1 mm_ok=1` | Retained PTAT Bias Current Mirror PMOS P |
| 141 | `XMP2_COMP` | `XMP2_COMP c_p2_comp c_p2_comp VCC_HBT VCC_HBT sg13_hv_pmos w=20.0u l=1.0u ng=1 m=1 mm_ok=1` | `c_p2_comp c_p2_comp VCC_HBT VCC_HBT` | `sg13_hv_pmos` | `w=20.0u l=1.0u ng=1 m=1 mm_ok=1` | Retained PTAT Bias Current Mirror PMOS N |
| 142 | `XQP1_COMP` | `XQP1_COMP c_p1_comp c_p1_comp e_p1_comp sub! npn13G2 Nx=1 mm_ok=1` | `c_p1_comp c_p1_comp e_p1_comp sub!` | `npn13G2` | `Nx=1 mm_ok=1` | Retained PTAT Bias Core HBT 1 |
| 143 | `XRDEG_P1_COMP` | `XRDEG_P1_COMP e_p1_comp VSS sub! rppd w=4.0u l=0.50u m=1 b=0 mm_ok=1` | `e_p1_comp VSS sub!` | `rppd` | `w=4.0u l=0.50u m=1 b=0 mm_ok=1` | Retained PTAT Bias Degeneration Resistor 1 |
| 144 | `XQP2_COMP` | `XQP2_COMP c_p2_comp c_p1_comp e_p2_comp sub! npn13G2 Nx=4 mm_ok=1` | `c_p2_comp c_p1_comp e_p2_comp sub!` | `npn13G2` | `Nx=4 mm_ok=1` | Retained PTAT Bias Core HBT 2 (Ratio 4:1) |
| 145 | `XRPTAT_COMP` | `XRPTAT_COMP e_p2_comp VSS sub! rppd w=2.0u l=1.107u m=1 b=0 mm_ok=1` | `e_p2_comp VSS sub!` | `rppd` | `w=2.0u l=1.107u m=1 b=0 mm_ok=1` | Retained PTAT Bias Setting Resistor |
| 146 | `XCSTAB_COMP` | `XCSTAB_COMP VSS c_p1_comp cap_cmim w=80.0u l=83.3u m=1 mm_ok=1` | `VSS c_p1_comp` | `cap_cmim` | `w=80.0u l=83.3u m=1 mm_ok=1` | Retained PTAT Bias Stability Capacitor |
| 147 | `XQS_COMP` | `XQS_COMP e_tail c_p1_comp e_scomp sub! npn13G2 Nx=6 mm_ok=1` | `e_tail c_p1_comp e_scomp sub!` | `npn13G2` | `Nx=6 mm_ok=1` | Retained Comparator Tail Current Source HBT |
| 148 | `XRDEG_SCOMP` | `XRDEG_SCOMP e_scomp VSS sub! rppd w=24.0u l=0.50u m=1 b=0 mm_ok=1` | `e_scomp VSS sub!` | `rppd` | `w=24.0u l=0.50u m=1 b=0 mm_ok=1` | Retained Tail Current Source Degeneration Resistor |
| 149 | `XQEF1` | `XQEF1 VCC_HBT c_p ef_p sub! npn13G2 Nx=1 mm_ok=1` | `VCC_HBT c_p ef_p sub!` | `npn13G2` | `Nx=1 mm_ok=1` | Retained Emitter Follower Level Shifter HBT P |
| 150 | `XQEF2` | `XQEF2 VCC_HBT c_n ef_n sub! npn13G2 Nx=1 mm_ok=1` | `VCC_HBT c_n ef_n sub!` | `npn13G2` | `Nx=1 mm_ok=1` | Retained Emitter Follower Level Shifter HBT N |

---

## 3. Mapping Retained Comparator Track/Latch Elements Onto Generic Master/Slave CML DFF Requirements

### A. Lineage Elements That Exist [LINEAGE_ONLY_IMPLEMENTATION_EVIDENCE]

- Retained CML collector load resistors (`XRC1/XRC2`)
- Retained track differential pair (`XQ1/XQ2`)
- Retained cross-coupled regenerative latch pair (`XQ3/XQ4`)
- Retained clock-steering differential pair (`XQCLK_TRACK/XQCLK_LATCH`)
- Retained emitter-follower output level shifters (`XQEF1/XQEF2`)
- Retained PTAT tail bias generator network (`XMP1_COMP` -- `XRDEG_SCOMP`)

### B. Required Elements That Are Absent [CONFIRMED_IMPLEMENTATION_EVIDENCE]

- **Complete Slave Latch Stage:** Zero slave collector load resistors, zero slave tracking differential pair, zero slave cross-coupled regenerative latch pair, zero slave clock-steering differential pair, and zero slave emitter-follower output level shifters exist in Top V3.
- **Inverted Feedback Routing:** Zero feedback interconnects connecting slave output nodes ($Q_N, Q_P$) to tracking input nodes ($D_P, D_N$) exist in Top V3.
- **Dedicated Slave Tail Bias:** Zero slave tail current sink exists in Top V3.

### C. Non-Portable Internal Nodes [UNKNOWN_TOP_DECISION]

The following internal nodes in lines 130--150 are specific to the comparator core and **cannot be ported directly** to a master-slave CML divider without explicit new sizing and bias decisions:

- Internal collector nodes `c_p`, `c_n`
- Emitter follower level-shifted nodes `ef_p`, `ef_n`
- Track/latch emitter nodes `e_track`, `e_latch`
- Tail node `e_tail`
- PTAT bias node `c_p1_comp`

---

## 4. Unresolved Divider Parameters [UNKNOWN_TOP_DECISION]

All device parameters, operating biases, and performance limits for the custom CML divide-by-2 stage remain **`UNKNOWN_TOP_DECISION`**:

1. **[UNKNOWN_TOP_DECISION] Device Sizing:** HBT emitter length ($l_e$) and finger count ($N_x$) for slave tracking, slave latch, and slave clock-steering pairs.
2. **[UNKNOWN_TOP_DECISION] Tail Bias Current:** Total DC tail bias current allocated to track and latch stages.
3. **[UNKNOWN_TOP_DECISION] Common-Mode Voltage:** Output common-mode voltage level $V_{cm}(DIV2\_P, DIV2\_N)$.
4. **[UNKNOWN_TOP_DECISION] Differential Voltage Swing:** Output differential peak-to-peak voltage swing $\Delta V_{diff}$.
5. **[UNKNOWN_TOP_DECISION] Reset & Startup Mechanism:** Asynchronous reset circuitry and startup initialization mechanism.
6. **[UNKNOWN_TOP_DECISION] Output Load Model:** Internal capacitive load model ($C_{load}$) driven into the second-stage divider.
7. **[UNKNOWN_TOP_DECISION] Power Dissipation Budget:** Maximum allowable DC power dissipation for the front divide-by-2 stage.
8. **[UNKNOWN_TOP_DECISION] PVT Operating Bounds:** Operational corners (`mos_tt`, `hbt_typ`, $27^{\circ}\text{C}$ vs $-40^{\circ}\text{C} \dots +125^{\circ}\text{C}$).
9. **[UNKNOWN_TOP_DECISION] Acceptance Tolerances:** Waveform duty cycle, phase noise, and peak-to-peak amplitude acceptance limits.

---

## 5. Smallest Future Design Step & Stop Conditions [PROVISIONAL]

- **Smallest Next Step [PROVISIONAL]:** The smallest next design step is a Principal Engineer retain/reject decision on this structural seed (`PROVISIONAL_SEED`), stopping before any circuit file creation or simulation.
- **Explicit Stop Conditions [PROVISIONAL]:**
  - Zero schematic files created
  - Zero symbol files created
  - Zero SPICE netlists generated
  - Zero OpenADA CLI calls executed
  - Zero ngspice simulation runs executed

---

## 6. Preservation & Status Classifications

- **Status:** `PROVISIONAL / NOT EVALUATED`
- **Execution Scope:** Lineage audit record definition V4 only; zero schematic edits, zero symbol edits, zero netlists, zero OpenADA calls, and zero ngspice simulations executed.
