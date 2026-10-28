* R1 full-chip testbench (track T10), block view "pex": the extracted netlists of record (sixth budget, 2026-10-28).
* run_tb.py --view pex builds the schematic view (views/sch.inc) with every option of the deck (subsets, fast view,
* ideal oscillator), then replaces each schematic block that is still in the deck by the section below. A stubbed or
* behavioural block stays stubbed or behavioural. Each section starts with "*T10PEX <schematic include>" or
* "*T10CELL <wrapper subckt in sch.inc>" and ends with "*T10END". "*T10SHA <file> <sha256>" lines are checked by the
* runner. Options on the *T10PEX line: DROP <subckt> (deck-local copy of the schematic file without that subckt, so the
* extracted cell replaces it), RENAME <old>=<new> (deck-local copy of the extracted file with the subckt renamed),
* CHIPBIAS (r1_chip.sp: XU_BIAS gets the revision-2 pins vref vref_b on vref_bg / vref_l; MODEL M6 removed).
* Blocks without an extraction of record keep the schematic: r1_t2f, r1_gate_lv / r1_gate_hv cells, r1_ls (t10_ls),
* and the r1_safe string, mux, level shifters and threshold DACs (only the comparator cell is extracted).
* Top-level routing has no extraction (r1_chip.sp wires are ideal; chip assembly try g pending).

*T10PEX r1_afe/schematic/r1_afe_revE.spice
*T10SHA @G1_RESULTS_ROOT@/r1_afe/pexrc-layout-e6-dev16/r1_afe_post_rc.spice ed92a2494ec936e7a9fa9c1410a3678d658c9e4bcb69ee414db82ad15ccf558e
* r1_afe layout E6 (dev16), RC extraction (fd0fcf4e4); same subckt name and pins as the schematic
.include @G1_RESULTS_ROOT@/r1_afe/pexrc-layout-e6-dev16/r1_afe_post_rc.spice
*T10END

*T10PEX r1_isense/schematic/r1_isense.spice
*T10SHA @G1_RESULTS_ROOT@/r1_isense/pex-20261026-c/rc/r1_isense_post.spice 1989529ba5df464802534b66a3b291db23c14ea03cef5e1c2a1135b33a44c2f1
* r1_isense layout c, RC extraction (pex-20261026-c, c09410f07); defines r1_ls (internal), r1_isense_ch, r1_isense
.include @G1_RESULTS_ROOT@/r1_isense/pex-20261026-c/rc/r1_isense_post.spice
*T10END

*T10PEX r1_safe/schematic/r1_safe.spice DROP r1_safe_cmp
*T10SHA @G1_RESULTS_ROOT@/r1_safe/pex-cmp-20261021-a/rc/r1_safe_cmp_pex.spice 598c5bd6f53f991d66f06191b7e3f98d2f95509bce5941d1f0e4aeaefd3e893d
* r1_safe: schematic of record except the comparator cell, which is the RC extraction pex-cmp-20261021-a (f65d55c49)
.include @G1_RESULTS_ROOT@/r1_safe/pex-cmp-20261021-a/rc/r1_safe_cmp_pex.spice
*T10END

*T10PEX r1_bgr/schematic/r1_bgr.spice
*T10SHA @G1_RESULTS_ROOT@/r1_bgr/pex-rc-20261021-b/r1_bgr_pex.spice 0b5a7299844a2359e42e86c30cc1719838c0c32bf00a350e1e9ae36c0303a055
* r1_bgr RC extraction (pex-rc-20261021-b, 3f5194f82)
.include @G1_RESULTS_ROOT@/r1_bgr/pex-rc-20261021-b/r1_bgr_pex.spice
*T10END

*T10PEX r1_bias/schematic/r1_bias_rev1d.spice RENAME r1_bias=r1_bias_r2pex CHIPBIAS
*T10SHA @G1_RESULTS_ROOT@/r1_bias/pex-rc-20261026-r2d/r1_bias_pex.spice 0ae828e6c431e12ab5cfa03dc7e82340c4017a164df1fe5a0de3bbd43883f1be
* r1_bias revision 2 RC extraction (pex-rc-20261026-r2d, ae4dfac95); contains the VREF buffer r1_vbuf (D20)
.include @RENAMED@
*T10END

