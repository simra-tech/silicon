// G1 digital macro wrapper: the hardened block is named g1_digital; it is a
// one-to-one wrapper around g1_digital_top so that the chip-level netlist can
// instantiate the macro under a stable name.
// SPDX-License-Identifier: Apache-2.0

module g1_digital #(
    parameter SEU_PLAIN_LEN = 256,
    parameter SEU_TMR_LEN   = 128
) (
    input  wire       osc_clk,
    input  wire       por_n,
    input  wire       en,
    input  wire       sclk,
    input  wire       sdi,
    output wire       sdo,
    output wire       cmp_clk,
    input  wire       cmp_soft,
    input  wire       cmp_hard,
    output wire [7:0] dac_soft,
    output wire [7:0] dac_hard,
    output wire       trip_set_sel,
    output wire       trip_d,
    output wire       clr_d,
    output wire       fast_en,
    input  wire       tripped,
    output wire       trip,
    output wire       gate_en,
    output wire       fault_n,
    output wire [1:0] trip_cause,
    output wire       osc_en,
    output wire [3:0] osc_trim,
    output wire       t2f_en,
    output wire       t2f_mode,
    output wire       bgr_r4,
    output wire       clk_div_out
);
    g1_digital_top #(.SEU_PLAIN_LEN(SEU_PLAIN_LEN), .SEU_TMR_LEN(SEU_TMR_LEN)) u_core (
        .osc_clk(osc_clk), .por_n(por_n), .en(en),
        .sclk(sclk), .sdi(sdi), .sdo(sdo),
        .cmp_clk(cmp_clk), .cmp_soft(cmp_soft), .cmp_hard(cmp_hard),
        .dac_soft(dac_soft), .dac_hard(dac_hard), .trip_set_sel(trip_set_sel),
        .trip_d(trip_d), .clr_d(clr_d), .fast_en(fast_en), .tripped(tripped),
        .trip(trip), .gate_en(gate_en), .fault_n(fault_n), .trip_cause(trip_cause),
        .osc_en(osc_en), .osc_trim(osc_trim),
        .t2f_en(t2f_en), .t2f_mode(t2f_mode), .bgr_r4(bgr_r4),
        .clk_div_out(clk_div_out));
endmodule
