# Read-Only Bias & Supply Provenance Audit V2

## 1. Observed Facts vs Proposed Architecture

### Observed Source & Testbench Facts (100% Byte-for-Byte Round-Trip Verified)
1. **Source Schematics & Hierarchical Netlists Have Isolated Supply Ports:**
   - Noise Generator `p1_noise_gen.sch` defines ports `VCC` and `VSS`.
   - Noise Preamplifier `p1_noise_amp.sch` defines ports `VCC` and `VSS`.
   - Comparator `p1_comparator.sch` defines ports `VCC_HBT` (2.5V), `VDD` (1.2V), and `VSS` (0.0V).
2. **Noise Generator Bias Ports (`VB1`, `VB2`, `IE`) & Lineage Difference:**
   - Source `p1_noise_gen.sch` defines input pins `VB1` (line 18), `VB2` (line 19), and inout pin `IE` (line 20).
   - In `p1_noise_gen.sch`, `VB1` connects to the base of HBT `Q1`, `VB2` connects to the base of HBT `Q2`, and `IE` connects to the shared emitter node of `Q1/Q2`.
   - **Standalone Testbench Drive:** Retained standalone testbench `cace_ihp_sg13g2_demo/runs/p1_noise_gen_run/tb_p1_noise_gen.spice` drives common-mode bias `VCM b_cm 0 DC 0.872` (line 20), AC stimulus `VVIN b1 b2 DC 0 AC 1` (line 21), and tail emitter bias current sink `ISET e VSS DC 2.0m` (line 10).
3. **Sampler Campaign Decks (`tb_chunk{0..3}_{27c,-40c}.cir`):**
   - All 8 current root sampler decks use PWL/E-source noise stimulus and instantiate the noise preamplifier and comparator, but **do NOT instantiate the source-backed noise-generator hierarchy**.
4. **Testbench Stimulus Drive vs Top-Level Design Authority:**
   - Retained testbench deck `tb_full_array_code0_modelvalid_2x8_900ua.cir` contains stimulus lines:
     - Line 83: `VCC_HBT VCC 0 DC 2.500` (`TESTBENCH_DRIVE`)
     - Line 84: `VDD VDD 0 DC 1.200` (`TESTBENCH_DRIVE`)
     - Line 85: `VSS VSS 0 DC 0.000` (`TESTBENCH_DRIVE`)
   - Testbench DC voltage sources represent simulation stimulus drive only and **must not be converted into top-level schematic decisions or silent supply joins**.

### Proposed Top-Level Architecture & Unresolved Questions (`UNRESOLVED / TOP_ARCHITECTURE`)
1. **Supply Domain Partitioning:**
   - No supply joining is performed in this audit.
   - Proposed top-level net names remain strictly separated: `NOISE_GEN_VCC`, `NOISE_AMP_VCC`, `COMPARATOR_VCC_HBT`, `NOISE_GEN_VSS`, `NOISE_AMP_VSS`, `COMPARATOR_VSS`, and `VDD`.
   - Unresolved Question: Whether analogue noise generator supplies, preamplifier supplies, and CML comparator supplies should share top-level PCB/chip power pins or maintain dedicated supply pads for noise isolation.
2. **Noise Generator Bias Network Integration:**
   - Unresolved Question: Whether top-level macro will incorporate an integrated bias network for `VB1`, `VB2`, and `IE` or accept external bias inputs.
