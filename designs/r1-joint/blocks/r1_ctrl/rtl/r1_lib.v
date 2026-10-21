// R1_CTRL: storage primitives for host-written configuration (revision 0.2).
//
// r1_cgate: clock gate (negative-level enable latch + AND), the standard
//   latch-based integrated clock gate. gclk pulses high during the clk high
//   phase of the cycle after en was high at the falling clk edge. Behavioural;
//   Yosys maps the enable latch to sg13g2_dllrq_1 through the PDK latch_map.v
//   (sg13g2_lgcp_1 is on the PDK synth_exclude list, so it is not used).
// r1_creg: W-bit configuration word stored in level-sensitive latches with an
//   asynchronous reset (sg13g2_dlhrq_1, 27.2 um2, against 49.0 um2 for
//   sg13g2_dfrbpq_1 plus a write-enable multiplexer). The latch is transparent
//   while gclk is high. Reset values other than 0 are stored inverted.
//   Rules for use: d must be stable while gclk is high (the SPI receive word is
//   stable while CS_N is high, which covers the write); q changes once per
//   write, half a cycle after the gating edge.
//   Simulation only: gclk is delayed by 10 ps, so that flip-flops clocked by
//   the same clk edge read the value from before the latch opens, as in
//   hardware (zero-delay simulation would otherwise race).
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps

module r1_cgate (
    input  wire clk,
    input  wire en,
    output wire gclk
);
    reg en_l;
    always @* if (!clk) en_l = en;
`ifdef SYNTHESIS
    assign gclk = clk & en_l;
`else
    assign #0.01 gclk = clk & en_l;
`endif
endmodule

module r1_creg #(
    parameter W = 16,
    parameter [W-1:0] RV = {W{1'b0}}
) (
    input  wire         rst_n,
    input  wire         gclk,
    input  wire [W-1:0] d,
    output wire [W-1:0] q
);
    reg [W-1:0] s;
    always @* begin
        if (!rst_n)    s = {W{1'b0}};
        else if (gclk) s = d ^ RV;
    end
    assign q = s ^ RV;
endmodule

// r1_cword: one host-writable configuration word at register address A
// (clock gate + latch word). wr is a one-tick pulse from a flip-flop; addr and
// d are stable from before the pulse until after the following cycle.
module r1_cword #(
    parameter W = 16,
    parameter [W-1:0] RV = {W{1'b0}},
    parameter [6:0] A = 7'h00
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         wr,
    input  wire [6:0]   addr,
    input  wire [W-1:0] d,
    output wire [W-1:0] q
);
`ifdef R1_CFG_GATED
    // revision 0.4: flip-flops on a clock-gated clock, one gate per word. Same
    // write edge as the enabled flop form (wr is high in cycle N; the gate latch
    // takes it in the low phase of N; the flops see the rising edge that ends N),
    // without a recirculating multiplexer per bit (-18 um2 per bit).
    wire gclk;
    r1_cgate u_cg (.clk(clk), .en(wr && (addr == A)), .gclk(gclk));
    reg [W-1:0] r;
    always @(posedge gclk or negedge rst_n)
        if (!rst_n) r <= RV;
        else        r <= d;
    assign q = r;
`elsif R1_CFG_FLOPS
    // revision 0.3 design of record (every flow sets R1_CFG_FLOPS): flip-flops
    // with write enable. The latch form below failed sign-off STA at the slow
    // corner (LibreLane runs t2, t4); the flop form closes 42 MHz at all three
    // corners (run t5). README revision 0.3.
    reg [W-1:0] r;
    always @(posedge clk or negedge rst_n)
        if (!rst_n) r <= RV;
        else if (wr && (addr == A)) r <= d;
    assign q = r;
`else
    wire gclk;
    r1_cgate u_cg (.clk(clk), .en(wr && (addr == A)), .gclk(gclk));
    r1_creg #(.W(W), .RV(RV)) u_r (.rst_n(rst_n), .gclk(gclk), .d(d), .q(q));
`endif
endmodule
