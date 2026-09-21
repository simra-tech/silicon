// SPDX-License-Identifier: Apache-2.0
// Integration dry-run core: all G1 macros of record as black boxes, in place of
// g1_core_placeholder (same port list, so g1_chip_top needs no change).
// Wiring follows blocks/g1_trip/INTERFACE.md, blocks/g1_t2f/INTERFACE.md and
// blocks/g1_ctrl/layout/PINS.md. Power pins are under USE_POWER_PINS; the 3.3 V
// macros take VDDA (pin 7, PLAN.md D14) and the core VSS
// (flow/config_dryrun.yaml, PDN_MACRO_CONNECTIONS).

`default_nettype none

module g1_core_placeholder (
`ifdef USE_POWER_PINS
    inout  wire  VDD,
    inout  wire  VSS,       // core and analog ground (D14)
    inout  wire  VDDA,      // 3.3 V analog supply, pin 7 (D14)
`endif
    input  logic en_i,
    input  logic sclk_i,
    input  logic sdi_i,
    output logic gate_o,
    output logic fault_n_o,
    output logic sdo_o,
    output logic temp_out_o,
    inout  wire  sense_p, sense_n, trip_set, vref,
    inout  wire  g_shared, d_std, d_elt,       // device pins -> g1_dose_macro
    inout  wire  hbt_e, hbt_b, hbt_c           // device pins -> g1_dut_macro
);

    // ---- digital <-> analog nets -------------------------------------------
    logic       osc_clk, osc_en;
    logic [3:0] osc_trim;
    logic       cmp_clk, cmp_soft, cmp_hard;
    logic [7:0] dac_soft, dac_hard;
    logic       trip_d, clr_d, fast_en, tripped;
    logic       t2f_en_12, t2f_mode_12, bgr_r4_12;      // 1.2 V
    logic       t2f_en_33, t2f_mode_33, bgr_r4_33;      // 3.3 V, after g1_ls_up
    /* verilator lint_off UNUSEDSIGNAL */
    logic       trip, gate_en, fault_n_dig, trip_set_sel, clk_div_out;
    logic [1:0] trip_cause;
    /* verilator lint_on UNUSEDSIGNAL */

    // ---- analog nets (3.3 V domain) ----------------------------------------
    wire iptat, pbias, pcasc, vref_bgr, vbe, dvbe;      // g1_bgr outputs
    wire isense, vref_buf, vped;                        // g1_sense outputs

    // ---- digital macro (1.2 V) ---------------------------------------------
    g1_digital u_digital (
`ifdef USE_POWER_PINS
        .VDD(VDD), .VSS(VSS),
`endif
        .osc_clk(osc_clk), .por_n(1'b1), .en(en_i), .sclk(sclk_i), .sdi(sdi_i), .sdo(sdo_o),
        .cmp_clk(cmp_clk), .cmp_soft(cmp_soft), .cmp_hard(cmp_hard),
        .dac_soft(dac_soft), .dac_hard(dac_hard), .trip_set_sel(trip_set_sel),
        .trip_d(trip_d), .clr_d(clr_d), .fast_en(fast_en), .tripped(tripped),
        .trip(trip), .gate_en(gate_en), .fault_n(fault_n_dig), .trip_cause(trip_cause),
        .osc_en(osc_en), .osc_trim(osc_trim),
        .t2f_en(t2f_en_12), .t2f_mode(t2f_mode_12), .bgr_r4(bgr_r4_12), .clk_div_out(clk_div_out));

    // ---- oscillator (1.2 V) ------------------------------------------------
    g1_osc u_osc (
`ifdef USE_POWER_PINS
        .VDD(VDD), .VSS(VSS),
`endif
        .en(osc_en), .trim(osc_trim), .osc_clk(osc_clk));

    // ---- bandgap (3.3 V) ---------------------------------------------------
    g1_bgr u_bgr (
`ifdef USE_POWER_PINS
        .vdd(VDDA), .vss(VSS),
`endif
        .r4(bgr_r4_33), .vref(vref_bgr), .iptat(iptat), .pbias(pbias), .pcasc(pcasc),
        .vbe(vbe), .dvbe(dvbe));
    assign vref = vref_bgr;                             // VREF pad (padres), monitor

    // ---- temperature to frequency (3.3 V + 1.2 V output stage) -------------
    g1_t2f u_t2f (
`ifdef USE_POWER_PINS
        .vdd(VDDA), .vdd12(VDD), .vss(VSS),
`endif
        .pbias(pbias), .pcasc(pcasc), .vref(vref_bgr), .en(t2f_en_33), .mode(t2f_mode_33),
        .fout(temp_out_o));

    // ---- sense amplifier (3.3 V) -------------------------------------------
    g1_sense u_sense (
`ifdef USE_POWER_PINS
        .vdd(VDDA), .vss(VSS),
`endif
        .sense_p(sense_p), .sense_n(sense_n), .iptat(iptat), .vref(vref_bgr),
        .isense(isense), .vref_buf(vref_buf), .vped(vped));

    // ---- trip comparators and DACs (1.2 V + 3.3 V shifters) ----------------
    g1_trip u_trip (
`ifdef USE_POWER_PINS
        .VDD(VDD), .IOVDD(VDDA), .VSS(VSS),
`endif
        .ISENSE(isense), .VREF(vref_buf), .dac_soft(dac_soft), .dac_hard(dac_hard),
        .clk(cmp_clk), .cmp_soft(cmp_soft), .cmp_hard(cmp_hard));

    // ---- gate driver latch (1.2 V logic, 3.3 V latch) ----------------------
    g1_gate u_gate (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vdda(VDDA), .vss(VSS),
`endif
        .trip_d(trip_d), .clr_d(clr_d), .en_core(en_i), .hard_cmp(cmp_hard), .fast_en(fast_en),
        .gate_core(gate_o), .tripped(tripped), .fault_core(fault_n_o));

    // ---- level shifters 1.2 V -> 3.3 V --------------------------------------
    g1_ls_up u_ls_r4   (.in(bgr_r4_12),   .out(bgr_r4_33)
`ifdef USE_POWER_PINS
        , .vdd(VDD), .vdda(VDDA), .vss(VSS)
`endif
    );
    g1_ls_up u_ls_mode (.in(t2f_mode_12), .out(t2f_mode_33)
`ifdef USE_POWER_PINS
        , .vdd(VDD), .vdda(VDDA), .vss(VSS)
`endif
    );
    g1_ls_up u_ls_en   (.in(t2f_en_12),   .out(t2f_en_33)
`ifdef USE_POWER_PINS
        , .vdd(VDD), .vdda(VDDA), .vss(VSS)
`endif
    );

    // ---- device macros (west side, pins 19-24) ------------------------------
    g1_dose_macro u_dose (
`ifdef USE_POWER_PINS
        .vss(VSS),
`endif
        .G_SHARED(g_shared), .D_STD(d_std), .D_ELT(d_elt));

    g1_dut_macro u_dut (
`ifdef USE_POWER_PINS
        .vss(VSS),
`endif
        .HBT_E(hbt_e), .HBT_B(hbt_b), .HBT_C(hbt_c));

    /* verilator lint_off UNUSEDSIGNAL */
    wire unused_trip_set = trip_set;                    // G1_TRIP has no TRIP_SET input yet
    wire unused_vped = vped;
    wire unused_vbe = vbe, unused_dvbe = dvbe;
    /* verilator lint_on UNUSEDSIGNAL */

endmodule

`default_nettype wire
