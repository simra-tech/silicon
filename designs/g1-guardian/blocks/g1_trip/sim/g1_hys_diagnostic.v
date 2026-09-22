// Isolated static-configuration diagnostic, not a production control macro.
// Ports are positional in d_cosim; vectors are MSB first. Read-only probes only.
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps
module g1_hys_diagnostic (
    input wire osc_clk, input wire en,
    input wire cmp_soft, input wire cmp_hard,
    output wire cmp_clk,
    output wire [7:0] dac_soft, output wire [7:0] dac_hard,
    output wire [23:0] soft_count,
    output wire cmp_soft_s, output wire cmp_hard_s,
    output wire soft_mask, output wire soft_armed, output wire trip,
    output wire reset_released
);
    wire por_n = 1'b1;
    // Exact reset-release/divider logic copied from g1_digital_top.
    wire arst_n = por_n & en;
    reg rs0, rs1;
    always @(posedge osc_clk or negedge arst_n) begin
        if (!arst_n) begin
            rs0 <= 1'b0;
            rs1 <= 1'b0;
        end else begin
            rs0 <= 1'b1;
            rs1 <= rs0;
        end
    end
    wire rst_n = rs1;
    reg cmp_clk_q;
    always @(posedge osc_clk or negedge rst_n) begin
        if (!rst_n) cmp_clk_q <= 1'b0;
        else        cmp_clk_q <= ~cmp_clk_q;
    end
    assign cmp_clk = cmp_clk_q;
    assign reset_released = rst_n;
    assign soft_count = u_trip.soft_cnt;
    assign soft_mask = u_trip.soft_mask;
    g1_trip_timer u_trip (
        .clk(osc_clk), .rst_n(rst_n), .cmp_clk(cmp_clk_q),
        .cmp_soft(cmp_soft), .cmp_hard(cmp_hard), .tripped_a(1'b0),
        .soft_en(1'b1), .hard_en(1'b0), .retrig(1'b0), .force_trip(1'b0),
        .soft_time(16'd1), .decay(2'd0), .hyst_en(1'b1), .hyst_2(1'b0),
        .hard_n(8'd1), .inrush(8'd0), .hold_time(8'd1), .retry_max(8'd0),
        .dac_soft_code(8'd128), .dac_hard_code(8'd240), .sense_ofs(8'd0),
        .clear(1'b0), .clr_trip_cnt(1'b0), .clr_peak(1'b0),
        .trip(trip), .soft_armed(soft_armed),
        .cmp_soft_s(cmp_soft_s), .cmp_hard_s(cmp_hard_s),
        .dac_soft_out(dac_soft), .dac_hard_out(dac_hard)
    );
endmodule
