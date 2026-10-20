// R1_CTRL / r1_cmpcal: offset calibration of the four r1_safe window comparators
// (INTERFACES.md "safe -> ctrl"; r1_safe README open issue 1, option a).
//
// Comparator order (contract): 0 OC_A, 1 NEG_A, 2 OC_B, 3 NEG_B.
// The host starts a search with CTRL.CMP_CAL (W1). While the search runs
// (busy): every threshold output carries THR_ZERO (AZ_CFG[13:8]), the gates are
// held off and the comparator faults are blanked (r1_ctrl_top, r1_safe). The
// isense auto-zero window az_win (r1_gate, AZ_START / AZ_LEN) gives the zero
// input. All four comparators are searched at the same time, one decision per
// az_win, sampled at the last tick of the window (synchronised flag, 2 ticks
// old):
//   f = flag XOR POL[i]  (1: the threshold is still below the input -> raise the code)
//   successive approximation of the 6-bit code over 6 windows (start 32, then
//   keep or clear each bit), then a 7th window that checks the final code:
//   EXH[i] = (code == 63 and f == 1) or (code == 0 and f == 0)
//   (the toggle point lies outside the 6-bit range).
// Result: code[i] = the largest code at which f = 1; the toggle lies between
// code and code + 1. The codes are host-writable (CMP_CAL_A/B) for bench use;
// a search overwrites them.
// SPDX-License-Identifier: Apache-2.0

module r1_cmpcal #(
    parameter [3:0] POL = 4'b0000      // per comparator: 1 = flag high means "lower the code"
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,          // pulse (CTRL.CMP_CAL)
    input  wire        az_win,
    input  wire [3:0]  flag_s,         // synchronised comparator flags
    input  wire        wr_a, wr_b,     // host writes of CMP_CAL_A / _B
    input  wire [15:0] wdata,
    output wire [23:0] cal,            // {NEG_B, OC_B, NEG_A, OC_A}, 6 bits each
    output reg         busy,
    output reg         done,
    output reg  [3:0]  exh,
    output wire [15:0] rd_a,           // CMP_CAL_A read value
    output wire [15:0] rd_b
);
    reg [5:0] c0, c1, c2, c3;
    reg [2:0] step;                    // 5..0: decide bit step; 7: final check
    reg       az_d;
    wire      win_end = az_d & ~az_win;
    wire [3:0] f = flag_s ^ POL;

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

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            c0 <= 6'd32; c1 <= 6'd32; c2 <= 6'd32; c3 <= 6'd32;
            step <= 3'd0; az_d <= 1'b0; busy <= 1'b0; done <= 1'b0; exh <= 4'd0;
        end else begin
            az_d <= az_win;
            if (start) begin
                c0 <= 6'd32; c1 <= 6'd32; c2 <= 6'd32; c3 <= 6'd32;
                step <= 3'd5; busy <= 1'b1; done <= 1'b0; exh <= 4'd0;
            end else if (busy && win_end) begin
                if (step == 3'd7) begin
                    exh  <= {chk(c3, f[3]), chk(c2, f[2]), chk(c1, f[1]), chk(c0, f[0])};
                    busy <= 1'b0; done <= 1'b1;
                end else begin
                    c0 <= sar(c0, step, f[0]); c1 <= sar(c1, step, f[1]);
                    c2 <= sar(c2, step, f[2]); c3 <= sar(c3, step, f[3]);
                    step <= (step == 3'd0) ? 3'd7 : step - 3'd1;
                end
            end else if (!busy) begin
                if (wr_a) begin c0 <= wdata[5:0]; c1 <= wdata[13:8]; end
                if (wr_b) begin c2 <= wdata[5:0]; c3 <= wdata[13:8]; end
            end
        end
    end
    assign cal  = {c3, c2, c1, c0};
    assign rd_a = {1'b0, exh[1], c1, 1'b0, exh[0], c0};
    assign rd_b = {1'b0, exh[3], c3, 1'b0, exh[2], c2};
endmodule
