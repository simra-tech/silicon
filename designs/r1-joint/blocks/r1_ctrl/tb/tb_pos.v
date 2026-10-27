// Testbench (a) for r1_pos: drives sin/cos pairs from pos_<case>_stim.hex at
// the scheduler timing (track-and-hold at tick 100 + P k, codes valid 28 ticks
// later; P = 30 in revision 0.2, P = 36 for the D17 ADC frame), loads register
// values from pos_<case>_regs.hex and logs:
//   M <meas_angle>                    corrected CORDIC angle per pair
//   T <tick> <pos_out> <velocity> <turns>   tracked output at each track-and-hold tick
// Pass/fail is decided by pos_ref.py check.
// Plusargs: +dir=<path> +case=<name> +n=<pairs> +pair=<ticks per pair, default 30>
//   +lat=<ticks from hold to valid codes, default 28; may exceed the frame (pipelined)>
//   +skip=<N>: every N-th frame slot carries no encoder pair (the current pair once per
//   PWM period); pair k is held in slot k + k/(N-1). 0 = no skipped slots (default).
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps
module tb_pos;
    reg clk = 0, rst_n = 0;
    always #16.667 clk = ~clk;     // 30 MHz
    reg smp_sh = 0, smp_valid = 0;
    reg [11:0] sin_code = 12'h800, cos_code = 12'h800;
    reg [15:0] regs [0:8];
    reg [23:0] stim [0:4095];
    wire [17:0] pos_out, meas_angle;
    wire [15:0] turns, velocity;
    wire [11:0] amplitude;
    wire meas_stb, amp_low, amp_high, overspeed, track_err, overrun, pos_valid;

    r1_pos dut (
        .clk(clk), .rst_n(rst_n), .smp_sh(smp_sh), .smp_valid(smp_valid),
        .sin_code(sin_code), .cos_code(cos_code),
        .ofs_sin(regs[0][11:0]), .ofs_cos(regs[1][11:0]), .gain(regs[2]), .cos_gain(16'h4000), .ph_sin(regs[3]),
        .ph_icos(regs[4]), .h3_amp(regs[5][7:0]), .h3_ph(regs[5][15:8]), .zero_ofs(16'd0),
        .dir(1'b0), .kp_sh(regs[6][3:0]), .ki_sh(regs[7][4:0]), .extrap(regs[8][7:0]),
        .amp_lo(8'd16), .amp_hi(8'd200), .ovs_lim(16'h7FFF),
        .pos_out(pos_out), .turns(turns), .velocity(velocity), .amplitude(amplitude),
        .meas_angle(meas_angle), .meas_stb(meas_stb),
        .amp_low(amp_low), .amp_high(amp_high), .overspeed(overspeed), .track_err(track_err),
        .overrun(overrun), .pos_valid(pos_valid));

    reg [1023:0] dir_s, case_s;
    reg [8*256-1:0] fn;
    integer n, k, fo, tick, n_ovr, pt, skp, js;
    initial begin
        if (!$value$plusargs("dir=%s", dir_s)) dir_s = ".";
        if (!$value$plusargs("case=%s", case_s)) case_s = "ideal";
        if (!$value$plusargs("n=%d", n)) n = 2000;
        if (!$value$plusargs("pair=%d", pt)) pt = 30;
        if (!$value$plusargs("skip=%d", skp)) skp = 0;
        $sformat(fn, "%0s/pos_%0s_regs.hex", dir_s, case_s);  $readmemh(fn, regs);
        $sformat(fn, "%0s/pos_%0s_stim.hex", dir_s, case_s);  $readmemh(fn, stim);
        $sformat(fn, "%0s/pos_%0s_out.txt", dir_s, case_s);   fo = $fopen(fn, "w");
        $fdisplay(fo, "# tb_pos case %0s n %0d", case_s, n);
    end

    // tick counter: tick 0 = first rising edge after reset release
    always @(posedge clk) if (rst_n) tick <= tick + 1;
    initial tick = 0;

    always @(posedge clk) if (meas_stb) $fdisplay(fo, "M %0d", meas_angle);
    always @(posedge clk) if (overrun) n_ovr = n_ovr + 1;

    // hold and data processes run in parallel, so the data of pair k may arrive
    // after the hold of pair k + 1 (D18: 22-tick frame, latency +lat ticks)
    integer lat, kd, jd, done_h;
    initial begin
        n_ovr = 0; done_h = 0;
        if (!$value$plusargs("lat=%d", lat)) lat = 28;
        #100 rst_n = 1;
        for (k = 0; k < n; k = k + 1) begin
            js = (skp > 1) ? k + k / (skp - 1) : k;
            while (tick != 100 + pt * js) @(negedge clk);
            smp_sh = 1;
            $fdisplay(fo, "T %0d %0d %0d %0d", tick, pos_out, $signed(velocity), turns);
            @(negedge clk); smp_sh = 0;
        end
        done_h = 1;
    end
    initial begin
        #100;
        for (kd = 0; kd < n; kd = kd + 1) begin
            jd = (skp > 1) ? kd + kd / (skp - 1) : kd;
            while (tick != 100 + pt * jd + lat) @(negedge clk);
            {sin_code, cos_code} = stim[kd];
            smp_valid = 1;
            @(negedge clk); smp_valid = 0;
        end
        repeat (40) @(negedge clk);
        $fdisplay(fo, "# overruns %0d pos_valid %0d amplitude %0d", n_ovr, pos_valid, amplitude);
        $display("tb_pos %0s: %0d pairs, overruns %0d, pos_valid %0d, amplitude %0d, turns %0d",
                 case_s, n, n_ovr, pos_valid, amplitude, turns);
        $fclose(fo);
        $finish;
    end
endmodule
