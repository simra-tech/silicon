// G1_SEU: one copy of a free-running shift-register chain. Every stage loads
// its d input at every clock; the parent supplies d = {previous stage values,
// input bit}, which for the TMR register is the majority vote of the three
// copies, so the vote is rewritten into all copies at every shift. There is
// deliberately no clock enable: sg13g2 has no enable flop, and a per-bit mux
// costs 18 um2 on top of the 49 um2 flop. The flops carry the yosys 'keep'
// attribute so that synthesis cannot merge the three TMR copies (copies b and
// c have identical inputs); in the flat netlist each copy stays addressable by
// instance name (u_seu.u_tmr_a/b/c.*) for placement regions.
// SPDX-License-Identifier: Apache-2.0

module g1_seu_chain #(
    parameter LEN = 256
) (
    input  wire           clk,
    input  wire           rst_n,
    input  wire [LEN-1:0] d,
    output reg  [LEN-1:0] q
);
    (* keep *) always @(posedge clk or negedge rst_n) begin
        if (!rst_n) q <= {LEN{1'b0}};
        else        q <= d;
    end
endmodule
