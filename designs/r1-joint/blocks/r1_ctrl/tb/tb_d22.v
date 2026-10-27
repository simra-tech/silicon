// Testbench for the D22 channel correction of r1_pos (revision 0.8): drives
// sin/cos code pairs from d22_<case>_stim.hex at a 22-tick frame (track-and-hold
// at tick 100 + 22 k, codes valid 19 ticks later), loads the correction registers
// from d22_<case>_regs.hex and logs per pair:
//   M <meas_angle> <amplitude>      corrected CORDIC angle (2^18 = one turn), ADC LSB
// Register file order: SIN_OFS, COS_OFS, SIN_GAIN, COS_GAIN, PH_SIN, PH_ICOS, H3.
// Pass/fail: tb/d22_ref.py check (bit-exact against the integer model).
// Plusargs: +dir=<path> +case=<name> +n=<pairs, default 4096>
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps
module tb_d22;
    reg clk = 0, rst_n = 0;
    always #16.667 clk = ~clk;
    reg smp_sh = 0, smp_valid = 0;
    reg [11:0] sin_code = 12'h800, cos_code = 12'h800;
    reg [15:0] regs [0:6];
    reg [23:0] stim [0:4095];
    wire [17:0] pos_out, meas_angle;
    wire [15:0] turns, velocity;
    wire [11:0] amplitude;
    wire meas_stb, amp_low, amp_high, overspeed, track_err, overrun, pos_valid;

    r1_pos dut (
        .clk(clk), .rst_n(rst_n), .smp_sh(smp_sh), .smp_valid(smp_valid),
        .sin_code(sin_code), .cos_code(cos_code),
        .ofs_sin(regs[0][11:0]), .ofs_cos(regs[1][11:0]), .gain(regs[2]), .cos_gain(regs[3]),
        .ph_sin(regs[4]), .ph_icos(regs[5]), .h3_amp(regs[6][7:0]), .h3_ph(regs[6][15:8]),
        .zero_ofs(16'd0), .dir(1'b0), .kp_sh(4'd2), .ki_sh(5'd11), .extrap(8'd0),
        .amp_lo(8'd16), .amp_hi(8'd200), .ovs_lim(16'h7FFF),
        .pos_out(pos_out), .turns(turns), .velocity(velocity), .amplitude(amplitude),
        .meas_angle(meas_angle), .meas_stb(meas_stb),
        .amp_low(amp_low), .amp_high(amp_high), .overspeed(overspeed), .track_err(track_err),
        .overrun(overrun), .pos_valid(pos_valid));

    reg [1023:0] dir_s, case_s;
    reg [8*256-1:0] fn;
    integer n, k, fo, tick, n_ovr, n_m;
    initial begin
        if (!$value$plusargs("dir=%s", dir_s)) dir_s = ".";
        if (!$value$plusargs("case=%s", case_s)) case_s = "raw";
        if (!$value$plusargs("n=%d", n)) n = 4096;
        $sformat(fn, "%0s/d22_%0s_regs.hex", dir_s, case_s);  $readmemh(fn, regs);
        $sformat(fn, "%0s/d22_%0s_stim.hex", dir_s, case_s);  $readmemh(fn, stim);
        $sformat(fn, "%0s/d22_%0s_out.txt", dir_s, case_s);   fo = $fopen(fn, "w");
        $fdisplay(fo, "# tb_d22 case %0s n %0d", case_s, n);
    end
    initial tick = 0;
    always @(posedge clk) if (rst_n) tick <= tick + 1;
    always @(posedge clk) if (meas_stb) begin $fdisplay(fo, "M %0d %0d", meas_angle, amplitude); n_m = n_m + 1; end
    always @(posedge clk) if (overrun) n_ovr = n_ovr + 1;
    initial begin
        n_ovr = 0; n_m = 0;
        #100 rst_n = 1;
        for (k = 0; k < n; k = k + 1) begin
            while (tick != 100 + 22 * k) @(negedge clk);
            smp_sh = 1; @(negedge clk); smp_sh = 0;
            while (tick != 100 + 22 * k + 19) @(negedge clk);
            {sin_code, cos_code} = stim[k];
            smp_valid = 1; @(negedge clk); smp_valid = 0;
        end
        repeat (40) @(negedge clk);
        $fdisplay(fo, "# overruns %0d pairs %0d", n_ovr, n_m);
        $display("tb_d22 %0s: %0d pairs in, %0d angles out, overruns %0d", case_s, n, n_m, n_ovr);
        $fclose(fo);
        $finish;
    end
endmodule
