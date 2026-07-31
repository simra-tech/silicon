# Standalone Custom CML Divide-by-2 Front-Stage Proposal & Test Plan V1

> **Publication disposition: REJECTED.** The original 7,667-byte snapshot has SHA-256
> `6bc5e58adeb2f70f8a9bbc8f19ac428f92382fb80a438ff72c352b75ab7f5691` and contained raw
> `0x08` backspace bytes at offsets 171, 208, 247, and 297. This public copy replaces each unsafe
> byte with the literal marker `<0x08>`; it also retained incorrect authority labels and an
> incomplete measurement plan.

## 1. Authority & Evidence Source Mapping

$$\begin{array}{lcm{3.5cm}l|l}
\text{\bf Item} & \text{<0x08>f Authority Classification} & \text{<0x08>f Source Citation / Artifact} & \text{<0x08>f Exact Source Literal / Record Context} & \text{<0x08>f Status} \\
\hline
1 & \text{[SOURCE_REQUIREMENT]} & \text{Requirements V4 README.md (baa1e17d...)} & \text{Top V3 clock divider monitor specification requirements} & \text{CONFIRMED} \\
2 & \text{[SOURCE_REQUIREMENT]} & \text{P1_TOP_LEVEL_SPECIFICATION.md line 154} & \text{On-chip clock divider (div-16/64) routed to top-metal probe pad} & \text{CONFIRMED} \\
3 & \text{[PUBLISHED_ASSUMPTION]} & \text{P1_TOP_LEVEL_SPECIFICATION.md line 61} & \text{Target sampling rate 1.0 to 5.0 GS/s (Assumed)} & \text{CONFIRMED} \\
4 & \text{[ARCHITECTURE_DECISION]} & \text{Principal Engineer decision, 2026-07-31} & \text{Adopt divide-by-16 baseline ratio for clock monitor} & \text{CONFIRMED} \\
5 & \text{[LINEAGE_EVIDENCE]} & \text{Top V3 netlist b8ac8271 lines 130--150} & \text{Single clock-steered HBT track/latch stage in comparator core} & \text{CONFIRMED} \\
6 & \text{[RESEARCH_DIRECTION]} & \text{Trifiletti et al. DOI 10.3390/electronics9111968} & \text{CML master-slave DFF topology direction only} & \text{PROVISIONAL} \\
\hline
\end{array}$$

---

## 2. Minimal Black-Box Interface Contract

* **Input Interface [SOURCE_REQUIREMENT]:**
  - `CLK_P` (Input): Positive terminal of high-speed differential clock.
  - `CLK_N` (Input): Negative terminal of high-speed differential clock.
* **Internal Output Interface [SOURCE_REQUIREMENT]:**
  - `DIV2_P` (Output): Positive terminal of internal divide-by-2 clock output.
  - `DIV2_N` (Output): Negative terminal of internal divide-by-2 clock output.
  - *(Note: `DIV2_P/N` is an internal macro signal and does not connect directly to an external probe pad).*
* **Power Supply Domain [CONFIRMED_IMPLEMENTATION_EVIDENCE]:**
  - `COMPARATOR_VCC_HBT`: $2.5\,\text{V}$ DC positive supply rail for HBT CML core.
  - `COMPARATOR_VSS`: $0.0\,\text{V}$ DC common ground reference rail.

---

## 3. CML Master-Slave DFF Topology Direction [PROVISIONAL_RESEARCH_DIRECTION]

Retained research (Trifiletti et al., DOI `10.3390/electronics9111968`) supports a **high-speed CML master-slave DFF with inverted output feedback** ($Q_N \to D_P, Q_P \to D_N$) as a candidate topology direction for the $5.0\,\text{GS/s}$ first divide-by-2 stage.

> **Boundary Notice [PROVISIONAL]:** The Trifiletti paper describes a 55 nm SiGe BiCMOS process. It supports topology direction only; zero transistor dimensions, tail bias currents, power dissipation, or frequency limits are transferred from the paper to the IHP SG13G2 process.

### Lineage Implementation Evidence [LINEAGE_ONLY_IMPLEMENTATION_EVIDENCE]
The current comparator core in Top V3 netlist `p1_top_hier.spice` (SHA-256: `b8ac82719ffcd365b91fbd7c997b45d9d422e684077fe82f05a691cb7dcbd4ca`) lines 130--150 supplies **one clock-steered HBT track/latch stage**, which is incomplete for a master-slave DFF and cannot be reused directly without a second slave latch stage.

---

## 4. ASCII Signal & State Transition Diagram

