// Testbench for the D27 phase-current correction r1_icor (revision 0.9): reads vectors
// {raw_a, raw_b, IA_OFS, IB_OFS, IA_GAIN, IB_GAIN} (12, 12, 12, 12, 16, 16 bit) from
// icor_<case>_stim.hex, applies each as one current pair (cur_valid pulse with the raw codes,
// as r1_gate drives them), waits for the result and logs per vector:
//   I <i_a> <i_b>
// Pass/fail: tb/icor_ref.py check (bit-exact against the integer model, saturation included).
// Plusargs: +dir=<path> +case=<name> +n=<vectors> +restart=1 (case restart: vector 2j is applied, vector 2j+1 follows
// 10 ticks later while the first is being corrected; only the result after vector 2j+1 is logged)
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps
module tb_icor;
    reg clk = 0, rst_n = 0;
    always #16.667 clk = ~clk;
    reg cur_valid = 0;
    reg [11:0] raw_a = 0, raw_b = 0, ofs_a = 0, ofs_b = 0;
    reg [15:0] gain_a = 16'h4000, gain_b = 16'h4000;
    wire [11:0] i_a, i_b;
    reg [79:0] stim [0:16383];
    r1_icor dut (.clk(clk), .rst_n(rst_n), .cur_valid(cur_valid), .raw_a(raw_a), .raw_b(raw_b),
                 .ofs_a(ofs_a), .ofs_b(ofs_b), .gain_a(gain_a), .gain_b(gain_b), .i_a(i_a), .i_b(i_b));
    reg [1023:0] dir_s, case_s;
    reg [8*256-1:0] fn;
    integer n, k, fo, rs;
    initial begin
        if (!$value$plusargs("dir=%s", dir_s)) dir_s = ".";
        if (!$value$plusargs("case=%s", case_s)) case_s = "id";
        if (!$value$plusargs("n=%d", n)) n = 4096;
        if (!$value$plusargs("restart=%d", rs)) rs = 0;
        $sformat(fn, "%0s/icor_%0s_stim.hex", dir_s, case_s);  $readmemh(fn, stim);
        $sformat(fn, "%0s/icor_%0s_out.txt", dir_s, case_s);   fo = $fopen(fn, "w");
        $fdisplay(fo, "# tb_icor case %0s n %0d", case_s, n);
        #100 rst_n = 1;
        $fdisplay(fo, "# reset values i_a %0d i_b %0d", i_a, i_b);
        for (k = 0; k < n; k = k + 1) begin
            @(negedge clk);
            {raw_a, raw_b, ofs_a, ofs_b, gain_a, gain_b} = stim[k];
            cur_valid = 1; @(negedge clk); cur_valid = 0;
            if (rs) begin
                repeat (10) @(negedge clk);
                k = k + 1;
                {raw_a, raw_b, ofs_a, ofs_b, gain_a, gain_b} = stim[k];
                cur_valid = 1; @(negedge clk); cur_valid = 0;
            end
            // the raw codes and the words stay until the next vector (they are registers in the chip)
            repeat (40) @(negedge clk);                    // I_A after 18 ticks, I_B after 35 (shift-add form)
            $fdisplay(fo, "I %0d %0d", i_a, i_b);
        end
        $display("tb_icor %0s: %0d vectors", case_s, n);
        $fclose(fo);
        $finish;
    end
endmodule
