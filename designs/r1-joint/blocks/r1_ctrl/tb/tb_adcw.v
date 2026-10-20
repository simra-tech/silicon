// Testbench for r1_adcw (ADC weight correction): applies the raw decisions of
// adcw_raw.hex (Python SAR model, adcw_ref.py) with the weights of
// adcw_w_<set>.hex at 15 ticks per conversion and logs every corrected code:
//   C <code>
// Pass/fail is decided by adcw_ref.py check (bit-exact against the integer
// model, DNL/INL with binary and calibrated weights).
// Plusargs: +dir=<path> +set=bin|cal +n=<points>
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps
module tb_adcw;
    reg clk = 0, rst_n = 0;
    always #16.667 clk = ~clk;
    reg         valid = 0;
    reg  [12:0] raw = 0;
    reg  [15:0] wmem [0:12];
    reg  [15:0] rmem [0:65535];
    wire [181:0] w;
    wire        cv;
    wire [11:0] code;
    genvar gi;
    generate for (gi = 0; gi < 13; gi = gi + 1) begin : g_w
        assign w[14*gi +: 14] = wmem[gi][13:0];
    end endgenerate
    r1_adcw dut (.clk(clk), .rst_n(rst_n), .valid(valid), .raw(raw), .w(w), .code_valid(cv), .code(code));

    reg [1023:0] dir_s, set_s;
    reg [8*256-1:0] fn;
    integer n, k, fo, nout;
    always @(posedge clk) if (cv) begin $fdisplay(fo, "C %0d", code); nout = nout + 1; end
    initial begin
        nout = 0;
        if (!$value$plusargs("dir=%s", dir_s)) dir_s = ".";
        if (!$value$plusargs("set=%s", set_s)) set_s = "bin";
        if (!$value$plusargs("n=%d", n)) n = 65536;
        $sformat(fn, "%0s/adcw_w_%0s.hex", dir_s, set_s); $readmemh(fn, wmem);
        $sformat(fn, "%0s/adcw_raw.hex", dir_s);         $readmemh(fn, rmem);
        $sformat(fn, "%0s/adcw_%0s_out.txt", dir_s, set_s); fo = $fopen(fn, "w");
        #100 rst_n = 1;
        for (k = 0; k < n; k = k + 1) begin
            @(negedge clk); raw = rmem[k][12:0]; valid = 1;
            @(negedge clk); valid = 0;
            repeat (13) @(negedge clk);
        end
        repeat (20) @(negedge clk);
        $display("tb_adcw %0s: %0d conversions, %0d codes", set_s, n, nout);
        $fclose(fo);
        $finish;
    end
endmodule
