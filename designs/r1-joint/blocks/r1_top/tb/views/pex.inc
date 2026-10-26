* R1 full-chip testbench (track T10), block view "pex": the extracted netlists. TEMPLATE, NOT COMPLETE (2026-10-26).
* Same cell names and pins as views/sch.inc: r1_afe r1_isense r1_safe r1_bgr r1_bias r1_osc r1_t2f r1_gate_lv t10_ls
* r1_adc. run_tb.py --view pex fills @G1_RESULTS_ROOT@ and refuses to run while a line starts with "*PENDING".
* Each block owner writes one .include (or a wrapper subckt with the canonical pin order) per cell.
*
* Extracted netlists that exist (run ids from the block READMEs; the file name inside the run is set by the owner):
*   r1_afe     layout E2, RC extraction        <G1_RESULTS_ROOT>/r1_afe/pex-e2-dev11/
*   r1_isense  layout b, RC extraction         <G1_RESULTS_ROOT>/r1_isense/ (run pex-20261021-b)
*   r1_osc     layout r2d, RC extraction       <G1_RESULTS_ROOT>/r1_osc/ (run pex-rc-20261021-r2d)
*   r1_bias    RC extraction                   <G1_RESULTS_ROOT>/r1_bias/pex-rc-20261021-c/
*   r1_bgr     RC extraction                   <G1_RESULTS_ROOT>/r1_bgr/ (run pex-rc-20261021-b)
*PENDING r1_afe r1_isense r1_osc r1_bias r1_bgr: include lines not written yet (wrapper to the canonical pins needed)
*PENDING r1_safe: only the comparator cell and the string were extracted (pex-cmp-20261021-a, pex-string-20261021-a)
*PENDING r1_t2f r1_gate_lv t10_ls: layout LVS clean, PEX not run
*PENDING r1_adc: no layout exists
*PENDING top-level wiring: no chip-level extraction (r1_top try e); the chip netlist r1_chip.sp has ideal top wires
* The MODEL parts of views/sch.inc (r1_adc wrapper: sequencer globals, vcm2/vcm sources, raw decoders; t10_ls wrapper)
* are copied unchanged into this view when it is completed.
