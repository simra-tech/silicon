// G1_CTRL: two-flop synchroniser (metastability filter) for level or toggle
// signals crossing into the clk domain. Latency 2 cycles.
// SPDX-License-Identifier: Apache-2.0

module g1_sync2 #(
    parameter W = 1
) (
    input  wire         clk,
    input  wire         rst_n,   // asynchronous, active low
    input  wire [W-1:0] d,
    output wire [W-1:0] q
);
    reg [W-1:0] s0, s1;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s0 <= {W{1'b0}};
            s1 <= {W{1'b0}};
        end else begin
            s0 <= d;
            s1 <= s0;
        end
    end
    assign q = s1;
endmodule
