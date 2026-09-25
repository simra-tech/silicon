// G1_SEU: triple-redundant register with majority vote and rewrite.
// Three copies load the same next value every cycle; the output is the
// bitwise majority, so a single upset in one copy is corrected at the next
// clock. The copies are separate instances of g1_tmr_copy whose flops carry
// the yosys 'keep' attribute: without it, opt_merge collapses the three
// identical flops into one after flattening (verified: 2408 -> 1703 flops).
// In the flat netlist the copies stay addressable by instance name
// (<reg>.u_a / u_b / u_c) for placement regions.
// SPDX-License-Identifier: Apache-2.0

module g1_tmr_copy #(
    parameter W = 8,
    parameter [W-1:0] RST = {W{1'b0}}
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [W-1:0] d,
    output reg  [W-1:0] q
);
    (* keep *) always @(posedge clk or negedge rst_n) begin
        if (!rst_n) q <= RST;
        else        q <= d;
    end
endmodule

module g1_tmr_reg #(
    parameter W = 8,
    parameter [W-1:0] RST = {W{1'b0}}
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [W-1:0] d,
    output wire [W-1:0] q
);
    wire [W-1:0] qa, qb, qc;
    g1_tmr_copy #(.W(W), .RST(RST)) u_a (.clk(clk), .rst_n(rst_n), .d(d), .q(qa));
    g1_tmr_copy #(.W(W), .RST(RST)) u_b (.clk(clk), .rst_n(rst_n), .d(d), .q(qb));
    g1_tmr_copy #(.W(W), .RST(RST)) u_c (.clk(clk), .rst_n(rst_n), .d(d), .q(qc));
    assign q = (qa & qb) | (qa & qc) | (qb & qc);
endmodule
