// R1_CTRL / r1_tapidx (revision 0.5): comparator tap-index adders for r1_safe.
// Contract: blocks/r1_safe/README.md ("DAC per comparator") and INTERFACES.md,
// "Signal ownership gaps found at assembly".
//   cell code  c = thr_oc            (OC cells, comparators 0 and 2)
//              c = 63 - thr_neg      (NEG cells, comparators 1 and 3)
//   calibration d = k - 32, k = 6-bit cal code (k = 32: no shift)
//   nP = 4c + ceil(d/2),  nN = 4(63 - c) - floor(d/2),  both clipped to 0..252
// Comparator order (contract): 0 OC_A, 1 NEG_A, 2 OC_B, 3 NEG_B; comparator i
// uses bits [6i +: 6] of thr and cal, and bits [8i +: 8] of tap_p and tap_n.
// thr is the effective threshold (THR_ZERO during a calibration search).
// The outputs are registered every clk, so they change one tick after thr or
// cal changes (this includes the end of a calibration search) and nP / nN of
// one comparator always change together. Reset values are the taps of the
// reset codes (thr = 63, cal = 32): OC nP 252 nN 0, NEG nP 0 nN 252.
// SPDX-License-Identifier: Apache-2.0

module r1_tapidx (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [23:0] thr,            // {NEG_B, OC_B, NEG_A, OC_A} thr codes, 6 bit each
    input  wire [23:0] cal,            // {NEG_B, OC_B, NEG_A, OC_A} cal codes, 6 bit each
    output reg  [31:0] tap_p,
    output reg  [31:0] tap_n
);
    // {nN, nP} for a cell code c and a calibration code k. With d = k - 32 the formula reduces to
    //   nP = 4 (c - 4)  + ((k + 1) >> 1)            ceil(d/2)  = ((k + 1) >> 1) - 16
    //   nN = 4 (~c - 4) + (32 - (k >> 1))           floor(d/2) = (k >> 1) - 16, ~c = 63 - c
    // i.e. 4 s + e with e = 0..32: s = base + (e >> 2) is a 7-bit add, e[1:0] are the two low result bits,
    // and the clip to 0..252 is s < 0 -> 0, s >= 63 -> 252. Same function as the contract form, checked
    // exhaustively by tb_tapidx.v (the first form, with 11-bit signed adders, was 7706 um^2).
    function [7:0] clip4;
        input signed [7:0] sbase;      // c - 4 or ~c - 4, -4..59
        input [5:0] e;                 // 0..32
        reg signed [7:0] sm;
        begin
            sm = sbase + $signed({3'b000, e[5:2]});
            if (sm < 8'sd0)        clip4 = 8'd0;
            else if (sm >= 8'sd63) clip4 = 8'd252;
            else                   clip4 = {sm[5:0], e[1:0]};
        end
    endfunction
    function [15:0] taps;
        input [5:0] c;
        input [5:0] k;
        reg [6:0] kp1;
        begin
            kp1 = {1'b0, k} + 7'd1;
            taps = {clip4($signed({2'b00, ~c}) - 8'sd4, 6'd32 - {1'b0, k[5:1]}),
                    clip4($signed({2'b00, c}) - 8'sd4, kp1[6:1])};
        end
    endfunction

    wire [5:0] c0 = thr[5:0],          c1 = ~thr[11:6],
               c2 = thr[17:12],        c3 = ~thr[23:18];
    wire [15:0] t0 = taps(c0, cal[5:0]),   t1 = taps(c1, cal[11:6]),
                t2 = taps(c2, cal[17:12]), t3 = taps(c3, cal[23:18]);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tap_p <= {8'd0, 8'd252, 8'd0, 8'd252};
            tap_n <= {8'd252, 8'd0, 8'd252, 8'd0};
        end else begin
            tap_p <= {t3[7:0], t2[7:0], t1[7:0], t0[7:0]};
            tap_n <= {t3[15:8], t2[15:8], t1[15:8], t0[15:8]};
        end
    end
endmodule
