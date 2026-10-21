// Exhaustive testbench for r1_tapidx (revision 0.5). For every cell code c = 0..63 and every
// calibration code k = 0..63 each of the four lanes is driven once; lane i sees the pair (c_i, k_i) with
// c_i = (c + 7 i) mod 63+1 and k_i = (k + 13 i) mod 64, which is a bijection, so every lane
// covers all 4096 pairs (OC lanes 0 and 2, NEG lanes 1 and 3; for a NEG lane thr = 63 - c).
// Log line per lane and pair: "<lane> <type> <c> <k> <nP> <nN>", compared by tb/tapidx_ref.py.
// +out=<file>
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps
module tb_tapidx;
    reg clk = 0, rst_n = 0;
    always #5 clk = ~clk;
    reg  [23:0] thr = 24'd0, cal = 24'd0;
    wire [31:0] tap_p, tap_n;
    r1_tapidx dut (.clk(clk), .rst_n(rst_n), .thr(thr), .cal(cal), .tap_p(tap_p), .tap_n(tap_n));
    integer c, k, i, ci, ki, fd, n, errs;
    reg [1023:0] ofile;
    reg [5:0] cc [0:3];
    reg [5:0] kk [0:3];
    initial begin
        if (!$value$plusargs("out=%s", ofile)) ofile = "tapidx_rtl.txt";
        fd = $fopen(ofile, "w");
        errs = 0; n = 0;
        // reset values
        #12; if (tap_p !== {8'd0, 8'd252, 8'd0, 8'd252} || tap_n !== {8'd252, 8'd0, 8'd252, 8'd0}) begin errs = errs + 1; $display("FAIL reset taps"); end
        rst_n = 1;
        for (c = 0; c < 64; c = c + 1)
            for (k = 0; k < 64; k = k + 1) begin
                for (i = 0; i < 4; i = i + 1) begin
                    ci = (c + 7 * i) % 64; ki = (k + 13 * i) % 64;
                    cc[i] = ci; kk[i] = ki;
                    // thr code: OC lanes thr = c, NEG lanes thr = 63 - c
                    thr[6*i +: 6] = (i % 2 == 1) ? (6'd63 - ci[5:0]) : ci[5:0];
                    cal[6*i +: 6] = ki[5:0];
                end
                @(posedge clk); @(posedge clk); #1;           // registered: valid one clock after the inputs
                for (i = 0; i < 4; i = i + 1) begin
                    $fdisplay(fd, "%0d %0d %0d %0d %0d %0d", i, i % 2, cc[i], kk[i], tap_p[8*i +: 8], tap_n[8*i +: 8]);
                    n = n + 1;
                end
            end
        $fclose(fd);
        $display("# %0d lane samples written", n);
        if (errs == 0) $display("DONE tapidx");
        $finish;
    end
endmodule
