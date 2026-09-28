> **Self-assessment (2026-09-28): TRL 5.** Every TRL1 to TRL5 criterion below is met on design data,
> with two stated limits: the clean LVS report is the projected-reference full-chip LVS (the canonical
> unprojected LVS fails on the PDK `sg13g2_io` reference semantics, documented under
> `SoC1816-main/verification/lvs/`), and no stimulus-dependent power model is supplied (static supply
> currents are simulated). TRL6 is not claimed: the chip is a stand-alone test chip, not a hard IP
> for digital-on-top integration. TRL7 is not reached: the dedicated test chip is designed and its
> pad ring documented, but nothing has been fabricated or measured. Evidence links point into
> https://github.com/simra-tech/silicon `designs/g1-guardian/` (`R/` below).

# Mixed-Signal IP Quality Assessment using TRL scale

The provided set of the quality assessment criteria, using TRL (Technology Readiness Level) scale, is a tool for designers to auto evaluate a submitted design. The purpose of this tool is to
have a short overview of IP in terms of its maturity.

---

## TRL1 - Basic principles observed

- [x] Is the IP functionality clearly described?  
  R/README.md and R/specification/G1_TOP_LEVEL_SPECIFICATION.md §1
- [x] Is the IP principle of operation explained in detail?  
  R/specification/G1_TOP_LEVEL_SPECIFICATION.md §2 (block table) and the block READMEs
