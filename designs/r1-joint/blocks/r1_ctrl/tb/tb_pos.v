// Testbench (a) for r1_pos: drives sin/cos pairs from pos_<case>_stim.hex at
// the scheduler timing (track-and-hold at tick 100 + 30 k, codes valid 28 ticks
// later), loads register values from pos_<case>_regs.hex and logs:
//   M <meas_angle>                    corrected CORDIC angle per pair
//   T <tick> <pos_out> <velocity>     tracked output at each track-and-hold tick
// Pass/fail is decided by pos_ref.py check.
// Plusargs: +dir=<path> +case=<name> +n=<pairs>
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
    wire [11:0] amplitude, raw_sin, raw_cos;
    wire meas_stb, amp_low, amp_high, overspeed, track_err, overrun, pos_valid;

    r1_pos dut (
        .clk(clk), .rst_n(rst_n), .smp_sh(smp_sh), .smp_valid(smp_valid),
        .sin_code(sin_code), .cos_code(cos_code),
        .ofs_sin(regs[0][11:0]), .ofs_cos(regs[1][11:0]), .gain(regs[2]), .ph_sin(regs[3]),
        .ph_icos(regs[4]), .h3_amp(regs[5][7:0]), .h3_ph(regs[5][15:8]), .zero_ofs(16'd0),
        .dir(1'b0), .kp_sh(regs[6][3:0]), .ki_sh(regs[7][4:0]), .extrap(regs[8][7:0]),
        .amp_lo(8'd16), .amp_hi(8'd200), .ovs_lim(16'h7FFF),
        .pos_out(pos_out), .turns(turns), .velocity(velocity), .amplitude(amplitude),
        .raw_sin(raw_sin), .raw_cos(raw_cos), .meas_angle(meas_angle), .meas_stb(meas_stb),
        .amp_low(amp_low), .amp_high(amp_high), .overspeed(overspeed), .track_err(track_err),
        .overrun(overrun), .pos_valid(pos_valid));

    reg [1023:0] dir_s, case_s;
    reg [8*256-1:0] fn;
    integer n, k, fo, tick, n_ovr;
    initial begin
        if (!$value$plusargs("dir=%s", dir_s)) dir_s = ".";
        if (!$value$plusargs("case=%s", case_s)) case_s = "ideal";
        if (!$value$plusargs("n=%d", n)) n = 2000;
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

    initial begin
        n_ovr = 0;
        #100 rst_n = 1;
        for (k = 0; k < n; k = k + 1) begin
            // track-and-hold at tick 100 + 30k
            while (tick != 100 + 30 * k) @(negedge clk);
            smp_sh = 1;
            $fdisplay(fo, "T %0d %0d %0d", tick, pos_out, $signed(velocity));
            @(negedge clk); smp_sh = 0;
            while (tick != 100 + 30 * k + 28) @(negedge clk);
            {sin_code, cos_code} = stim[k];
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
