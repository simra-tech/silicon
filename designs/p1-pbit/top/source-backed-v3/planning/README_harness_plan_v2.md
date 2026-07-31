# Read-Only Top V2 Electrical Testbench Harness Plan V2

## 1. Scope & Status Notice
This document specifies a read-only electrical testbench harness plan for the accepted **Top V2 Structural Candidate** (`cace_ihp_sg13g2_demo/xschem/candidates/p1_top_hier_v2/p1_top.sch`, SHA-256 `e91c46604e14e0de056f0aacb2c8e6976490d8453130e656a5653d1db7f5ca50`).
- **No schematic, symbol, or netlist edits performed.**
- **No electrical simulation executed.**
- **Engineering Status: PROVISIONAL / NOT EVALUATED.**

## 2. Seven Distinct Block Supply Rails
To avoid silent supply joins, all seven block supply-related ports are strictly maintained as distinct top-level testbench connections:
1. `NOISE_GEN_VCC`: 2.5V DC supply for noise generator collector load resistors RC1/RC2.
2. `NOISE_GEN_VSS`: 0.0V ground reference for noise generator substrate tap XTAP1.
3. `NOISE_AMP_VCC`: Analogue supply for preamplifier 2-stage active loads & bias dividers.
4. `NOISE_AMP_VSS`: Analogue ground reference for preamplifier degeneration & substrate taps.
5. `COMPARATOR_VCC_HBT`: 2.500V DC supply for CML comparator HBT loads and output followers.
6. `VDD`: 1.200V DC supply for CML-to-CMOS level shifters and digital output dividers.
7. `COMPARATOR_VSS`: 0.000V ground reference for comparator substrate taps and NMOS current sinks.

## 3. Retained Prior-Bench Stimulus Lineage vs Unresolved Top-Level Decisions

### Retained Prior-Bench Lineage (`LINEAGE_ONLY / UNKNOWN_TOP_DECISION`)
- **Noise Generator Standalone Testbench (`cace_ihp_sg13g2_demo/runs/p1_noise_gen_run/tb_p1_noise_gen.spice`, SHA-256 `1bc05c2814996ec2e9372da263aa2941f5b89dfb370eeb34de20bf6da822cf64`):**
  - Line 17: `VCC vcc 0 DC 2.5` (2.5V positive supply)
  - Line 20: `VCM b_cm 0 DC 0.872` (0.872V common-mode base bias)
  - Line 10: `ISET e VSS DC 2.0m` (2.0mA tail emitter bias current sink)
- **Full-Array Comparator Testbench (`tb_full_array_code0_modelvalid_2x8_900ua.cir`, SHA-256 `5a391a7292b48994f61d276bae88b6fe0ef892c813186f08f3e68da56452aca0`):**
  - Line 83: `VCC_HBT VCC 0 DC 2.500` (2.500V HBT CML supply)
  - Line 84: `VDD VDD 0 DC 1.200` (1.200V CMOS supply)
  - Line 85: `VSS VSS 0 DC 0.000` (0.000V ground reference)

### Unresolved Top-Level Decisions (`UNKNOWN_TOP_DECISION`)
1. **`VB1` / `VB2` Input Base Bias:** Whether common-mode bias $V_{CM} = 0.872	ext{V}$ is driven externally via top pins or generated internally via an integrated bias divider network.
2. **`IE` Tail Emitter Current Sink:** Whether 2.0mA tail current sink $I_{SET}$ is placed in the external testbench harness or integrated as an internal bias cell.
3. **Supply Rail Consolidation:** Which of the seven distinct supply rails may eventually be joined at the top level for PCB/pad minimization.

## 4. Directory File Count Notice
The candidate directory `cace_ihp_sg13g2_demo/xschem/candidates/p1_top_hier_v2/` contains **15 total directory files**:
- **14 listed artifacts** in `p1_top_v2_manifest_v2.tsv`
- **1 non-self-listed manifest file** (`p1_top_v2_manifest_v2.tsv` itself)