```text
                  +-------------------------------------------------------------+
                  |           STANDALONE CML DIVIDE-BY-2 FRONT STAGE            |
                  |                                                             |
   CLK_P ---------+--> [ Master Clock Gate ]        [ Slave Clock Gate ] -------+
   CLK_N ---------+--> [ (Sample on CLK_P) ]        [ (Sample on CLK_N) ] ------+
                  |            |                             |                  |
                  |            v                             v                  |
                  |     +--------------+              +--------------+          |
                  |     | Master Latch | ------------>|  Slave Latch | ---+-----+---> DIV2_P
                  |     +--------------+              +--------------+    |     |
                  |            ^                             |            |     |
                  |            |                             v            |     |
                  |            +--- Inverted Feedback <------+------------+-----+---> DIV2_N
                  |                (Q_N -> D_P, Q_P -> D_N)                     |
                  +-------------------------------------------------------------+

Input Clock CLK_P:  __/\__/\__/\__/\__/\__/\__/\__/\__/\__/\__  (5.0 GHz Period T = 200 ps)

Output DIV2_P:      ____/--------\____/--------\____/--------\  (2.5 GHz Period 2T = 400 ps)

Output DIV2_N:      ----\____/--------\____/--------\____/--  (Complementary 2.5 GHz)
```

---

## 5. Explicit Unresolved Parameters [UNKNOWN_TOP_DECISION]

All physical, electrical, and structural design choices for the custom CML divide-by-2 stage remain **`UNKNOWN_TOP_DECISION`** and require explicit source-backed specification:

1. **[UNKNOWN_TOP_DECISION] Transistor Topology & Devices:** Exact HBT device count, emitter length ($l_e$), and finger count ($N_x$) per differential pair.
2. **[UNKNOWN_TOP_DECISION] Tail Bias Current:** Total DC tail bias current ($I_{tail}$) allocated to master and slave CML latches.
3. **[UNKNOWN_TOP_DECISION] Common-Mode Voltage Level:** Output and input CML common-mode voltage level ($V_{cm}$).
4. **[UNKNOWN_TOP_DECISION] Differential Voltage Swing:** Nominal differential output voltage swing ($\Delta V_{diff} = |DIV2_P - DIV2_N|$).
5. **[UNKNOWN_TOP_DECISION] Reset & Startup State:** Startup initialization mechanism to ensure reliable frequency division from zero state.
6. **[UNKNOWN_TOP_DECISION] Output Load Model:** Internal capacitive load model ($C_{load}$) driven by `DIV2_P/N` into the second-stage divider.
7. **[UNKNOWN_TOP_DECISION] Power Dissipation Budget:** Allowable power dissipation for the front divide-by-2 stage.
8. **[UNKNOWN_TOP_DECISION] PVT Operating Bounds:** Process, voltage, and temperature operating bounds ($27^{\circ}\text{C}$ vs $-40^{\circ}\text{C} \dots +125^{\circ}\text{C}$).
9. **[UNKNOWN_TOP_DECISION] Acceptance Tolerances:** Duty cycle distortion, phase noise, and peak-to-peak amplitude acceptance limits.

---

## 6. Standalone Test Plan Specification [PROVISIONAL]

Future standalone evaluation of the custom CML divide-by-2 front-stage shall execute under this bounded test plan:

* **Experiment Points [PUBLISHED_ASSUMPTION]:**
  - Point 1: $1.0\,\text{GS/s}$ input clock frequency ($f_{in} = 1.0\,\text{GHz}$, $T = 1.0\,\text{ns}$)
  - Point 2: $5.0\,\text{GS/s}$ input clock frequency ($f_{in} = 5.0\,\text{GHz}$, $T = 200\,\text{ps}$)
  *(Note: Input sampling rates are published assumptions and do not represent guaranteed operational limits).*
* **Required Test Artifacts [PROVISIONAL]:**
  - Standalone testbench SPICE deck candidate
  - Combined stdout/stderr execution log file
  - Output binary raw dataset file (`.raw`)
* **Required Un-Thresholded Measurements [PROVISIONAL]:**
  - Frequency division ratio ($f_{in} / f_{out}$)
  - Peak-to-peak differential voltage swing $\Delta V_{diff}(DIV2\_P, DIV2\_N)$
  - Total DC supply branch current $I(COMPARATOR\_VCC\_HBT)$
  - First and last linear-interpolation midpoint crossing times
  *(Note: All measurements shall be reported as raw physical quantities without numeric pass/fail thresholds).*

---

## 7. Preservation & Status Classifications

* **Status:** `PROVISIONAL / NOT EVALUATED`
* **Execution Scope:** Architecture proposal definition only; zero schematic edits, zero symbol edits, zero netlists, zero OpenADA calls, and zero ngspice simulations executed.