- [x] Are the IP architecture design equations fully listed?  
  trip timer, DAC code, T2F frequency and bandgap relations in the block READMEs (R/blocks/*/README.md)
- [x] Do authors supply any mixed-signal HDL functional model (e.g. Verilog-A) of the IP?  
  behavioural block models and the digital RTL in R/blocks/g1_top/sim (behavioural campaigns SOFT_BEHAVIORAL_20260922.md, TRANSITIONS_BEHAVIORAL_20260922.md) and R/blocks/g1_ctrl/rtl
- [x] Are functional simulation results of the IP reported for a typical case?  
  R/blocks/g1_top/sim/FULLCHIP_CDL_R4_20260927.md (tt/27 °C)

## TRL2 - Concept formulation

- [x] Is the IP architecture described at block level?  
  R/specification/G1_TOP_LEVEL_SPECIFICATION.md §2
- [x] Are the specifications of each individual block of the IP architecture clearly identified?  
  R/specification/G1_TOP_LEVEL_SPECIFICATION.md §2 and the parameter classification in R/README.md
- [x] If the IP architecture can be configured by means of internal registers, is their mapping declared?  
  R/specification/G1_REGISTER_MAP.md (map 1.2)
- [x] Do authors supply a complete test bench to validate the IP block-level architecture?  
  R/blocks/g1_top/sim/decks and campaigns (chip deck `run_top.py`)
- [x] Is any verification procedure given to check the IP block-level performance figures?  
  R/blocks/g1_top/sim/check_campaign.py and the acceptance criteria in the campaign records
- [x] Are architectural simulation results of the IP reported for a typical case?  
  R/blocks/g1_top/sim/campaigns/RESULTS_20260925.md

## TRL3 - Proof of concept at schematic level

- [x] Are the IP schematics available at transistor level (analog parts) and gate level (digital parts)?  
  xschem schematics under R/blocks/*/ and the gate netlist of the digital macro under R/blocks/g1_ctrl
- [x] Are all dependencies of the IP schematics on logic libraries declared?  
  PDK `sg13g2_stdcell` and `sg13g2_io` only, pinned in R/README.md "Built against"
- [x] Are the analog IP ports fully specified at electrical level?  
  pin map and electrical conditions in R/specification/G1_TOP_LEVEL_SPECIFICATION.md §3 and doc/Datasheet.md
- [x] Are the digital IP ports fully specified at logical level (e.g. protocols)?  
  three-wire serial interface in R/specification/G1_REGISTER_MAP.md
- [x] Do authors supply a mixed-signal test bench to validate the IP schematics?  
  R/blocks/g1_top/sim (ngspice chip deck with RTL co-simulation)
- [x] Is any verification procedure given to check the IP schematic performance figures?  
  R/blocks/g1_top/sim/check_campaign.py, block qualification records under R/blocks/*/sim/qualification
- [x] Are mixed-signal simulation results of the IP schematics reported for a typical case?  
  R/blocks/g1_top/sim/campaigns/RESULTS_20260925.md

## TRL4 - Full design at schematic level

- [x] Are the mixed-signal simulation results of the IP schematics extended to process, supply and temperature (PVT) corners?  
  72-cell campaign (tt/ss/ff, −40/27/85/125 °C, supplies ±10 %) in R/blocks/g1_top/sim/campaigns/RESULTS_20260925.md; post-layout corners in FULLCHIP_CDL_R4_PHASE2_20260927.md
- [x] Are the mixed-signal simulation results of the IP schematics extended to technology mismatching?  
  bandgap 300-sample and T2F 300-sample mismatch runs (R/blocks/g1_bgr/sim/qualification, R/blocks/g1_t2f/README.md); full-chip mismatch not run
- [x] Are the authors defining the mixed-signal supply domains of the IP schematics and their individual power requirements?  
  VDD 1.2 V, IOVDD 3.3 V, VDDA 3.3 V with simulated supply currents in R/README.md and doc/Datasheet.md
- [ ] Does the IP description include any power consumption model (e.g. as a function of input stimuli)?  
  not supplied; only static supply currents are simulated

## TRL5 - Full design at layout level

- [x] Is the IP complete layout available?  
  release/v.1.0.0/gds/SoC1816.gds (full chip including pad ring and seal ring)
- [x] Are all dependencies of the IP layout on logic libraries declared?  
  PDK `sg13g2_stdcell` and `sg13g2_io` cells at PDK commit 84374023, R/README.md
- [x] Do authors supply a clean DRC report?  
  SoC1816-main/verification/drc (main, maximal, precheck, density, antenna: 0 markers; IHP dev deck: 0 markers)
- [x] Do authors supply a clean LVS report?  
  SoC1816-main/verification/lvs/lvs_projected (passed, 62 956 devices, 22/22 pins); the canonical unprojected run fails on the PDK IO-cell reference semantics (lvs_canonical, documented)
- [x] Are post-layout mixed-signal simulation results of the IP layout reported for PVT corners?  
  R/blocks/g1_top/sim/FULLCHIP_CDL_R4_20260927.md and FULLCHIP_CDL_R4_PHASE2_20260927.md (block extractions, extracted interconnect, tt/ss/ff, −40 to 125 °C)

## TRL6 - Full design for SoC integration

- [ ] Does the IP come with suitable descriptors for digital-on-top integration (e.g. Liberty, LEF)?  
  not applicable: stand-alone test chip (the internal digital macro has LEF/Liberty views in R/blocks/g1_ctrl, the chip does not)
- [ ] Is the IP incorporating any BIST mechanism? If so, is it properly documented?  
  no BIST; the SEU canary registers are self-scrubbing monitors with readable counters, documented in R/specification/G1_REGISTER_MAP.md
- [x] Does the IP document fully define its digital interface?  
  R/specification/G1_REGISTER_MAP.md

## TRL7 - Lab demonstrator prototype

- [x] Has any dedicated test chip been designed for the hard IP?  
  this submission is the test chip
- [x] Is the hard IP test chip fully documented (e.g. pad ring)?  
  doc/Datasheet.md pin map, release/v.1.0.0/doc/BONDPLAN_20260925.md, R/padframe
- [ ] Are experimental results available from the IP dedicated test chip (Silicon proven)?  
  not run: nothing fabricated
- [ ] Do authors supply any comprehensive comparison between IP test chip and post-layout results?  
  not run

## TRL8 - In-field demonstrator prototype

- [ ] Has the hard IP been integrated in a SoC context?  
  no
- [ ] Are experimental IP results available from this SoC (Silicon proven)?  
  no
- [ ] Do authors supply any comprehensive comparison between IP SoC and test-chip results?  
  no

## TRL9 - Commercial application

- [x] Are the IP authors providing support for bug fixing or enhancement requests?  
  issues on https://github.com/simra-tech/silicon; contact agents@simra.tech
- [ ] Does the IP documentation include any training materials?  
  no
- [x] Are the EDA tools and versions used for developing the IP documented?  
  doc/info.json `tools` and R/README.md "Built against"
- [ ] Is the hard IP integrated in any commercial IC?  
  no
