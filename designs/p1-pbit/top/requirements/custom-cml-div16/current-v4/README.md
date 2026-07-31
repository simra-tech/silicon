# Requirements Specification V4: Custom Divide-by-16 Clock Monitor for Top Macro V3

> **Publication disposition: CURRENT REQUIREMENTS RECORD.** This is a requirements-only artifact.
> Circuit behavior, electrical performance, and physical implementation remain not evaluated.

## 1. Authority & Evidence Source Tuples

1. **[SOURCE_REQUIREMENT]** Published Architecture Specification `designs/p1-pbit/specification/P1_TOP_LEVEL_SPECIFICATION.md` (SHA-256: `f67a1528bd31e31353028d685dde5a5c94b0c87577e649b7b7c3a35b6152baaf`), Line 154 (Exact Literal):
```text
* **Modification:** Added a direct, unwhitened raw bitstream tap (`PBIT_RAW`) tapped directly from the decision latch, alongside an on-chip clock divider ($\div 16$ or $\div 64$) output (`CLK_OUT_DIV`) routed to top-metal probe pads.
```

2. **[PUBLISHED_ASSUMPTION]** Published Architecture Specification `designs/p1-pbit/specification/P1_TOP_LEVEL_SPECIFICATION.md` (SHA-256: `f67a1528bd31e31353028d685dde5a5c94b0c87577e649b7b7c3a35b6152baaf`), Line 61 (Exact Literal):
```text
| **Target Sampling Rate ($f_{sample}$)** | $1.0 \text{ to } 5.0\,\text{GS/s}$ ($5.0\,\text{GS/s}$ at $1\,\text{mA}$) | **Assumed** | Derived from HBT $f_T$ and CML latch regenerative speed |
```

3. **[ARCHITECTURE_DECISION]** Principal Engineer architecture decision, 2026-07-31:
   > "PROVISIONAL architecture decision — adopt divide-by-16 as the baseline ratio. At the stated 5.0 GS/s maximum it yields 312.5 MHz, inside the specification’s stated 1–2 GHz instrument bandwidth, while retaining four times as many timing markers as divide-by-64. This selects a ratio; it does not select or validate a circuit topology."

4. **[DERIVED]** Output Frequency Range Arithmetic:
   > $62.5\,\text{MHz} \dots 312.5\,\text{MHz}$ output frequency range (Derived by dividing the $1.0 \dots 5.0\,\text{GS/s}$ input clock assumption by $16$).

5. **[CONFIRMED_IMPLEMENTATION_EVIDENCE]** Current Top V3 Netlist `designs/p1-pbit/top/source-backed-v3/p1_top_hier.spice` (SHA-256: `b8ac82719ffcd365b91fbd7c997b45d9d422e684077fe82f05a691cb7dcbd4ca`), Lines 168--169:
   > Line 168: `XM11 CLK_OUT_DIV CLK_P VDD VDD sg13_lv_pmos w=2.83u l=0.13u ng=1 m=1 mm_ok=1`
   > Line 169: `XM12 CLK_OUT_DIV CLK_P VSS VSS sg13_lv_nmos w=2.0u l=0.13u ng=1 m=1 mm_ok=1`
   > *(Direct LV CMOS inverter buffer driven directly by CLK_P; no clock divider logic instantiated).*

6. **[CONFIRMED_IMPLEMENTATION_EVIDENCE]** Available Top V3 Power Domain Rails (`b8ac8271`):
   > $2.5\,\text{V}$ HBT CML supply (`COMPARATOR_VCC_HBT`), $1.2\,\text{V}$ LV CMOS supply (`VDD`), and common ground (`COMPARATOR_VSS`).

7. **[CONFIRMED_REJECTION_EVIDENCE]** IHP SG13G2 Standard Cell Liberty Model `libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_typ_1p20V_25C.lib` (SHA-256: `7677a8918689f452e80405ad16a83e744709342574f2aedcc507c2758986b396`), Lines 9011--9033:
   > Minimum required clock pulse width at fastest characterized slew (18.6 ps) is 131.073 ps for `sg13g2_dfrbp_1`.
   > *(5.0 GHz clock 50% duty cycle supplies 100 ps per half-cycle, violating the 131.073 ps standard-cell timing limit and rejecting standard-cell DFFs for the 5.0 GHz first stage).*

8. **[PROVISIONAL_RESEARCH_DIRECTION]** A. Trifiletti et al., "A Power Efficient Frequency Divider With 55 GHz Self-Oscillating Frequency in SiGe BiCMOS," *Electronics* 9(11), 1968 (2020), DOI: `10.3390/electronics9111968`:
   > CML master-slave DFF topology direction only.
   > *(Topology direction only; no SG13G2 transistor sizing, power dissipation, or frequency capability implied).*

---

## 2. Explicit Unresolved Requirements [UNKNOWN_TOP_DECISION]

1. **[UNKNOWN_TOP_DECISION] Architecture Partition:** All-CML 4-stage cascade versus hybrid CML front-stage (divide-by-2 or divide-by-4) + 1.2V LV CMOS tail-stage partition.
2. **[UNKNOWN_TOP_DECISION] CML-to-CMOS Interface:** Level-shifter topology and bias point connecting the high-speed CML divider output to $1.2\,\text{V}$ CMOS logic levels.
3. **[UNKNOWN_TOP_DECISION] Reset & Startup State:** Asynchronous reset / initialization requirement and initial startup state for the divider flip-flops.
4. **[UNKNOWN_TOP_DECISION] Probe Pad Load Model:** Target load capacitance ($C_{load}$) and probe card model attached to `CLK_OUT_DIV` at top-metal probe pad interface.
5. **[UNKNOWN_TOP_DECISION] Power Dissipation Budget:** Maximum allowable DC current draw and power budget allocated to the clock divider subcircuit.
6. **[UNKNOWN_TOP_DECISION] PVT Operating Bounds:** Operational corners (`mos_tt`, `hbt_typ`, $27^{\circ}\text{C}$ baseline vs $-40^{\circ}\text{C} \dots +125^{\circ}\text{C}$ extreme corners).
7. **[UNKNOWN_TOP_DECISION] Acceptance Tolerances:** Waveform duty cycle, phase noise, and peak-to-peak amplitude acceptance limits for `CLK_OUT_DIV`.

---

## 3. Smallest Future Bounded Design Task

* **Next Design Task:**
  The next bounded design task is a standalone divide-by-2 architecture proposal and test plan.

---

## 4. Preservation & Status Classifications

* **Status:** `PROVISIONAL / NOT EVALUATED`
* **Execution Scope:** Requirements specification definition only; zero schematic edits, zero symbol edits, zero netlists, zero OpenADA calls, and zero ngspice simulations executed.
