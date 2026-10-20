// R1_CTRL / r1_cmpcal: offset calibration of the four r1_safe window comparators
// (INTERFACES.md "safe -> ctrl"; contract of r1_safe revision 3, sim/cal_model.py).
//
// Revision 0.3: two-sided search, result relative to the ideal toggle point.
// Comparator order (contract): 0 OC_A, 1 NEG_A, 2 OC_B, 3 NEG_B.
// The host starts a search with CTRL.CMP_CAL (W1). While the search runs
// (busy): every threshold output carries THR_ZERO (AZ_CFG[13:8], 14 per the
// contract), the gates are held off and the comparator faults are blanked
// (r1_ctrl_top, r1_safe). With the gates off the isense input is at zero
// current; the isense output is not valid inside az_win, so each decision is
// taken in the zero-current time after az_win (INTERFACES.md, change 2026-10-20):
//   az_win falls -> STEP ticks settle -> preset code -> STEP ticks -> probe code
//   -> STEP ticks -> sample the synchronised flag (f = flag XOR POL).
// If az_win rises again before the sample, the decision is dropped and taken
// again after the next window. STEP = 16 << AZ_CFG[15:14] ticks (reset 32).
// The comparators have hysteresis. The preset puts the comparator in a known
// state before each probe, so every decision answers one monotonic question:
//   pass R: preset 0 (threshold far below the input, output high);
//           f = 1 at the probe <=> the output has not released (dn(T) <= Vcal)
//   pass T: preset 63 (threshold far above the input, output low);
//           f = 1 at the probe <=> the output has tripped (up(T) < Vcal)
// Each pass: 6-bit successive approximation (start 32; f = 1 keeps the bit),
// then one check window: code = the largest k with f = 1, and
//   EXH = (code == 63 and f == 1) or (code == 0 and f == 0).
// k_rel = a + 1 (pass R result a), k_trip = b (pass T result b),
//   S = k_rel + k_trip,  cal = 32 + floor((S - IDEAL2) / 2), saturated to
//   0..63 (EXH). IDEAL2 = floor(2 k_ideal) in half codes, from CMP_CAL_IDEAL
//   (reset 72 for OC: k_ideal 36.31, 55 for NEG: k_ideal 27.69). This equals
//   r1_safe's k_cal = 32 + round((k_rel + k_trip)/2 - k_ideal) exactly while
//   k_ideal is not a multiple of 1/2 (tb/cmpcal_ref.py).
// 14 windows per search (2 x (6 + 1)). The codes are host-writable
// (CMP_CAL_A/B) when no search runs; a search overwrites them. CMP_CAL_A/B
// read the applied codes, so during a search they show the preset/probe codes.
// SPDX-License-Identifier: Apache-2.0

