// One-hot weight check of r1_adcw (revision 0.4, coordinator item: raw decision readback through the
// normal code path). For every decision i: weight W_i = 4*k, all other weights 0, raw = all ones or only
// bit i. Expected code = k when b_i = 1, 0 when b_i = 0 (no rounding, no clamping while k <= 4095).
// Run: iverilog -g2005 rtl/r1_adcw.v tb/tb_adcw_onehot.v && vvp a.out ; prints "# n checks, m failed".
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps
module tb_adcw_onehot;
    reg clk = 0, rst_n = 0;
    always #16.667 clk = ~clk;
    reg         valid = 0;
    reg  [13:0] raw = 0;
    reg  [195:0] w = 0;
    wire        cv;
    wire [11:0] code;
    r1_adcw dut (.clk(clk), .rst_n(rst_n), .valid(valid), .raw(raw), .w(w), .code_valid(cv), .code(code));
    integer i, kk, nchk, nfail, ks;
    reg [11:0] got;
    reg [13:0] kval [0:3];
    task conv(input [13:0] r, output [11:0] c);
        begin
            @(negedge clk); raw = r; valid = 1;
            @(negedge clk); valid = 0;
            c = 12'hxxx;
            repeat (8) begin @(posedge clk); #1 if (cv) c = code; end
        end
    endtask
    initial begin
        nchk = 0; nfail = 0;
        kval[0] = 1; kval[1] = 3; kval[2] = 77; kval[3] = 4095;
        #100 rst_n = 1;
        for (i = 0; i < 14; i = i + 1) begin
            for (ks = 0; ks < 4; ks = ks + 1) begin
                w = 196'd0; w[14*i +: 14] = {kval[ks][11:0], 2'b00};     // 4 * k, units of 1/4 LSB
                if (ks == 3 && i < 12) w[14*i +: 14] = 14'd16380;           // k = 4095 where the field allows it
                kk = w[14*i +: 14] / 4;
                conv(14'h3FFF, got);  nchk = nchk + 1;
                if (got !== kk[11:0]) begin nfail = nfail + 1; $display("FAIL i=%0d w=%0d raw=ones got %0d want %0d", i, w[14*i +: 14], got, kk); end
                conv(14'h3FFF & ~(14'd1 << i), got); nchk = nchk + 1;
                if (got !== 12'd0) begin nfail = nfail + 1; $display("FAIL i=%0d bit clear got %0d want 0", i, got); end
                conv(14'd1 << i, got); nchk = nchk + 1;
                if (got !== kk[11:0]) begin nfail = nfail + 1; $display("FAIL i=%0d only bit set got %0d want %0d", i, got, kk); end
            end
        end
        $display("# %0d checks, %0d failed", nchk, nfail);
        if (nfail == 0) $display("ALL TESTS PASSED");
        $finish;
    end
endmodule
