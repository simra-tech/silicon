// R1_CTRL: two-flop synchroniser for level or toggle signals entering the clk
// domain. Latency 2 cycles. Same structure as G1 g1_sync2 (copied, not shared).
// SPDX-License-Identifier: Apache-2.0

module r1_sync2 #(
    parameter W = 1,
    parameter RST_VAL = 0
) (
    input  wire         clk,
    input  wire         rst_n,   // asynchronous, active low
    input  wire [W-1:0] d,
    output wire [W-1:0] q
);
    reg [W-1:0] s0, s1;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s0 <= {W{RST_VAL[0]}};
            s1 <= {W{RST_VAL[0]}};
        end else begin
            s0 <= d;
            s1 <= s0;
        end
    end
    assign q = s1;
endmodule
