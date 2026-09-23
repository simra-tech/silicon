set ::env(CLOCK_NET) osc_clk
set ::env(STEP_ID) OpenROAD.CTS
set ::env(TECH_LEF) /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef
set ::env(MACRO_LEFS) ""
set ::env(STD_CELL_LIBRARY) sg13g2_stdcell
set ::env(PAD_CELL_LIBRARY) sg13g2_io
set ::env(VDD_PIN) VPWR
set ::env(GND_PIN) VGND
set ::env(TECH_LEFS) "\"*\" /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_tech.lef"
set ::env(PRIMARY_GDSII_STREAMOUT_TOOL) klayout
set ::env(DEFAULT_CORNER) nom_typ_1p20V_25C
set ::env(STA_CORNERS) "nom_fast_1p32V_m40C nom_slow_1p08V_125C nom_typ_1p20V_25C"
set ::env(RT_MIN_LAYER) Metal2
set ::env(RT_MAX_LAYER) TopMetal2
set ::env(SCL_GROUND_PINS) VSS
set ::env(SCL_POWER_PINS) VDD
set ::env(TRISTATE_CELLS) "\"sg13g2_ebufn_*\" \"sg13g2_einvn_*\""
set ::env(FILL_CELLS) "sg13g2_fill_1 sg13g2_fill_2"
set ::env(DECAP_CELLS) "\"sg13g2_decap_*\""
set ::env(CELL_LIBS) "\"*_typ_1p20V_25C\" \"/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_typ_1p20V_25C.lib /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/lib/sg13g2_io_typ_1p2V_3p3V_25C.lib\" \"*_fast_1p32V_m40C\" \"/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_fast_1p32V_m40C.lib /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/lib/sg13g2_io_fast_1p32V_3p6V_m40C.lib\" \"*_slow_1p08V_125C\" \"/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_slow_1p08V_125C.lib /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/lib/sg13g2_io_slow_1p08V_3p0V_125C.lib\""
set ::env(CELL_LEFS) /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/lef/sg13g2_stdcell.lef
set ::env(CELL_GDS) /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/gds/sg13g2_stdcell.gds
set ::env(CELL_VERILOG_MODELS) /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_stdcell.v
set ::env(CELL_SPICE_MODELS) /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/spice/sg13g2_stdcell.spice
set ::env(CELL_CDLS) /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/cdl/sg13g2_stdcell.cdl
set ::env(SYNTH_EXCLUDED_CELL_FILE) /foss/pdks/ihp-sg13g2/libs.tech/librelane/sg13g2_stdcell/synth_exclude.cells
set ::env(PNR_EXCLUDED_CELL_FILE) /foss/pdks/ihp-sg13g2/libs.tech/librelane/sg13g2_stdcell/pnr_exclude.cells
set ::env(OUTPUT_CAP_LOAD) 6.0
set ::env(MAX_FANOUT_CONSTRAINT) 10
set ::env(CLOCK_UNCERTAINTY_CONSTRAINT) 0.25
set ::env(CLOCK_TRANSITION_CONSTRAINT) 0.15
set ::env(TIME_DERATING_CONSTRAINT) 5
set ::env(IO_DELAY_CONSTRAINT) 20
set ::env(SYNTH_DRIVING_CELL) sg13g2_buf_4/X
set ::env(SYNTH_TIEHI_CELL) sg13g2_tiehi/L_HI
set ::env(SYNTH_TIELO_CELL) sg13g2_tielo/L_LO
set ::env(SYNTH_BUFFER_CELL) sg13g2_buf_1/A/X
set ::env(PLACE_SITE) CoreSite
set ::env(CELL_PAD_EXCLUDE) "\"sg13g2_fill_*\" \"sg13g2_decap_*\""
set ::env(DIODE_CELL) sg13g2_antennanp/A
set ::env(DESIGN_NAME) g1_digital
set ::env(CLOCK_PERIOD) 100
set ::env(CLOCK_PORT) osc_clk
set ::env(VDD_NETS) VDD
set ::env(GND_NETS) VSS
set ::env(DIE_AREA) "0 0 360 360"
set ::env(FALLBACK_SDC) ${REPOSITORY}/designs/g1-guardian/blocks/g1_ctrl/flow/g1_digital.sdc
set ::env(PAD_LIBS) ""
set ::env(PAD_LEFS) /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/lef/sg13g2_io.lef
set ::env(PAD_GDS) /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/gds/sg13g2_io.gds
set ::env(PAD_VERILOG_MODELS) /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/verilog/sg13g2_io.v
set ::env(PAD_SPICE_MODELS) /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/spice/sg13g2_io.spi
set ::env(PAD_CDLS) /foss/pdks/ihp-sg13g2/libs.ref/sg13g2_io/cdl/sg13g2_io.cdl
set ::env(PAD_CORNER) sg13g2_Corner
set ::env(PAD_FILLERS) "sg13g2_Filler10000 sg13g2_Filler4000 sg13g2_Filler2000 sg13g2_Filler1000 sg13g2_Filler400 sg13g2_Filler200"
set ::env(PAD_SITE_NAME) sg13g2_ioSite
set ::env(PAD_CORNER_SITE_NAME) sg13g2_cornerSite
set ::env(PAD_BONDPAD_NAME) bondpad_70x70
set ::env(PAD_BONDPAD_WIDTH) 70
set ::env(PAD_BONDPAD_HEIGHT) 70
set ::env(PAD_BONDPAD_OFFSETS) "\"sg13g2_IOPad*\" \"5.0 -70.0\""
set ::env(PAD_EDGE_SPACING) 140
set ::env(PAD_ROTATION_HORIZONTAL) R0
set ::env(PAD_ROTATION_VERTICAL) R0
set ::env(PAD_ROTATION_CORNER) R0
set ::env(SET_RC_VERBOSE) 0
set ::env(LAYERS_RC) "\"*\" \"Metal1 \\\"res 0.00854576 cap 1E-10\\\" Metal2 \\\"res 0.00253519 cap 0.000169121\\\" Metal3 \\\"res 0.00154329 cap 0.000182832\\\" Metal4 \\\"res 0.000631424 cap 0.000166454\\\" Metal5 \\\"res 0.000684051 cap 0.0000857431\\\"\""
set ::env(VIAS_R) "\"*\" \"Cont \\\"res 0.0022\\\" Via1 \\\"res 0.0020\\\" Via2 \\\"res 0.0020\\\" Via3 \\\"res 0.0020\\\" Via4 \\\"res 0.0020\\\" TopVia1 \\\"res 0.0004\\\" TopVia2 \\\"res 0.00022\\\"\""
set ::env(PDN_CONNECT_MACROS_TO_GRID) 1
set ::env(PDN_ENABLE_GLOBAL_CONNECTIONS) 1
set ::env(PNR_SDC_FILE) ${REPOSITORY}/designs/g1-guardian/blocks/g1_ctrl/flow/g1_digital.sdc
set ::env(DEDUPLICATE_CORNERS) 0
set ::env(PL_OPTIMIZE_MIRRORING) 1
set ::env(PL_MAX_DISPLACEMENT_X) 500
set ::env(PL_MAX_DISPLACEMENT_Y) 100
set ::env(DPL_CELL_PADDING) 0
set ::env(CTS_SINK_CLUSTERING_ENABLE) 1
set ::env(CTS_CLK_MAX_WIRE_LENGTH) 0
set ::env(CTS_DISABLE_POST_PROCESSING) 0
set ::env(CTS_DISTANCE_BETWEEN_BUFFERS) 0
set ::env(CTS_ROOT_BUFFER) sg13g2_buf_16
set ::env(CTS_CLK_BUFFERS) "sg13g2_buf_8 sg13g2_buf_4 sg13g2_buf_2"
set ::env(CTS_APPLY_NDR) half
set ::env(CURRENT_ODB) ${REPOSITORY}/designs/g1-guardian/blocks/g1_ctrl/flow/runs/run7/34-openroad-detailedplacement/g1_digital.odb
set ::env(SAVE_ODB) {${RESULTS_ROOT}/digital-cts-baseline-20260923-r1/g1_digital.odb}
set ::env(SAVE_DEF) {${RESULTS_ROOT}/digital-cts-baseline-20260923-r1/g1_digital.def}
set ::env(SAVE_SDC) {${RESULTS_ROOT}/digital-cts-baseline-20260923-r1/g1_digital.sdc}
set ::env(SAVE_NL) {${RESULTS_ROOT}/digital-cts-baseline-20260923-r1/g1_digital.nl.v}
set ::env(SAVE_PNL) {${RESULTS_ROOT}/digital-cts-baseline-20260923-r1/g1_digital.pnl.v}