module r1_cmpcal #(
    parameter [3:0] POL = 4'b0000      // per comparator: 1 = flag high means "lower the code"
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,          // pulse (CTRL.CMP_CAL)
    input  wire        az_win,
    input  wire [3:0]  flag_s,         // synchronised comparator flags
    input  wire [1:0]  step_sel,       // AZ_CFG[15:14]: STEP = 16 << step_sel ticks
    input  wire [6:0]  ideal_oc,       // CMP_CAL_IDEAL[6:0], half codes
    input  wire [6:0]  ideal_neg,      // CMP_CAL_IDEAL[14:8]
    input  wire        wr_a, wr_b,     // host writes of CMP_CAL_A / _B
    input  wire [15:0] wdata,
    output wire [23:0] cal,            // {NEG_B, OC_B, NEG_A, OC_A}, 6 bits each (registered)
    output reg         busy,
    output reg         done,
    output reg  [3:0]  exh,
    output wire [15:0] rd_a,           // CMP_CAL_A read value
    output wire [15:0] rd_b
);
    reg [5:0] c0, c1, c2, c3;          // search codes
    reg [5:0] a0, a1, a2, a3;          // pass R results
    reg [5:0] p0, p1, p2, p3;          // applied codes (to r1_safe) = stored results when idle (host-writable)
    reg [3:0] exr;                     // pass R exhaustion
    reg [2:0] step;                    // 5..0: decide bit step; 7: check window
    reg       pass_t;                  // 0: pass R, 1: pass T
    reg [1:0] ph;                      // 0 wait, 1 settle, 2 preset, 3 probe
    reg [6:0] cnt;
    reg       az_d;
    wire      win_end = az_d & ~az_win;
    wire [3:0] f = flag_s ^ POL;
    wire [6:0] stepm1 = (7'd16 << step_sel) - 7'd1;    // 15, 31, 63, 127
    wire [5:0] preset = pass_t ? 6'd63 : 6'd0;

    function [5:0] sar;                // decide the current bit, set the next one
        input [5:0] c; input [2:0] s; input fb;
        reg [5:0] t;
        begin
            t = c;
            if (!fb) t[s] = 1'b0;
            if (s != 3'd0) t[s - 3'd1] = 1'b1;
            sar = t;
        end
    endfunction
    function chk;
        input [5:0] c; input fb;
        begin chk = (c == 6'd63 && fb) || (c == 6'd0 && !fb); end
    endfunction
    // result: {sat, code}; S = a + 1 + b; w = S + 128 - IDEAL2 (2..255); cal = w/2 - 32
    function [6:0] fin;
        input [5:0] a, b; input [6:0] id2;
        reg [7:0] w; reg [6:0] h;
        begin
            w = {2'b00, a} + {2'b00, b} + 8'd129 - {1'b0, id2};
            h = w[7:1];
            if (h < 7'd32)      fin = {1'b1, 6'd0};
            else if (h > 7'd95) fin = {1'b1, 6'd63};
            else                fin = {1'b0, h[5:0] - 6'd32};
        end
    endfunction
    wire [6:0] r0 = fin(a0, c0, ideal_oc), r1 = fin(a1, c1, ideal_neg),
               r2 = fin(a2, c2, ideal_oc), r3 = fin(a3, c3, ideal_neg);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            c0 <= 6'd32; c1 <= 6'd32; c2 <= 6'd32; c3 <= 6'd32;
            a0 <= 6'd0;  a1 <= 6'd0;  a2 <= 6'd0;  a3 <= 6'd0;
            p0 <= 6'd32; p1 <= 6'd32; p2 <= 6'd32; p3 <= 6'd32;
            exr <= 4'd0; step <= 3'd0; pass_t <= 1'b0; ph <= 2'd0; cnt <= 7'd0;
            az_d <= 1'b0; busy <= 1'b0; done <= 1'b0; exh <= 4'd0;
        end else begin
            az_d <= az_win;
            if (start) begin
                c0 <= 6'd32; c1 <= 6'd32; c2 <= 6'd32; c3 <= 6'd32;
                step <= 3'd5; pass_t <= 1'b0; ph <= 2'd0; cnt <= 7'd0;
                busy <= 1'b1; done <= 1'b0; exh <= 4'd0; exr <= 4'd0;
            end else if (busy) begin
                if (az_win) begin
                    ph <= 2'd0;                            // drop an unfinished decision
                end else if (win_end) begin
                    ph <= 2'd1; cnt <= 7'd0;
                end else if (ph != 2'd0) begin
                    if (cnt != stepm1) cnt <= cnt + 7'd1;
                    else begin
                        cnt <= 7'd0;
                        if (ph == 2'd1) begin
                            ph <= 2'd2; p0 <= preset; p1 <= preset; p2 <= preset; p3 <= preset;
                        end else if (ph == 2'd2) begin
                            ph <= 2'd3; p0 <= c0; p1 <= c1; p2 <= c2; p3 <= c3;
                        end else begin                     // sample
                            ph <= 2'd0;
                            if (step != 3'd7) begin
                                c0 <= sar(c0, step, f[0]); c1 <= sar(c1, step, f[1]);
                                c2 <= sar(c2, step, f[2]); c3 <= sar(c3, step, f[3]);
                                step <= (step == 3'd0) ? 3'd7 : step - 3'd1;
                            end else if (!pass_t) begin    // end of pass R
                                a0 <= c0; a1 <= c1; a2 <= c2; a3 <= c3;
                                exr <= {chk(c3, f[3]), chk(c2, f[2]), chk(c1, f[1]), chk(c0, f[0])};
                                c0 <= 6'd32; c1 <= 6'd32; c2 <= 6'd32; c3 <= 6'd32;
                                pass_t <= 1'b1; step <= 3'd5;
                            end else begin                 // end of pass T: result
                                p0 <= r0[5:0]; p1 <= r1[5:0]; p2 <= r2[5:0]; p3 <= r3[5:0];
                                exh <= exr | {r3[6], r2[6], r1[6], r0[6]} |
                                       {chk(c3, f[3]), chk(c2, f[2]), chk(c1, f[1]), chk(c0, f[0])};
                                busy <= 1'b0; done <= 1'b1;
                            end
                        end
                    end
                end
            end else begin
                if (wr_a) begin p0 <= wdata[5:0]; p1 <= wdata[13:8]; end
                if (wr_b) begin p2 <= wdata[5:0]; p3 <= wdata[13:8]; end
            end
        end
    end
    assign cal  = {p3, p2, p1, p0};
    assign rd_a = {1'b0, exh[1], p1, 1'b0, exh[0], p0};    // during a search: the applied codes
    assign rd_b = {1'b0, exh[3], p3, 1'b0, exh[2], p2};
endmodule