*T10PEX r1_osc/schematic/r1_osc.spice
*T10SHA @G1_RESULTS_ROOT@/r1_osc/pex-rc-20261021-r2d/r1_osc_pex.spice c6d76aac02c310790dbea47e8362a6f663f070edaa097eea7b5711aff2184c77
* r1_osc r2d RC extraction (pex-rc-20261021-r2d, 679a97320); used only with --osc tl
.include @G1_RESULTS_ROOT@/r1_osc/pex-rc-20261021-r2d/r1_osc_pex.spice
*T10END

*T10CELL r1_adc
*T10SHA /work/designs/r1-joint/blocks/r1_adc/sim/post/r1_adc_post_rc_mb5.spice 7bf2b33fe2c6ddc544c4c754f8f37a9d4ee09bed36801e903b498b6360b949e9
*T10SHA /work/designs/r1-joint/blocks/r1_adc/sim/post/b5/sar/r1_adc_sar_gl_lumpc.spice 102f66b6a65f778556d45695f7a38ee7122dba367afe0e5a41c8bf97f841a59a
* r1_adc layout B5 (620b3130f): RC extraction merged (sim/post/r1_adc_post_rc_mb5.spice, subckt r1_adc_lay_sar) and the
* hardened SAR sub-macro as its gate-level netlist with SPEF lumped C (sim/post/b5/sar/r1_adc_sar_gl_lumpc.spice, cells from
* sg13g2_stdcell.spice, included by the deck). Instance lines as the ADC owner decks sim/post/b5/decks/b5/ref_tt_buf.cir
* (reference buffer of the layout, no ideal VREF). The SAR makes the timing and the valid; the testbench sequencer
* model (seq_* globals) is then unused and the ctrl takes adc_valid_a/b from the macro pins (T10_VALID_BRIDGE).
.include /work/designs/r1-joint/blocks/r1_adc/sim/post/r1_adc_post_rc_mb5.spice
.include /work/designs/r1-joint/blocks/r1_adc/sim/post/b5/sar/r1_adc_sar_gl_lumpc.spice
.subckt r1_adc adc_hold is_smp clk adc_start adc_sel adc_valid_a
+ adc_raw_a_0 adc_raw_a_1 adc_raw_a_2 adc_raw_a_3 adc_raw_a_4 adc_raw_a_5 adc_raw_a_6 adc_raw_a_7 adc_raw_a_8 adc_raw_a_9 adc_raw_a_10 adc_raw_a_11 adc_raw_a_12 adc_raw_a_13
+ adc_valid_b
+ adc_raw_b_0 adc_raw_b_1 adc_raw_b_2 adc_raw_b_3 adc_raw_b_4 adc_raw_b_5 adc_raw_b_6 adc_raw_b_7 adc_raw_b_8 adc_raw_b_9 adc_raw_b_10 adc_raw_b_11 adc_raw_b_12 adc_raw_b_13
+ por_n ain_sin_p ain_sin_n ain_cos_p ain_cos_n vcm2 ibias ain_isa_p ain_isa_n ain_isb_p ain_isb_n vcm vdda vdd vss vref_in cur_trk
XL adc_hold is_smp clk adc_start adc_sel adc_valid_a adc_raw_a_0 adc_raw_a_1 adc_raw_a_2 adc_raw_a_3 adc_raw_a_4
+ adc_raw_a_5 adc_raw_a_6 adc_raw_a_7 adc_raw_a_8 adc_raw_a_9 adc_raw_a_10 adc_raw_a_11 adc_raw_a_12 adc_raw_a_13 adc_valid_b adc_raw_b_0 adc_raw_b_1 adc_raw_b_2 adc_raw_b_3
+ adc_raw_b_4 adc_raw_b_5 adc_raw_b_6 adc_raw_b_7 adc_raw_b_8 adc_raw_b_9 adc_raw_b_10 adc_raw_b_11 adc_raw_b_12 adc_raw_b_13 por_n ain_sin_p ain_sin_n ain_cos_p
+ ain_cos_n vcm2 ibias ain_isa_p ain_isa_n ain_isb_p ain_isb_n vcm vdda vdd vss vref_in topap topan
+ topbp topbn sar_clka sar_clkab sar_clkb sar_clkbb sar_clkna sar_clknab sar_clknb sar_clknbb sar_cna0 sar_cna1 sar_cna10 sar_cna11
+ sar_cna12 sar_cna2 sar_cna3 sar_cna4 sar_cna5 sar_cna6 sar_cna7 sar_cna8 sar_cna9 sar_cnb0 sar_cnb1 sar_cnb10 sar_cnb11 sar_cnb12
+ sar_cnb2 sar_cnb3 sar_cnb4 sar_cnb5 sar_cnb6 sar_cnb7 sar_cnb8 sar_cnb9 sar_cpa0 sar_cpa1 sar_cpa10 sar_cpa11 sar_cpa12 sar_cpa2
+ sar_cpa3 sar_cpa4 sar_cpa5 sar_cpa6 sar_cpa7 sar_cpa8 sar_cpa9 sar_cpb0 sar_cpb1 sar_cpb10 sar_cpb11 sar_cpb12 sar_cpb2 sar_cpb3
+ sar_cpb4 sar_cpb5 sar_cpb6 sar_cpb7 sar_cpb8 sar_cpb9 sar_oan sar_oann sar_oanp sar_oap sar_obn sar_obnn sar_obnp sar_obp
+ sar_trka0 sar_trka1 sar_trkb0 sar_trkb1 sar_mclk vrefa vrefla vdd vss r1_adc_lay_sar
XSAR adc_hold adc_sel adc_start adc_valid_a adc_valid_b clk sar_clka sar_clkab sar_clkb sar_clkbb sar_clkna
+ sar_clknab sar_clknb sar_clknbb cur_trk is_smp sar_mclk sar_oan sar_oann sar_oanp sar_oap sar_obn sar_obnn sar_obnp sar_obp
+ por_n sar_trka0 sar_trka1 sar_trkb0 sar_trkb1 adc_raw_a_13 adc_raw_a_12 adc_raw_a_11 adc_raw_a_10 adc_raw_a_9 adc_raw_a_8 adc_raw_a_7 adc_raw_a_6 adc_raw_a_5
+ adc_raw_a_4 adc_raw_a_3 adc_raw_a_2 adc_raw_a_1 adc_raw_a_0 adc_raw_b_13 adc_raw_b_12 adc_raw_b_11 adc_raw_b_10 adc_raw_b_9 adc_raw_b_8 adc_raw_b_7 adc_raw_b_6 adc_raw_b_5
+ adc_raw_b_4 adc_raw_b_3 adc_raw_b_2 adc_raw_b_1 adc_raw_b_0 sar_cna12 sar_cna11 sar_cna10 sar_cna9 sar_cna8 sar_cna7 sar_cna6 sar_cna5 sar_cna4
+ sar_cna3 sar_cna2 sar_cna1 sar_cna0 sar_cnb12 sar_cnb11 sar_cnb10 sar_cnb9 sar_cnb8 sar_cnb7 sar_cnb6 sar_cnb5 sar_cnb4 sar_cnb3
+ sar_cnb2 sar_cnb1 sar_cnb0 sar_cpa12 sar_cpa11 sar_cpa10 sar_cpa9 sar_cpa8 sar_cpa7 sar_cpa6 sar_cpa5 sar_cpa4 sar_cpa3 sar_cpa2
+ sar_cpa1 sar_cpa0 sar_cpb12 sar_cpb11 sar_cpb10 sar_cpb9 sar_cpb8 sar_cpb7 sar_cpb6 sar_cpb5 sar_cpb4 sar_cpb3 sar_cpb2 sar_cpb1
+ sar_cpb0 vdd vss r1_adc_sar_glc
* MODEL (as views/sch.inc): common-mode outputs vcm2 (AFE) and vcm (isense), ideal 0.6 V through 1 kOhm
Vcm2s vcm2i vss 0.6
Rcm2 vcm2i vcm2 1k
Vcms vcmi vss 0.6
Rcm vcmi vcm 1k
.ends r1_adc
*T10END

