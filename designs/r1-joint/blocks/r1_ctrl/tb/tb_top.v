// Chip-level testbench for r1_ctrl_top (testbenches b..f and cal of the r1_ctrl
// README, revision 0.3).
//   +test=biss | ssi | spi | gate | safe | cal | calmc | tap | ana | disc | cdc | v07 | d22 | d27    test group
//   (d27, revision 0.9: IA/IB offset and gain words, CRC coverage, bit-exact I_A/I_B through the chip, raw current
//    min/max capture, host calibration of a 1.057 ADC gain, I2t over-current trip on the corrected sample)
//   (d22, revision 0.8: COS_GAIN, CRC coverage, raw min/max capture, host calibration, angle error before/after)
//   (v07, revision 0.7: R3 EN synchroniser, R4 threshold reset, OSC_TRIM lock, comparator mask, reset-value table)
//   +vec=<file> +out=<file>                   (calmc) comparator tables from tb/cmpcal_ref.py, RTL results
//   +clk_ns=<real>                            clk period (RC corners: 23.81, 33.33, 47.62)
// Models: encoder head (ideal sin/cos, amplitude ENC_AMP, electrical frequency
// enc_f), ADC (12-tick conversion, 4:1 mux, track-and-hold on adc_hold, 13 raw
// decisions with an ideal binary CDAC: raw[11:0] = code, raw[12] = 0),
// behavioural window comparators with offset, hysteresis and 200 ns delay
// (tests cal, calmc; revision 0.3),
// BiSS-C / SSI master on MA/SLO, SPI host (mode 0, 24-bit frames).
// Every check prints PASS/FAIL; the last line is "ALL TESTS PASSED" or
// "TESTS FAILED: <n>".
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps
module tb_top;
    // ---------------- clock, reset ----------------
    real clk_ns;
    reg  clk = 0, por_n = 0;
    initial begin
        if (!$value$plusargs("clk_ns=%f", clk_ns)) clk_ns = 33.333;
    end
    always #(clk_ns / 2.0) clk = ~clk;

    // ---------------- pads ----------------
    reg  cs_n = 1, ma = 1, sdi = 0, en_pad = 1, t2f_clk = 0;
    reg  [3:0] cmp = 4'd0;             // forced comparator flags
    reg  [3:0] cmp_mdl = 4'd0;         // behavioural comparators (test cal)
    wire slo_sdo, fault_n, gate_a, gate_b, gate_c, adc_hold, is_smp, adc_start, adc_sel, az_win;
    wire cur_trk;                      // 0.7: SAR current-track request (r1_adc/sar S1)
    wire [4:0] osc_trim;
    // revision 0.5: thr / cal no longer leave the macro; the testbench probes them inside (they are the
    // inputs of r1_tapidx) and the behavioural comparators below use the tap ports tap_p / tap_n
    wire [15:0] ana_ctrl = dut.ana_ctrl;
    wire [5:0] thr_oc_a = dut.thr_oc_a, thr_neg_a = dut.thr_neg_a, thr_oc_b = dut.thr_oc_b, thr_neg_b = dut.thr_neg_b;
    wire [5:0] cal_oc_a = dut.cal_oc_a, cal_neg_a = dut.cal_neg_a, cal_oc_b = dut.cal_oc_b, cal_neg_b = dut.cal_neg_b;
    wire [31:0] tap_p, tap_n;
    wire [3:0] pga_c;
    wire t2f_en, t2f_mode, bias_en;
    reg  adc_valid_a = 0, adc_valid_b = 0;
    reg  [13:0] adc_raw_a = 0, adc_raw_b = 0;

    r1_ctrl_top dut (
        .clk(clk), .por_n(por_n), .cs_n(cs_n), .ma_sclk(ma), .sdi(sdi), .slo_sdo(slo_sdo),
        .en_pad(en_pad), .fault_n(fault_n), .gate_a(gate_a), .gate_b(gate_b), .gate_c(gate_c),
        .adc_hold(adc_hold), .is_smp(is_smp), .adc_start(adc_start), .adc_sel(adc_sel), .cur_trk(cur_trk),
        .adc_valid_a(adc_valid_a), .adc_raw_a(adc_raw_a), .adc_valid_b(adc_valid_b), .adc_raw_b(adc_raw_b),
        .cmp(cmp | cmp_mdl),
        .tap_p(tap_p), .tap_n(tap_n),
        .az_win(az_win), .t2f_clk(t2f_clk), .osc_trim(osc_trim),
        .pga_c(pga_c), .t2f_en(t2f_en), .t2f_mode(t2f_mode), .bias_en(bias_en));

    // ---------------- bookkeeping ----------------
    integer errors = 0, checks = 0;
    task check;
        input cond;
        input [8*128-1:0] msg;
        begin
            checks = checks + 1;
            if (cond) $display("PASS %0s", msg);
            else begin errors = errors + 1; $display("FAIL %0s  (t=%0t)", msg, $time); end
        end
    endtask

    // ---------------- encoder + ADC model ----------------
    real enc_f = 1000.0, enc_amp = 1400.0, enc_ph0 = 0.1;
    // 0.8 (test d22): head offset (LSB) and gain per channel; defaults leave the other tests unchanged
    real enc_os = 0.0, enc_oc = 0.0, enc_gs = 1.0, enc_gc = 1.0;
    // 0.8: model of the raw-code capture (weight-corrected codes of the encoder conversions, as r1_adcw computes them)
    reg  mm_en = 1'b0;
    integer mm_smin = 4095, mm_smax = 0, mm_cmin = 4095, mm_cmax = 0, mm_n = 0;
    real held_ang;
    integer conv_a = 0, conv_b = 0;
    reg  conv_sel = 0;
    reg  [11:0] ia_code = 12'd2048, ib_code = 12'd2048;
    // revision 0.5 (test disc): ia_inc steps the ISA code by 1 at every current conversion, bad_n makes the next
    // bad_n conversions return all-ones decisions (the start-up error of the r1_adc revision 5, first frame wrong)
    reg  ia_inc = 1'b0, conv_bad = 1'b0;
    // 0.9 (test d27): im_rnd sets new random ISA/ISB codes (300..3799) at every current conversion start; im_en tracks the
    // model min/max of the raw (weight-corrected) current codes of the conversions, as RAW_IA/IB_MIN/MAX capture them
    reg  im_rnd = 1'b0, im_en = 1'b0;
    integer im_amin = 4095, im_amax = 0, im_bmin = 4095, im_bmax = 0, im_n = 0, im_seed = 27;
    integer bad_n = 0;
    // revision 0.3 (D18): two slices start together on adc_start; slice A returns
    // adc_valid_a CONV ticks after the start pulse, slice B one tick earlier
    // (both <= 17, the binding conversion time); 14 decisions from a greedy SAR
    // with the nominal r1_adc revision-3 weights (1/4 LSB), i.e. the reset weights
    localparam CONV = 17;
    integer f_mm;
    localparam [195:0] WNOM = {14'd8130, 14'd4065, 14'd2032, 14'd1016, 14'd508, 14'd315, 14'd158,
                               14'd79,   14'd39,   14'd20,   14'd10,   14'd5,   14'd2,   14'd1};
    function [13:0] sar14;
        input [11:0] c;
        integer acc, j;
        reg [13:0] r;
        begin
            acc = 0; r = 0;
            for (j = 13; j >= 0; j = j - 1)
                if (acc + WNOM[14*j +: 14] <= 4 * c) begin acc = acc + WNOM[14*j +: 14]; r[j] = 1'b1; end
            sar14 = r;
        end
    endfunction
    // 0.8: weight-corrected code of a raw decision word (r1_adcw: (sum + 2) >> 2, clamped), nominal weights
    function integer adcw_code;
        input [13:0] r;
        integer j, acc;
        begin
            acc = 0;
            for (j = 0; j < 14; j = j + 1) if (r[j]) acc = acc + WNOM[14*j +: 14];
            acc = (acc + 2) / 4;
            adcw_code = (acc > 4095) ? 4095 : acc;
        end
    endfunction
    // 0.9 (test d27): integer model of r1_icor (register map 0.9 section 4.7)
    function integer icor_m;
        input integer raw; input integer ofs12; input integer gain;
        integer d, q;
        begin
            d = raw - 2048 - ((ofs12 >= 2048) ? ofs12 - 4096 : ofs12);
            q = (d * gain + 8192) >>> 14;
            q = q + 2048;
            icor_m = (q < 0) ? 0 : (q > 4095) ? 4095 : q;
        end
    endfunction
    function real angle_now;           // turns
        input dummy;
        real a;
        begin a = enc_ph0 + enc_f * $realtime * 1e-9; angle_now = a - $floor(a); end
    endfunction
    function [11:0] code;
        input real v;
        integer q;
        begin q = $rtoi(v + 2048.5); if (q > 4095) q = 4095; if (q < 0) q = 0; code = q; end
    endfunction
    // the track-and-holds take the pair at the rising edge of adc_hold
    always @(posedge adc_hold) held_ang = angle_now(0);
    always @(posedge clk) begin
        adc_valid_a <= 1'b0; adc_valid_b <= 1'b0;
        if (adc_start) begin
            conv_a <= CONV - 1; conv_b <= CONV - 2; conv_sel <= adc_sel;   // valid CONV ticks after the start pulse
            conv_bad <= (bad_n > 0); if (bad_n > 0) bad_n <= bad_n - 1;
            if (adc_sel && ia_inc) ia_code <= ia_code + 12'd1;
            if (adc_sel && im_rnd) begin ia_code <= 300 + {$random(im_seed)} % 3500; ib_code <= 300 + {$random(im_seed)} % 3500; end
        end else begin
            if (conv_a > 0) conv_a <= conv_a - 1;
            if (conv_b > 0) conv_b <= conv_b - 1;
            if (conv_a == 1) begin
                adc_valid_a <= 1'b1;
                adc_raw_a <= conv_bad ? 14'h3FFF : conv_sel ? sar14(ia_code) : sar14(code(enc_gs * enc_amp * $sin(6.283185307179586 * held_ang) + enc_os - 0.5));
                if (im_en && conv_sel && !conv_bad) begin
                    im_n = im_n + 1; f_mm = adcw_code(sar14(ia_code));
                    if (f_mm < im_amin) im_amin = f_mm;
                    if (f_mm > im_amax) im_amax = f_mm;
                end
                if (mm_en && !conv_sel && !conv_bad) begin
                    mm_n = mm_n + 1;
                    f_mm = adcw_code(sar14(code(enc_gs * enc_amp * $sin(6.283185307179586 * held_ang) + enc_os - 0.5)));
                    if (f_mm < mm_smin) mm_smin = f_mm;
                    if (f_mm > mm_smax) mm_smax = f_mm;
                end
            end
            if (conv_b == 1) begin
                adc_valid_b <= 1'b1;
                adc_raw_b <= conv_bad ? 14'h3FFF : conv_sel ? sar14(ib_code) : sar14(code(enc_gc * enc_amp * $cos(6.283185307179586 * held_ang) + enc_oc - 0.5));
                if (im_en && conv_sel && !conv_bad) begin
                    f_mm = adcw_code(sar14(ib_code));
                    if (f_mm < im_bmin) im_bmin = f_mm;
                    if (f_mm > im_bmax) im_bmax = f_mm;
                end
                if (mm_en && !conv_sel && !conv_bad) begin
                    f_mm = adcw_code(sar14(code(enc_gc * enc_amp * $cos(6.283185307179586 * held_ang) + enc_oc - 0.5)));
                    if (f_mm < mm_cmin) mm_cmin = f_mm;
                    if (f_mm > mm_cmax) mm_cmax = f_mm;
                end
            end
        end
    end

    // ---------------- behavioural comparators (tests cal, calmc) ----------------
    // Revision 0.3: r1_safe cell frame in units of one calibration step
    // (VREF/252). Cell code c = THR (OC) or 63 - THR (NEG); threshold
    //   T = 4 (2c - 63) + (CAL - 32);  input at zero current: Vcal = -/+ 14*252/26
    //   (OC / NEG) = -/+ 135.69 steps. Trip point up = T + OFS + HY/2, release
    //   point dn = T + OFS - HY/2: state = 1 if Vcal > up, 0 if Vcal < dn, else
    //   held (hysteresis). Inside az_win the isense output is not valid: the
    //   model drives the input to +1000 steps (all flags high).
    // Test calmc: the trip/release offsets per calibration code come from a
    //   table (tb/cmpcal_ref.py, r1_safe DC/transient MC data).
    // flag = state, 200 ns after the clk edge.
    reg  cmp_mdl_en = 0, cmp_tab = 0;
    real cmp_vin = 100.0;
    real cofs [0:3];
    real chy  [0:3];
    real tabu [0:255];
    real tabd [0:255];
    reg  [3:0] cst = 4'd0;
    localparam real VCAL = 135.6923077;
    function real cthr;               // threshold in steps (cell frame)
        input integer i; input [5:0] cal, thr;
        integer c;
        begin
            c = (i == 1 || i == 3) ? 63 - thr : thr;
            cthr = 4.0 * (2.0 * c - 63.0) + ($itor(cal) - 32.0);
        end
    endfunction
    function real cvin;
        input integer i;
        begin cvin = az_win ? 1000.0 : ((i == 1 || i == 3) ? VCAL : -VCAL) + cmp_vin; end
    endfunction
    task cupd;                         // one comparator evaluation
        input integer i; input [5:0] cal, thr;
        real t, v, u, d;
        begin
            if (cmp_tab) begin
                u = tabu[64 * i + cal]; d = tabd[64 * i + cal];
                if (az_win) begin u = -1.0; d = -1.0; end
            end else begin
                t = $itor(tap_p[8*i +: 8]) - $itor(tap_n[8*i +: 8]);   // 0.5: threshold from the tap indices (nP - nN)
                v = cvin(i);
                u = t + cofs[i] + 0.5 * chy[i] - v; d = t + cofs[i] - 0.5 * chy[i] - v;
            end
            if (u < 0.0) cst[i] = 1'b1;
            else if (d > 0.0) cst[i] = 1'b0;
        end
    endtask
    always @(posedge clk) begin : cmpm
        if (cmp_mdl_en) begin
            cupd(0, cal_oc_a, thr_oc_a); cupd(1, cal_neg_a, thr_neg_a);
            cupd(2, cal_oc_b, thr_oc_b); cupd(3, cal_neg_b, thr_neg_b);
            cmp_mdl <= #200 cst;
        end else cmp_mdl <= #200 4'd0;
    end
    // expected code by the r1_safe cal_model.py formula (independent of the RTL):
    // k_rel = first k ascending with dn > Vcal, k_trip = first k descending with
    // up < Vcal, k_cal = 32 + floor((k_rel + k_trip)/2 - k_ideal + 0.5), EXH when
    // a toggle is missing or k_cal is outside 0..63
    reg  [5:0] exp_k;
    reg        exp_x;
    task cexp;
        input integer i; input [5:0] thr; input real kid;
        integer k, kr, kt, kc;
        real t, v;
        begin
            kr = -1; kt = -1;
            for (k = 0; k < 64; k = k + 1) begin
                t = cthr(i, k, thr); v = ((i == 1 || i == 3) ? VCAL : -VCAL);
                if (kr < 0 && t + cofs[i] - 0.5 * chy[i] > v) kr = k;
            end
            for (k = 63; k >= 0; k = k - 1) begin
                t = cthr(i, k, thr); v = ((i == 1 || i == 3) ? VCAL : -VCAL);
                if (kt < 0 && t + cofs[i] + 0.5 * chy[i] < v) kt = k;
            end
            if (kr < 0 || kt < 0) begin exp_k = 6'd0; exp_x = 1'b1; end
            else begin
                kc = 32 + $rtoi($floor((kr + kt) / 2.0 - kid + 0.5));
                exp_x = (kc < 0) || (kc > 63);
                exp_k = (kc < 0) ? 6'd0 : (kc > 63) ? 6'd63 : kc;
            end
        end
    endtask


    // ---------------- revision 0.5: tap-index reference, discard monitor ----------------
    // independent integer form of the r1_safe formula: {nN, nP} for comparator i (0 OC_A, 1 NEG_A, 2 OC_B, 3 NEG_B)
    function [15:0] tapx;
        input integer i; input integer thr, cal;
        integer c, d, p, n;
        begin
            c = (i == 1 || i == 3) ? 63 - thr : thr;
            d = cal - 32;
            p = 4 * c + ((d >= 0) ? (d + 1) / 2 : -((-d) / 2));           // ceil(d/2)
            n = 4 * (63 - c) - ((d >= 0) ? d / 2 : -((-d + 1) / 2));      // floor(d/2)
            if (p < 0) p = 0; if (p > 252) p = 252;
            if (n < 0) n = 0; if (n > 252) n = 252;
            tapx = {n[7:0], p[7:0]};
        end
    endfunction
    // frame monitor: started frames since an arm event (or since the reset release in test disc), by type
    reg  mon_en = 1'b0, arm_p = 1'b0;
    integer tb_disc = 1, nidx = 0, ast_e = 0, ast_c = 0, dr_e = 0, dr_c = 0, fl_e = 0, fl_c = 0, dv_e = 0, dv_c = 0, dn_all = 0;
    integer npre = 0;
    always @(posedge adc_hold) begin #1; if (mon_en && !adc_start) npre = npre + 1; end
    reg  [11:0] dropcode = 12'hFFF;
    reg  dropcode_ok = 1'b0, bad_seen = 1'b0, drop_seen = 1'b0;
    reg  [11:0] drop_hist [0:15];
    integer ndh = 0, dh;
    always @(posedge clk) begin
        if (dut.adc_arm) begin
            nidx = 0; ast_e = 0; ast_c = 0; dr_e = 0; dr_c = 0; fl_e = 0; fl_c = 0; dv_e = 0; dv_c = 0; dn_all = 0;
            ndh = 0; dropcode_ok = 1'b0; bad_seen = 1'b0; drop_seen = 1'b0;
            if (dut.u_gate.conv) begin if (adc_sel) fl_c = 1; else fl_e = 1; end   // frame in flight at the arm tick
            arm_p <= 1'b1; mon_en = 1'b1;
        end else begin
            arm_p <= 1'b0;
            if (mon_en && adc_start) begin
                if (arm_p) begin if (adc_sel) fl_c = fl_c + 1; else fl_e = fl_e + 1; end   // started in the arm tick: not counted by the RTL
                else begin
                    if (adc_sel) ast_c = ast_c + 1; else ast_e = ast_e + 1;
                    if (nidx < tb_disc) begin
                        if (adc_sel) begin dr_c = dr_c + 1; drop_hist[ndh] = ia_code + (ia_inc ? 12'd1 : 12'd0); ndh = ndh + 1; end
                        else dr_e = dr_e + 1;
                    end
                    if (nidx < 15) nidx = nidx + 1;
                end
            end
        end
        if (mon_en && dut.smp_valid) dv_e = dv_e + 1;
        if (mon_en && dut.u_gate.nra && dut.u_gate.nrb) dn_all = dn_all + 1;
        if (mon_en && (dut.sin_code == 12'hFFF || dut.cos_code == 12'hFFF || dut.i_a == 12'hFFF || dut.i_b == 12'hFFF)) bad_seen = 1'b1;
    end
    always @(dut.i_a) if (mon_en) begin
        dv_c = dv_c + 1;
        for (dh = 0; dh < ndh; dh = dh + 1) if (dut.i_a == drop_hist[dh]) drop_seen = 1'b1;
    end

    // revision 0.5 (test cdc)
    reg  [17:0] alt_pos = 18'h2AAAA;
    always @(posedge clk) alt_pos <= ~alt_pos;               // the position input changes at every tick
    reg  cdc_mon = 1'b0;
    real t_clk_last = 0.0;
    integer n_mr_rise = 0, n_mr_off = 0, n_mr_fall = 0;
    always @(posedge clk) t_clk_last = $realtime;
    always @(dut.u_biss.ma_rst_n) if (cdc_mon) begin
        if (dut.u_biss.ma_rst_n) begin n_mr_rise = n_mr_rise + 1; if ($realtime - t_clk_last > 0.01) n_mr_off = n_mr_off + 1; end
        else n_mr_fall = n_mr_fall + 1;
    end

    // ---------------- SPI host ----------------
    real sck_half = 50.0;              // 10 MHz SCLK
    reg  [23:0] spi_mi;
    task spi_x;                        // one frame of nbits (24 = well-formed)
        input [23:0] mo;
        input integer nbits;
        integer i;
        begin
            ma = 1'b0; #(sck_half);
            cs_n = 1'b0; #(sck_half);
            spi_mi = 24'd0;
            for (i = nbits - 1; i >= 0; i = i - 1) begin
                sdi = mo[i]; #(sck_half);
                ma = 1'b1; spi_mi[i] = slo_sdo; #(sck_half);
                ma = 1'b0;
            end
            #(sck_half); cs_n = 1'b1;
            #(10 * clk_ns + 50);       // CS_N high time
        end
    endtask
    task spi_wr;
        input [6:0] a; input [15:0] d;
        begin spi_x({1'b0, a, d}, 24); end
    endtask
    reg [15:0] rd_val;
    reg [7:0]  rd_stat;
    task spi_rd;
        input [6:0] a;
        begin spi_x({1'b1, a, 16'd0}, 24); spi_x({1'b1, 7'h00, 16'd0}, 24);
              rd_val = spi_mi[15:0]; rd_stat = spi_mi[23:16]; end
    endtask
    task bus_idle;                     // return MA high and wait for BiSS arming
        begin ma = 1'b1; #(1000 * clk_ns + 1000); end
    endtask

    // CRC-8 (0x07, init 0xFF) over the calibration registers, as the host computes it
    function [7:0] crc8;
        input [127:0] bytes;
        integer i, j;
        reg [7:0] r;
        begin
            r = 8'hFF;
            for (i = 15; i >= 0; i = i - 1) begin
                r = r ^ bytes[i*8 +: 8];
                for (j = 0; j < 8; j = j + 1) r = r[7] ? ({r[6:0], 1'b0} ^ 8'h07) : {r[6:0], 1'b0};
            end
            crc8 = r;
        end
    endfunction
    reg [127:0] calb;
    integer ci;
    // revision 0.3: CRC-8 over the 43 covered words in the order 0x10..0x17,
    // 0x36..0x3C, 0x50..0x5D, 0x60..0x6D (values as read back, high byte first)
    reg  [7:0] crc_r;
    reg        crc_v07 = 1'b0;         // 0.8 test d22: 1 = the 43-word CRC of revision 0.7 (negative check)
    reg        crc_v08 = 1'b0;         // 0.9 test d27: 1 = the 44-word CRC of revision 0.8 (negative check)
    task crc_word;
        input [15:0] w;
        integer j;
        begin
            crc_r = crc_r ^ w[15:8];
            for (j = 0; j < 8; j = j + 1) crc_r = crc_r[7] ? ({crc_r[6:0], 1'b0} ^ 8'h07) : {crc_r[6:0], 1'b0};
            crc_r = crc_r ^ w[7:0];
            for (j = 0; j < 8; j = j + 1) crc_r = crc_r[7] ? ({crc_r[6:0], 1'b0} ^ 8'h07) : {crc_r[6:0], 1'b0};
        end
    endtask
    task load_cal_crc;                 // read back the covered words, write CAL_CRC
        begin
            crc_r = 8'hFF;
            for (ci = 0; ci < 8; ci = ci + 1) begin
                spi_rd(7'h10 + ci);
                calb[(15 - 2 * ci) * 8 +: 8] = rd_val[15:8];
                calb[(14 - 2 * ci) * 8 +: 8] = rd_val[7:0];
                crc_word(rd_val);
            end
            if (crc_r != crc8(calb)) $display("FAIL testbench CRC helpers disagree");
            for (ci = 8'h36; ci <= 8'h3C; ci = ci + 1) begin spi_rd(ci); crc_word(rd_val); end
            for (ci = 8'h50; ci <= 8'h5D; ci = ci + 1) begin spi_rd(ci); crc_word(rd_val); end
            for (ci = 8'h60; ci <= 8'h6D; ci = ci + 1) begin spi_rd(ci); crc_word(rd_val); end
            if (!crc_v07) begin spi_rd(7'h3F); crc_word(rd_val); end      // 0.8: COS_GAIN is the 44th word
            if (!crc_v07 && !crc_v08)                                        // 0.9: IA_OFS, IB_OFS, IA_GAIN, IB_GAIN = words 45..48
                for (ci = 8'h48; ci <= 8'h4B; ci = ci + 1) begin spi_rd(ci); crc_word(rd_val); end
            spi_wr(7'h18, {8'd0, crc_r});
            #(360 * clk_ns);
        end
    endtask

    task init_chip;
        begin
            por_n = 0; #(10 * clk_ns); por_n = 1; #(20 * clk_ns);
            ma = 1'b1; #(700 * clk_ns);            // MA idle -> BiSS armed
            load_cal_crc;
            spi_wr(7'h04, 16'h0001);               // CLR
            #(20 * clk_ns);
            bus_idle;
        end
    endtask

    // ---------------- BiSS master ----------------
    reg  [63:0] b_bits;                // received bits after START: CDS, data, CRC
    integer b_busy, b_n, b_start_edge;
    real b_to_ns, b_lat_t;
    reg  b_ack_ok, b_stop_ok, b_cds;
    reg  [35:0] b_data;                // data incl. nE nW, right-aligned
    reg  [5:0]  b_crc_wire, b_crc_calc;
    function [5:0] crc6;
        input [35:0] d; input integer n;
        integer i;
        reg [5:0] c; reg fb;
        begin
            c = 6'd0;
            for (i = n - 1; i >= 0; i = i - 1) begin
                fb = c[5] ^ d[i]; c = {c[4:0], 1'b0}; if (fb) c = c ^ 6'h03;
            end
            crc6 = c;
        end
    endfunction
    // ndata = data bits incl. nE nW; abort_at > 0 stops clocking after that many edges
    task biss_frame;
        input real th; input real tl; input integer ndata; input cdm; input integer abort_at;
        integer k, got, need, j;
        reg s;
        real t_last;
        begin
            k = 0; got = 0; b_start_edge = 0; b_bits = 64'd0; b_ack_ok = 0; b_stop_ok = 0;
            need = 1 + ndata + 6;          // CDS + data + CRC
            j = 0;
            while (slo_sdo !== 1'b1 && j < 100000) begin #10; j = j + 1; end
            ma = 1'b0; #(tl);
            while ((b_start_edge == 0 || got < need + 1) && k < 400 && !(abort_at > 0 && k >= abort_at)) begin
                ma = 1'b1; k = k + 1;
                if (k == 1) b_lat_t = $realtime;
                t_last = $realtime;
                #(th);
                s = slo_sdo;                 // value driven after rising edge k
                ma = 1'b0; t_last = $realtime;
                if (k == 2) b_ack_ok = (s == 1'b0);
                else if (k >= 3 && b_start_edge == 0) begin
                    if (s) b_start_edge = k;
                end else if (b_start_edge != 0) begin
                    if (got < need) b_bits[63 - got] = s;
                    else b_stop_ok = (s == 1'b0);
                    got = got + 1;
                end
                #(tl);
            end
            // end of clocking: MA = inverted CDM during the timeout
            if (!cdm) begin ma = 1'b1; t_last = $realtime; end
            j = 0;
            while (slo_sdo !== 1'b1 && j < 200000) begin #1; j = j + 1; end
            b_to_ns = $realtime - t_last;
            if (cdm) begin #(200); ma = 1'b1; end
            #(200);
            b_busy = (b_start_edge > 0) ? b_start_edge - 1 : -1;
            b_cds  = b_bits[63];
            b_data = 36'd0;
            for (j = 0; j < ndata; j = j + 1) b_data[ndata - 1 - j] = b_bits[62 - j];
            for (j = 0; j < 6; j = j + 1) b_crc_wire[5 - j] = b_bits[62 - ndata - j];
            b_crc_calc = crc6(b_data, ndata);
        end
    endtask

    // ---------------- SSI master ----------------
    reg [35:0] s_data;
    real s_mono_ns;
    task ssi_frame;
        input real th; input real tl; input integer n;
        integer k, j;
        real t_last;
        begin
            s_data = 36'd0;
            j = 0;
            while (slo_sdo !== 1'b1 && j < 100000) begin #10; j = j + 1; end
            ma = 1'b0; #(tl);                      // first falling edge: latch
            for (k = 0; k < n; k = k + 1) begin
                ma = 1'b1; #(th);
                ma = 1'b0; s_data[n - 1 - k] = slo_sdo; #(tl);
            end
            ma = 1'b1; t_last = $realtime;         // edge n+1: data low (monoflop)
            #(th);
            j = 0;
            while (slo_sdo !== 1'b1 && j < 200000) begin #1; j = j + 1; end
            s_mono_ns = $realtime - t_last;
            #(200);
        end
    endtask

    // ---------------- BiSS control channel (D2 pp. 13-17) ----------------
    // Frame k carries CDM_k (sent at the end of frame k) and CDS_k; the slave
    // answers CDM_k in CDS_{k+1} (D2 p. 14). Command: S CTS=1 ID[2:0] ADR[6:0]
    // CRC4 R W, then the start bit S at frame s_at (D2: may be delayed), then 0.
    // seq_at > 0: a second S at that frame (sequential read, D2 Fig. 30).
    reg [79:0] cc_cds;
    function [3:0] crc4;               // x^4 + x + 1, start 0, MSB first, not inverted
        input [10:0] d; input integer n;
        integer i; reg [3:0] c;
        begin c = 4'd0; for (i = n - 1; i >= 0; i = i - 1) c = {c[2:0], 1'b0} ^ ((c[3] ^ d[i]) ? 4'h3 : 4'h0); crc4 = c; end
    endfunction
    task cc_cmd;
        input [6:0] adr; input rd; input wr; input bad_crc; input integer s_at; input integer seq_at; input integer nfr;
        integer k; reg [3:0] c4; reg cdm;
        begin
            for (k = 0; k < 14; k = k + 1) biss_frame(250.0, 250.0, 20, 1'b0, 0);   // 14 x CDM = 0: reset
            c4 = bad_crc ? 4'hF : crc4({1'b1, 3'b000, adr}, 11);                       // CTS = 1 (register access, D2 p. 14), ID 0
            cc_cds = 80'd0;
            for (k = 0; k < nfr; k = k + 1) begin
                if (k <= 1) cdm = 1'b1;                                                   // S, CTS = 1
                else if (k <= 4) cdm = 1'b0;
                else if (k <= 11) cdm = adr[11 - k];
                else if (k <= 15) cdm = ~c4[15 - k];
                else if (k == 16) cdm = rd;
                else if (k == 17) cdm = wr;
                else cdm = (k == s_at) || (k == seq_at);
                biss_frame(250.0, 250.0, 20, cdm, 0);
                cc_cds[k] = b_cds;
            end
        end
    endtask
    function [7:0] cc_byte;            // 8 CDS bits from frame k, MSB first
        input integer k; integer i;
        begin for (i = 0; i < 8; i = i + 1) cc_byte[7 - i] = cc_cds[k + i]; end
    endfunction
    function [3:0] cc_nib;
        input integer k; integer i;
        begin for (i = 0; i < 4; i = i + 1) cc_nib[3 - i] = cc_cds[k + i]; end
    endfunction

    // =====================================================================
    reg [1023:0] test;
    integer i, k, nb, f_i;
    real fr, th, tl, err_deg, tick_ns, exp_ns;
    reg [17:0] exp18;
    reg [35:0] word;
    reg [15:0] v16, gray16;
    initial begin
        if (!$value$plusargs("test=%s", test)) test = "biss";
        tick_ns = clk_ns;
        $display("# tb_top test=%0s clk_ns=%0.3f", test, clk_ns);
        init_chip;
        check(fault_n == 1'b1, "init: FAULT_N high after CAL_CRC load and CLR");

        // =================================================================
        if (test == "biss") begin
            // ---- item 1: CRC-6 vectors, 18-bit position, nE = nW = 1 ----
            spi_wr(7'h05, 16'h0212);                       // ST_LEN 18, MT off, TEST_POS_EN
            bus_idle;
            spi_wr(7'h06, 16'h0000); spi_wr(7'h05, 16'h0212); bus_idle;
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            check(b_data[19:2] == 18'h00000 && b_data[1:0] == 2'b11, "biss item1: data 0x00000 nE nW = 1 1");
            check(b_crc_wire == 6'h3A, "biss item1: 0x00000 CRC on wire 0x3A");
            spi_wr(7'h06, 16'hFFFF); spi_wr(7'h05, 16'h3212); bus_idle;
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            check(b_data[19:2] == 18'h3FFFF && b_crc_wire == 6'h02, "biss item1: 0x3FFFF CRC on wire 0x02");
            spi_wr(7'h06, 16'h2345); spi_wr(7'h05, 16'h1212); bus_idle;
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            check(b_data[19:2] == 18'h12345 && b_crc_wire == 6'h0D, "biss item1: 0x12345 CRC on wire 0x0D");
            check(b_ack_ok && b_stop_ok, "biss: ACK 0 at edge 2, stop 0 after CRC");

            // ---- items 2, 3: MA 80 kHz .. 10 MHz, 40 % duty corners, t_busy ----
            for (f_i = 0; f_i < 5; f_i = f_i + 1) begin
                case (f_i)
                    0: fr = 80e3; 1: fr = 250e3; 2: fr = 1e6; 3: fr = 5e6; default: fr = 10e6;
                endcase
                for (k = 0; k < 2; k = k + 1) begin
                    th = (k == 0 ? 0.4 : 0.6) * 1e9 / fr; tl = 1e9 / fr - th;
                    biss_frame(th, tl, 20, 1'b0, 0);
                    $display("INFO biss f_MA=%0.0f Hz duty_high=%0.1f t_busy=%0d T_MA timeout=%0.2f us",
                             fr, th * fr / 1e9, b_busy, b_to_ns / 1000.0);
                    check(b_data[19:2] == 18'h12345 && b_crc_wire == ~b_crc_calc && b_ack_ok,
                          "biss item2: frame data and CRC at this MA frequency / duty");
                    if (fr <= 1e6) check(b_busy == 2, "biss item3: t_busy = 2 T_MA (f_MA <= 1 MHz)");
                    else check(b_busy >= 2 && b_busy <= 6, "biss item3: t_busy in 2..6 T_MA (f_MA > 1 MHz, handshake)");
                end
            end

            // ---- item 4: static timeout (TIMEOUT_TICKS = 600) ----
            exp_ns = 600.0 * clk_ns;
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            $display("INFO biss timeout measured %0.3f us, 600 ticks = %0.3f us", b_to_ns / 1000.0, exp_ns / 1000.0);
            check(b_to_ns > exp_ns && b_to_ns < exp_ns + 8 * clk_ns, "biss item4: timeout = TIMEOUT_TICKS + sync (< 6 ticks)");
            check(b_to_ns > 12500.0 && b_to_ns < 40000.0, "biss item4: timeout inside 12.5..40 us");

            // ---- item 5: back-to-back frames at minimum cycle ----
            nb = 0;
            for (i = 0; i < 5; i = i + 1) begin
                biss_frame(50.0, 50.0, 20, 1'b0, 0);
                if (b_data[19:2] == 18'h12345 && b_crc_wire == ~b_crc_calc) nb = nb + 1;
            end
            check(nb == 5, "biss item5: 5 back-to-back frames at 10 MHz, restart when SLO high");

            // ---- item 6: aborted frame, recovery ----
            biss_frame(500.0, 500.0, 20, 1'b0, 9);
            #(40000);
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            check(b_data[19:2] == 18'h12345 && b_crc_wire == ~b_crc_calc && b_busy == 2,
                  "biss item6: frame after an aborted frame and 40 us is correct");

            // ---- item 7: nE / nW and Null Value ----
            spi_wr(7'h05, 16'h1612); bus_idle;           // FORCE_NE
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            check(b_data[1:0] == 2'b01 && b_crc_wire == ~b_crc_calc, "biss item7: FORCE_NE gives nE = 0, CRC valid");
            spi_wr(7'h05, 16'h1A12); bus_idle;           // FORCE_NW
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            check(b_data[1:0] == 2'b10 && b_crc_wire == ~b_crc_calc, "biss item7: FORCE_NW gives nW = 0, CRC valid");
            spi_wr(7'h05, 16'h0012); bus_idle;           // real position, MT off
            enc_amp = 0.0; #(20000);                      // signal loss: pos_valid drops
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            check(b_data == 36'd0 && b_crc_wire == ~b_crc_calc, "biss item7: Null Value (data 0, nE 0) on signal loss");
            enc_amp = 1400.0; #(40000);
            spi_wr(7'h03, 16'h0020); spi_wr(7'h04, 16'h0001); #(1000);   // clear the AMP fault
            spi_wr(7'h03, 16'h0000); bus_idle;

            // ---- position latch and extrapolation with a rotating head (10 kHz el) ----
            enc_f = 10000.0; #(200000);
            spi_wr(7'h05, 16'h0032); bus_idle;            // MT on, ST 18
            nb = 0; err_deg = 0.0;
            for (i = 0; i < 6; i = i + 1) begin
                biss_frame(250.0, 250.0, 36, 1'b0, 0);
                th = angle_now(0);
                tl = enc_ph0 + enc_f * b_lat_t * 1e-9; tl = tl - $floor(tl);
                exp_ns = (b_data[19:2] / 262144.0 - tl) * 360.0;
                if (exp_ns > 180.0) exp_ns = exp_ns - 360.0;
                if (exp_ns < -180.0) exp_ns = exp_ns + 360.0;
                if (exp_ns < 0) exp_ns = -exp_ns;
                if (exp_ns > err_deg) err_deg = exp_ns;
                if (b_crc_wire == ~b_crc_calc && b_data[1:0] == 2'b11) nb = nb + 1;
                $display("INFO biss latch frame %0d: busy %0d MT %0d ST 0x%05h nE nW %b crc %02h/%02h head %0.5f err %0.3f deg", i, b_busy, b_data[35:20], b_data[19:2], b_data[1:0], b_crc_wire, ~b_crc_calc, tl, exp_ns);
                #(30000);
            end
            $display("INFO biss latch: max |position at LAT - head angle at LAT| = %0.3f deg el at 10 kHz el", err_deg);
            check(nb == 6, "biss: 6 multi-turn frames with real position, nE nW 1 1, CRC valid");
            check(err_deg < 0.25, "biss: latched position within 0.25 deg el (2 ticks) of the head angle at LAT (10 kHz el)");
            enc_f = 1000.0;

            // ---- half-tick LAT timing (BUS_CFG.LAT_HALF): latch error spread at 100 kHz el ----
            begin : lh
                real mn, mx, e, spr0, spr1;
                for (k = 0; k < 2; k = k + 1) begin
                    enc_f = 100000.0;
                    spi_wr(7'h05, k ? 16'h4032 : 16'h0032); bus_idle; #(200000);
                    mn = 1e9; mx = -1e9;
                    for (i = 0; i < 40; i = i + 1) begin
                        #(i * 3.917 + 0.7);                  // spread the LAT edge over the tick
                        biss_frame(250.0, 250.0, 36, 1'b0, 0);
                        tl = enc_ph0 + enc_f * b_lat_t * 1e-9; tl = tl - $floor(tl);
                        e = (b_data[19:2] / 262144.0 - tl) * 360.0;
                        if (e > 180.0) e = e - 360.0;
                        if (e < -180.0) e = e + 360.0;
                        if (e < mn) mn = e;
                        if (e > mx) mx = e;
                        #(20000);
                    end
                    if (k) spr1 = mx - mn; else spr0 = mx - mn;
                    $display("INFO biss LAT_HALF=%0d at 100 kHz el: latch error %0.3f .. %0.3f deg el, spread %0.3f deg (1 tick = %0.3f deg)",
                             k, mn, mx, mx - mn, 360.0 * 100000.0 * clk_ns * 1e-9);
                end
                check(spr1 < 0.75 * spr0, "biss: LAT_HALF reduces the latch error spread at 100 kHz el (< 0.75 x without)");
                enc_f = 1000.0; #(200000);
            end

            // ---- item 8: control channel (D2 pp. 13-17) ----
            spi_wr(7'h05, 16'h0212); bus_idle;
            begin : cc
                reg [7:0] d;
                spi_rd(7'h32); v16 = rd_val; bus_idle;
                // read 0x42 (BP_ID high byte), S without delay
                cc_cmd(7'h42, 1'b1, 1'b0, 1'b0, 18, 0, 34);
                d = cc_byte(20);
                $display("INFO biss cc read 0x42: CDS[1..32] %b", cc_cds[32:1]);
                check(cc_cds[1] == 1'b1 && cc_cds[16:2] == 15'd0, "biss item8: IDL0 = 1 after the start bit, then 0 (D2 p. 14-15)");
                check(cc_cds[17] == 1'b1 && cc_cds[18] == 1'b0, "biss item8: slave repeats R = 1, W = 0 (address accepted, D2 p. 16)");
                check(cc_cds[19] == 1'b1 && d == 8'h00 && cc_nib(28) == ~crc4({3'd0, d}, 8),
                      "biss item8: S repeated, D = 0x00 (BP_ID high), CRC-4 inverted over the data");
                check(cc_cds[32] == 1'b0, "biss item8: stop bit P = 0 (next address 0x43 accepted)");
                // sequential read 0x42, 0x43 (second S at frame 32)
                cc_cmd(7'h42, 1'b1, 1'b0, 1'b0, 18, 32, 48);
                d = cc_byte(34);
                check(cc_cds[33] == 1'b1 && d == 8'h01 && cc_nib(42) == ~crc4({3'd0, d}, 8) && cc_cds[46] == 1'b0,
                      "biss item8: sequential read gives 0x43 = 0x01 (BP_ID non-zero), CRC-4, P = 0");
                // delayed start bit (S at frame 21)
                cc_cmd(7'h78, 1'b1, 1'b0, 1'b0, 21, 0, 37);
                d = cc_byte(23);
                check(cc_cds[21:19] == 3'd0 && cc_cds[22] == 1'b1 && d == 8'h52 && cc_nib(31) == ~crc4({3'd0, d}, 8),
                      "biss item8: delayed S, read 0x78 (DEV_ID byte 0 = 0x52)");
                // last address: P = 1
                cc_cmd(7'h7F, 1'b1, 1'b0, 1'b0, 18, 0, 34);
                d = cc_byte(20);
                check(cc_cds[19] && d == 8'h00 && cc_nib(28) == ~crc4({3'd0, d}, 8) && cc_cds[32] == 1'b1,
                      "biss item8: read 0x7F (MFR_ID low, reset value), P = 1 (no next address)");
                // refused read of 0x40 (BSEL, one bank): W inverted, no S
                cc_cmd(7'h40, 1'b1, 1'b0, 1'b0, 18, 0, 34);
                check(cc_cds[17] == 1'b1 && cc_cds[18] == 1'b1 && cc_cds[33:19] == 15'd0,
                      "biss item8: refused read (0x40) -> W repeated inverted, no data (D2 p. 16)");
                // write (not supported): W inverted
                cc_cmd(7'h44, 1'b0, 1'b1, 1'b0, 18, 0, 34);
                check(cc_cds[17] == 1'b0 && cc_cds[18] == 1'b0 && cc_cds[33:19] == 15'd0,
                      "biss item8: write access refused -> W repeated inverted, no data");
                // CRC-4 error: no response
                cc_cmd(7'h42, 1'b1, 1'b0, 1'b1, 18, 0, 34);
                check(cc_cds[33:17] == 17'd0, "biss item8: header CRC-4 error -> no response");
                spi_rd(7'h32); bus_idle;
                $display("INFO biss cc error counter %0d -> %0d", v16[11:8], rd_val[11:8]);
                check(rd_val[11:8] == v16[11:8] + 4'd3, "biss item8: refused read, refused write and CRC error counted (DIAG_BISS[11:8] + 3)");
                // 14 x CDM = 0 aborts a started command
                cc_cmd(7'h42, 1'b1, 1'b0, 1'b0, 18, 0, 8);
                for (i = 0; i < 14; i = i + 1) biss_frame(250.0, 250.0, 20, 1'b0, 0);
                check(dut.u_biss.cst == 3'd0, "biss item8: 14 x CDM = 0 returns the control channel to idle");
            end
        end

        // =================================================================
        if (test == "ssi") begin
            enc_f = 0.0; enc_ph0 = 0.3; #(500000);
            for (k = 0; k < 2; k = k + 1) begin
                spi_wr(7'h05, k ? 16'h00ED : 16'h006D); bus_idle;   // SSI, MT on, ST 13, gray k
                ssi_frame(500.0, 500.0, 29);
                spi_rd(7'h19); v16 = rd_val; spi_rd(7'h1A); bus_idle;
                word = {rd_val, v16[15:3]};                     // MT16 + ST13 from SPI, binary
                if (k) word = word ^ (word >> 1);
                $display("INFO ssi gray=%0d data 0x%08h expected 0x%08h monoflop %0.2f us", k, s_data[28:0], word[28:0], s_mono_ns / 1000.0);
                check(s_data[28:0] == word[28:0], k ? "ssi: Gray word = SPI POS/TURNS (MT16 + ST13)" : "ssi: binary word = SPI POS/TURNS (MT16 + ST13)");
                exp_ns = 600.0 * clk_ns;
                check(s_mono_ns > exp_ns && s_mono_ns < exp_ns + 8 * clk_ns, "ssi: monoflop = TIMEOUT_TICKS + sync");
            end
            for (f_i = 0; f_i < 3; f_i = f_i + 1) begin
                fr = (f_i == 0) ? 100e3 : (f_i == 1) ? 1e6 : 2e6;
                ssi_frame(0.5e9 / fr, 0.5e9 / fr, 29);
                check(s_data[28:0] == word[28:0], "ssi: Gray word at 100 kHz / 1 MHz / 2 MHz clock");
            end
            // host clock trim (S5): OSC_COUNT over 16 SCLK periods at 1 MHz, then
            // TIMEOUT_TICKS = OSC_COUNT * 20 / 16 for a 20 us monoflop / BiSS timeout
            spi_wr(7'h08, 16'h0110);
            sck_half = 500.0; spi_x(24'd0, 40); sck_half = 50.0;
            spi_rd(7'h09); v16 = rd_val;
            spi_wr(7'h07, (v16 * 20 + 8) / 16); bus_idle;
            ssi_frame(500.0, 500.0, 29);
            $display("INFO ssi clk %0.3f ns: OSC_COUNT %0d -> TIMEOUT_TICKS %0d, monoflop %0.2f us (600 ticks untrimmed = %0.2f us)",
                     clk_ns, v16, (v16 * 20 + 8) / 16, s_mono_ns / 1000.0, 600.0 * clk_ns / 1000.0);
            check(s_data[28:0] == word[28:0] && s_mono_ns > 19000.0 && s_mono_ns < 21000.0,
                  "ssi: after the host trim from OSC_COUNT the monoflop is 20 us +-5 %");
        end

        // =================================================================
        if (test == "spi") begin
            spi_rd(7'h00);
            check(rd_val == 16'h5209, "spi: ID reads 0x5209 (revision 0.9)");
            spi_rd(7'h08);
            check(rd_val == 16'd22 && osc_trim == 5'd22, "spi: OSC_TRIM reset value 22 (D13), on the oscillator port");
            spi_rd(7'h05);
            check(rd_val == 16'h40B2, "spi: BUS_CFG reset 0x40B2 (LAT_HALF on, BiSS, MT on, ST 18)");
            spi_wr(7'h05, 16'h4112); spi_rd(7'h05);
            check(rd_val == 16'h4012, "spi: BUS_CFG bit 8 reserved (reads 0; AS5047P mode removed)");
            spi_wr(7'h05, 16'h40B2);
            spi_rd(7'h5D);
            check(rd_val == 16'd8130, "spi: ADC_A_W13 reset 8130 (nominal r1_adc rev 3 weight x 4, D18)");
            spi_rd(7'h68);
            check(rd_val == 16'd315, "spi: ADC_B_W8 reset 315 (nominal 78.8 LSB x 4, slice B, D18)");
            // 8131: a 1/4-LSB change, so the live encoder path is not disturbed
            spi_wr(7'h6D, 16'd8131); spi_rd(7'h6D); v16 = rd_val; spi_rd(7'h5D);
            check(v16 == 16'd8131 && rd_val == 16'd8130, "spi: ADC_B_W13 is a separate word (slice A unchanged)");
            spi_wr(7'h6D, 16'd8130);
            #(400 * clk_ns); spi_wr(7'h04, 16'h0001);   // weight writes clear CAL_VALID (CAL fault): clean pass, then CLR
            // walking pattern on writable registers
            nb = 0;
            for (i = 0; i < 16; i = i + 1) begin
                spi_wr(7'h20 + (i % 7), 16'h0001 << i);
                spi_rd(7'h20 + (i % 7));
                // revision 0.4: PWM words are 13 bit; bits 15:13 ignore writes and read 0
                if (rd_val == ((16'h0001 << i) & 16'h1FFF)) nb = nb + 1;
            end
            check(nb == 16, "spi: walking-one write/read on PWM registers (13 bit, bits 15:13 read 0)");
            spi_wr(7'h20, 16'h0000);
            spi_wr(7'h0C, 16'hA5C3); spi_rd(7'h0C);
            check(rd_val == 16'hA5C3 && ana_ctrl == 16'hA5C3, "spi: ANA_CTRL write reads back and reaches the register output");
            #(4 * clk_ns);
            check(pga_c == 4'b0111 && !t2f_en && !t2f_mode && !bias_en,
                  "spi: ANA_CTRL 0xA5C3 decodes to PGA code 3 (c1 c2 c3), T2F_EN 0, T2F_MODE 0, BIAS_EN 0");
            spi_wr(7'h0C, 16'h0028);
            spi_wr(7'h08, 16'h0013); spi_rd(7'h08);
            check(rd_val == 16'h0013 && osc_trim == 5'h13, "spi: OSC_TRIM write reaches the oscillator port");
            spi_x({1'b0, 7'h0D, 16'h0007}, 24);
            check(spi_mi[23:16] == dut.status[7:0], "spi: status byte in every frame");
            spi_x({1'b1, 7'h0D, 16'h0000}, 24);
            check(spi_mi[15:0] == 16'h0007, "spi: write echo in the next frame");
            spi_rd(7'h7E); check(rd_val == 16'h0000, "spi: BiSS MFR_ID mirror at 0x7E");
            spi_rd(7'h79); check(rd_val == 16'h0031, "spi: BiSS DEV_ID mirror at 0x79 ('1')");
            // malformed frame (20 bits) -> error counter
            spi_x({4'h0, 20'hFFFFF}, 20); spi_rd(7'h33);
            check(rd_val[7:0] == 8'd1, "spi: short frame counted as SPI error");
            // OSC_COUNT: arm, burst of 40 SCLK periods at 1 MHz (malformed frame), read
            spi_wr(7'h08, 16'h0113);
            sck_half = 500.0; spi_x(24'd0, 40); sck_half = 50.0;
            spi_rd(7'h09);
            exp_ns = 16000.0 / clk_ns;
            $display("INFO OSC_COUNT = %0d, expected %0.1f (16 us of %0.3f ns ticks)", rd_val, exp_ns, clk_ns);
            check(rd_val >= exp_ns - 2 && rd_val <= exp_ns + 2 && dut.status[10], "spi: OSC_COUNT over 16 SCLK periods (1 MHz) within +-2 ticks, OSC_DONE");
            spi_rd(7'h09);
            check(rd_val >= exp_ns - 2 && rd_val <= exp_ns + 2, "spi: OSC_COUNT held after later SPI traffic");
            // clock-fault window: OSC_WIN = {HI, LO} in units of 16 ticks
            k = $rtoi(exp_ns / 16.0);
            spi_wr(7'h0A, {k[7:0] + 8'd2, k[7:0] - 8'd2}); spi_rd(7'h01);
            check(rd_val[5] == 1'b0, "spi: OSC_COUNT inside OSC_WIN -> STATUS.CLK_FAULT = 0");
            spi_wr(7'h0A, {k[7:0] - 8'd4, k[7:0] - 8'd8}); spi_rd(7'h01);
            check(rd_val[5] == 1'b1, "spi: OSC_COUNT above OSC_WIN.HI -> STATUS.CLK_FAULT = 1");
            spi_wr(7'h0A, {k[7:0] + 8'd8, k[7:0] + 8'd4}); spi_rd(7'h01);
            check(rd_val[5] == 1'b1, "spi: OSC_COUNT below OSC_WIN.LO -> STATUS.CLK_FAULT = 1");
            spi_wr(7'h0A, 16'h0000); spi_rd(7'h01);
            check(rd_val[5] == 1'b0, "spi: OSC_WIN = 0 disables the clock-fault check");
            // mode switch: BiSS frame, SPI, BiSS
            spi_wr(7'h05, 16'h1212); spi_wr(7'h06, 16'h2345); bus_idle;
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            $display("INFO spi/biss frame: busy %0d data 0x%05h nE nW %b crc wire %02h calc~ %02h ack %0d", b_busy, b_data[19:2], b_data[1:0], b_crc_wire, ~b_crc_calc, b_ack_ok);
            check(b_crc_wire == 6'h0D && b_data[19:2] == 18'h12345, "spi/biss: BiSS frame before SPI access");
            spi_wr(7'h06, 16'h0000); spi_wr(7'h05, 16'h0212); spi_rd(7'h06);
            check(rd_val == 16'h0000, "spi/biss: SPI access between BiSS frames");
            bus_idle;
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            check(b_crc_wire == 6'h3A && b_data[19:2] == 18'h0, "spi/biss: BiSS frame after SPI sees the new TEST_POS");
            // MA traffic while CS_N high does not disturb SPI state; SPI after BiSS
            spi_rd(7'h00);
            check(rd_val == 16'h5209, "spi/biss: SPI read correct after BiSS traffic on the shared pad");
        end

        // =================================================================
        if (test == "gate") begin
            begin : gt
                integer t_on_a, t_off_a, t_on_b, t_off_b, t_on_c, t_off_c, tk, t_sa, t_sb, t_is, n_late;
                integer t_az_on, t_az_off, n_sa, n_enc, t_enc, g_enc, g_max, n_g22, n_gx;
                integer per, da, db, dc, pa, pb, pc, dt;
                reg ga_d, gb_d, gc_d, az_d, is_d, gc1;
                per = 1500; da = 600; db = 300; dc = 900; pa = 0; pb = 500; pc = 1000; dt = 15;
                spi_wr(7'h20, per); spi_wr(7'h21, da); spi_wr(7'h22, db); spi_wr(7'h23, dc);
                spi_wr(7'h24, pa); spi_wr(7'h25, pb); spi_wr(7'h26, pc); spi_wr(7'h27, dt);
                spi_wr(7'h38, 16'd1200); spi_wr(7'h39, 16'h2028);   // AZ_START 1200, AZ_LEN 40
                load_cal_crc; spi_wr(7'h04, 16'h0001);      // 0.3: AZ words are CRC-covered -> new CAL_CRC, CLR
                spi_wr(7'h04, 16'h0002);                    // GATE_EN
                #(3 * per * clk_ns);
                // measure one period in ticks relative to the counter wrap
                @(posedge dut.u_gate.pwm_wrap);
                tk = 0; t_on_a = -1; t_off_a = -1; t_on_b = -1; t_off_b = -1; t_on_c = -1; t_off_c = -1;
                t_sa = -1; t_sb = -1; t_is = -1; t_az_on = -1; t_az_off = -1; n_sa = 0;
                n_enc = 0; t_enc = -1; g_max = 0; n_g22 = 0; n_gx = 0;
                ga_d = gate_a; gb_d = gate_b; gc_d = gate_c; az_d = az_win; is_d = is_smp;
                while (tk < per) begin
                    @(posedge clk); #1; tk = tk + 1;
                    if (gate_a && !ga_d) t_on_a = tk;  if (!gate_a && ga_d) t_off_a = tk;
                    if (gate_b && !gb_d) t_on_b = tk;  if (!gate_b && gb_d) t_off_b = tk;
                    if (gate_c && !gc_d) t_on_c = tk;  if (!gate_c && gc_d) t_off_c = tk;
                    if (az_win && !az_d) t_az_on = tk; if (!az_win && az_d) t_az_off = tk;
                    if (is_smp && !is_d) t_is = tk;
                    if (adc_start && adc_sel) begin t_sa = tk; n_sa = n_sa + 1; end
                    if (adc_start && !adc_sel) begin
                        n_enc = n_enc + 1;
                        if (t_enc >= 0) begin
                            g_enc = tk - t_enc; if (g_enc > g_max) g_max = g_enc;
                            if (g_enc == 22) n_g22 = n_g22 + 1; else n_gx = n_gx + 1;
                        end
                        t_enc = tk;
                    end
                    ga_d = gate_a; gb_d = gate_b; gc_d = gate_c; az_d = az_win; is_d = is_smp;
                end
                $display("INFO gate A on %0d off %0d (width %0d), B on %0d off %0d (width %0d), C on %0d off %0d (width %0d); current frame start %0d is_smp %0d; az_win %0d..%0d",
                         t_on_a, t_off_a, (t_off_a - t_on_a + per) % per, t_on_b, t_off_b, t_off_b - t_on_b,
                         t_on_c, t_off_c, (t_off_c - t_on_c + per) % per, t_sa, t_is, t_az_on, t_az_off);
                $display("INFO gate encoder frames in one period %0d: %0d gaps of 22 ticks, %0d other, longest %0d ticks",
                         n_enc, n_g22, n_gx, g_max);
                check((t_off_a - t_on_a + per) % per == da - 2 * dt, "gate: A on-time = DUTY - 2 DEAD");
                check(t_off_b - t_on_b == db - 2 * dt, "gate: B on-time = DUTY - 2 DEAD");
                check((t_off_c - t_on_c + per) % per == dc - 2 * dt, "gate: C on-time = DUTY - 2 DEAD (window wraps the period)");
                check(t_on_b - (pb + dt) == t_on_a - (pa + dt) || t_on_a == -1, "gate: B rising edge at PHASE_B + DEAD (same offset as A)");
                check(t_sa >= 0 && ((t_sa - t_on_a + per) % per) - (da - 2 * dt) / 2 >= -1 &&
                      ((t_sa - t_on_a + per) % per) - (da - 2 * dt) / 2 <= 1, "gate: current strobe at the centre of the A on-time (+-1 tick)");
                check(n_sa == 1 && t_is == t_sa,
                      "gate: one current frame per period; is_smp rises with its start (both slices, adc_sel = 1)");
                check(n_gx <= 1 && g_max <= 22 + 22 + 20 && g_max >= 44 && n_enc >= per / 22 - 2,
                      "gate: D18 frames: encoder frames every 22 ticks, one gap of 44..64 ticks around the current frame");
                check(t_az_off - t_az_on == 40 && t_az_on - t_on_a == 1200 - (pa + dt),
                      "gate: az_win is AZ_LEN = 40 ticks wide and starts at counter value AZ_START");
                // strobes are never late (guard keeps the ADC free) over 20 periods
                spi_rd(7'h35); n_late = rd_val;
                #(20 * per * clk_ns);
                spi_rd(7'h35);
                check(rd_val == n_late, "gate: no late current conversion over 20 PWM periods (guard)");
                spi_rd(7'h33);
                check(rd_val[11:8] == 4'd0, "gate: no position pair overrun with current conversions interleaved");
                // comparator blanking: az_win and AZ_EXT ticks after it (0.7: reset 120; 0.6: fixed 16; exact edges in test v07)
                @(posedge az_win); #(5 * clk_ns); @(negedge clk); cmp[0] = 1'b1; #(4 * clk_ns); cmp[0] = 1'b0;
                @(negedge az_win); #(8 * clk_ns); @(negedge clk); cmp[0] = 1'b1; #(4 * clk_ns); cmp[0] = 1'b0;
                #(20 * clk_ns);
                check(fault_n == 1'b1, "gate: comparator flags inside az_win and 8 ticks after it are blanked");
                #(100 * clk_ns); @(negedge clk); cmp[0] = 1'b1; #(4 * clk_ns); cmp[0] = 1'b0; #(10 * clk_ns);
                check(fault_n == 1'b0, "gate: the same flag 132 ticks after az_win (AZ_EXT 120) latches OC_A");
                spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                check(fault_n == 1'b1, "gate: CLR releases the blanking-test fault");
                // shadow update: change duty mid-period, takes effect at wrap
                spi_wr(7'h21, 16'd200);
                @(posedge dut.u_gate.pwm_wrap); @(posedge dut.u_gate.pwm_wrap);
                tk = 0; t_on_a = -1; t_off_a = -1; ga_d = gate_a;
                while (tk < per) begin
                    @(posedge clk); #1; tk = tk + 1;
                    if (gate_a && !ga_d) t_on_a = tk; if (!gate_a && ga_d) t_off_a = tk;
                    ga_d = gate_a;
                end
                check((t_off_a - t_on_a + per) % per == 200 - 2 * dt, "gate: new DUTY_A applied at the period wrap");
                // DUTY_A <= 2 DEAD: channel A stays off, no current strobe
                spi_wr(7'h21, 16'd20);
                @(posedge dut.u_gate.pwm_wrap); @(posedge dut.u_gate.pwm_wrap);
                tk = 0; nb = 0;
                while (tk < per) begin @(posedge clk); #1; tk = tk + 1; if (gate_a) nb = nb + 1; if (adc_start && adc_sel) nb = nb + 1000; end
                check(nb == 0, "gate: DUTY_A <= 2 DEAD keeps channel A off and suppresses the current strobe");
                spi_wr(7'h21, 16'd600);
                // EN low forces the outputs low immediately
                #(3 * per * clk_ns);
                wait (gate_c == 1'b1); #5;
                en_pad = 1'b0; #1; gc1 = gate_c; #999;
                // 0.5: the criterion is the specification's 1 us (fault path). The zero-delay RTL path is combinational
                // (gc1 below); STA gives 1.47 ns at the slow corner, so a 1 ns limit fails only under SDF.
                check(gate_c == 1'b0, "gate: EN low forces GATE_C low within 1 us (specification; STA: 1.47 ns slow corner)");
                $display("INFO gate: GATE_C = %0b 1 ns after EN low in the zero-delay RTL (combinational path)", gc1);
                #(10 * clk_ns);
                check(fault_n == 1'b0, "gate: EN low latches a fault (FAULT_N low)");
                en_pad = 1'b1; #(10 * clk_ns);
                spi_wr(7'h04, 16'h0003); #(per * 2 * clk_ns);
                check(fault_n == 1'b1, "gate: CLR after EN high releases the fault");
                // ADC weight correction in the path, per slice (D18): ADC_A_W13 + 100 LSB
                // moves I_A by +100 and leaves I_B; ADC_B_W13 + 100 LSB moves I_B only
                ia_code = 12'd2848; ib_code = 12'd2848; #(3 * per * clk_ns);
                spi_rd(7'h29); v16 = rd_val; spi_rd(7'h2A); gray16 = rd_val;
                check(v16 == 16'd2848 && gray16 == 16'd2848, "gate: I_A, I_B = corrected codes with the reset (nominal) weights");
                spi_wr(7'h5D, 16'd8530); #(3 * per * clk_ns);
                spi_rd(7'h29); v16 = rd_val; spi_rd(7'h2A);
                $display("INFO gate with ADC_A_W13 = 8530: I_A %0d I_B %0d", v16, rd_val);
                check(v16 == 16'd2948 && rd_val == 16'd2848, "gate: ADC_A_W13 = 8130 + 400 adds 100 LSB to I_A only (slice A weights)");
                spi_wr(7'h5D, 16'd8130); spi_wr(7'h6D, 16'd8530); #(3 * per * clk_ns);
                spi_rd(7'h29); v16 = rd_val; spi_rd(7'h2A);
                check(v16 == 16'd2848 && rd_val == 16'd2948, "gate: ADC_B_W13 = 8130 + 400 adds 100 LSB to I_B only (slice B weights)");
                spi_wr(7'h6D, 16'd8130); ia_code = 12'd2048; ib_code = 12'd2048;
            end
        end

        // =================================================================
        // comparator offset calibration (r1_cmpcal revision 0.3): behavioural
        // comparators with offset and hysteresis (in calibration steps). Expected
        // codes come from the r1_safe cal_model.py formula (task cexp), not from
        // the RTL algorithm. Where the formula has no in-range result, only
        // EXH = 1 is required (the RTL code is then saturated toward the toggle).
        if (test == "cal") begin
            begin : ct
                integer tk, n_gate, n_win, n_fault, rnd, j, seed, nexp;
                reg az_d;
                reg [3:0] xexh;
                seed = 20261020;
                cofs[0] = 1.3; cofs[1] = -2.6; cofs[2] = 0.4; cofs[3] = -0.2;
                chy[0] = 2.5;  chy[1] = 3.1;   chy[2] = 1.7; chy[3] = 2.9;
                cmp_vin = 0.0;
                spi_wr(7'h20, 16'd300); spi_wr(7'h21, 16'd150);
                spi_wr(7'h38, 16'd200); spi_wr(7'h39, 16'h4E28);    // AZ_START 200, AZ_LEN 40, THR_ZERO 14, STEP 32
                spi_rd(7'h3C);
                check(rd_val == 16'h3748, "cal: CMP_CAL_IDEAL reset = 0x3748 (NEG 55, OC 72 half codes)");
                spi_wr(7'h36, 16'h0528); spi_wr(7'h37, 16'h0528);   // OC 40, NEG 5: not tripped at zero current
                cmp_mdl_en = 1'b1;
                load_cal_crc; spi_wr(7'h04, 16'h0003); #(4 * 300 * clk_ns);
                check(fault_n == 1'b1, "cal: comparators idle at CMP_THR (OC 40, NEG 5), no fault");
                for (rnd = 0; rnd < 10; rnd = rnd + 1) begin
                    if (rnd == 1) begin cofs[0] = 3.9; cofs[1] = -3.7; cofs[2] = 0.0; cofs[3] = 2.2;
                                        chy[0] = 3.3; chy[1] = 0.6; chy[2] = 4.0; chy[3] = 1.0; end
                    if (rnd == 2) begin cofs[0] = 24.0; cofs[1] = -40.0; cofs[2] = 45.0; cofs[3] = -24.0;   // range ends, outside
                                        chy[0] = 2.0; chy[1] = 2.0; chy[2] = 2.0; chy[3] = 2.0; end
                    if (rnd == 3) begin cofs[0] = -27.0; cofs[1] = 27.0; cofs[2] = 27.5; cofs[3] = -28.5;   // near the saturation
                                        chy[0] = 2.0; chy[1] = 2.5; chy[2] = 3.0; chy[3] = 1.5; end
                    if (rnd >= 4) for (j = 0; j < 4; j = j + 1) begin
                        cofs[j] = ($random(seed) % 1000) / 50.0;         // +-20 steps
                        chy[j] = 0.3 + (($random(seed) & 32'h7FFF) % 1000) / 250.0;   // 0.3 .. 4.3 steps
                    end
                    spi_wr(7'h04, 16'h000A);                             // GATE_EN + CMP_CAL
                    #(4 * clk_ns);
                    if (rnd == 0)
                        check(dut.status[11] == 1'b1 && thr_oc_a == 6'd14 && thr_neg_b == 6'd14,
                              "cal: STATUS.CAL_BUSY = 1, every threshold carries THR_ZERO = 14 during the search");
                    tk = 0; n_gate = 0; n_win = 0; n_fault = 0; az_d = az_win;
                    while (dut.status[11] && tk < 40 * 300) begin
                        @(posedge clk); #1; tk = tk + 1;
                        if (gate_a | gate_b | gate_c) n_gate = n_gate + 1;
                        if (dut.u_safe.cause[3:0] != 4'd0) n_fault = n_fault + 1;
                        if (az_d && !az_win) n_win = n_win + 1;
                        az_d = az_win;
                    end
                    nexp = 0;
                    cexp(0, 14, 36.3076923); if (exp_x ? dut.cal_exh[0] : (cal_oc_a == exp_k && !dut.cal_exh[0])) nexp = nexp + 1; xexh[0] = exp_x;
                    $display("INFO cal round %0d OC_A  ofs %7.3f hy %5.3f: RTL %0d exh %0d, model %0d exh %0d", rnd, cofs[0], chy[0], cal_oc_a, dut.cal_exh[0], exp_k, exp_x);
                    cexp(1, 14, 27.6923077); if (exp_x ? dut.cal_exh[1] : (cal_neg_a == exp_k && !dut.cal_exh[1])) nexp = nexp + 1; xexh[1] = exp_x;
                    $display("INFO cal round %0d NEG_A ofs %7.3f hy %5.3f: RTL %0d exh %0d, model %0d exh %0d", rnd, cofs[1], chy[1], cal_neg_a, dut.cal_exh[1], exp_k, exp_x);
                    cexp(2, 14, 36.3076923); if (exp_x ? dut.cal_exh[2] : (cal_oc_b == exp_k && !dut.cal_exh[2])) nexp = nexp + 1; xexh[2] = exp_x;
                    $display("INFO cal round %0d OC_B  ofs %7.3f hy %5.3f: RTL %0d exh %0d, model %0d exh %0d", rnd, cofs[2], chy[2], cal_oc_b, dut.cal_exh[2], exp_k, exp_x);
                    cexp(3, 14, 27.6923077); if (exp_x ? dut.cal_exh[3] : (cal_neg_b == exp_k && !dut.cal_exh[3])) nexp = nexp + 1; xexh[3] = exp_x;
                    $display("INFO cal round %0d NEG_B ofs %7.3f hy %5.3f: RTL %0d exh %0d, model %0d exh %0d", rnd, cofs[3], chy[3], cal_neg_b, dut.cal_exh[3], exp_k, exp_x);
                    $display("INFO cal round %0d: %0d ticks, %0d az windows", rnd, tk, n_win);
                    check(nexp == 4, "cal: 4 codes equal the r1_safe cal_model formula; EXH where it has no in-range result (code then saturated)");
                    if (rnd == 0) begin
                        check(n_win == 14, "cal: search uses 14 auto-zero windows (2 x (6 decisions + range check))");
                        check(n_gate == 0, "cal: gates held off during the search (GATE_EN set)");
                        check(n_fault == 0, "cal: no comparator fault latches during the search (flags blanked)");
                        spi_rd(7'h3A); v16 = rd_val; spi_rd(7'h3B);
                        $display("INFO cal CMP_CAL_A 0x%04h CMP_CAL_B 0x%04h", v16, rd_val);
                        check(v16 == {2'b00, cal_neg_a, 2'b00, cal_oc_a} && rd_val == {2'b00, cal_neg_b, 2'b00, cal_oc_b},
                              "cal: CMP_CAL_A/B read the codes, EXH clear");
                        spi_rd(7'h01);
                        check(rd_val[11] == 1'b0 && rd_val[12] == 1'b1 && rd_val[13] == 1'b0 && rd_val[4] == 1'b0,
                              "cal: STATUS CAL_BUSY 0, CAL_DONE 1, CAL_EXH 0; CAL_VALID 0 (codes are CRC-covered)");
                        spi_rd(7'h02);
                        check(rd_val[11] == 1'b1 && rd_val[3:0] == 4'd0 && thr_oc_a == 6'd40,
                              "cal: after the search CAL fault set until CAL_CRC is rewritten; no comparator fault; thresholds back to CMP_THR");
                        load_cal_crc; spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                        check(fault_n == 1'b1, "cal: new CAL_CRC + CLR clears the fault");
                        tk = 0; n_gate = 0;
                        while (tk < 300) begin @(posedge clk); tk = tk + 1; if (gate_a) n_gate = n_gate + 1; end
                        check(n_gate > 0, "cal: gates run again after the search");
                    end
                    if (rnd == 2) begin
                        spi_rd(7'h3A); v16 = rd_val; spi_rd(7'h3B);
                        check(v16[6] == xexh[0] && v16[14] == xexh[1] && rd_val[6] == xexh[2] && rd_val[14] == xexh[3] &&
                              (xexh != 4'd0), "cal: EXH bits read in CMP_CAL_A/B for offsets outside the range");
                        spi_rd(7'h01);
                        check(rd_val[13] == 1'b1, "cal: STATUS.CAL_EXH = 1");
                    end
                end
                // CMP_CAL_IDEAL moves the result: OC ideal 72 -> 76 (two codes)
                cofs[0] = 1.3; chy[0] = 2.5;
                cexp(0, 14, 36.3076923); j = exp_k;
                spi_wr(7'h3C, 16'h374C); spi_wr(7'h04, 16'h0008);
                #(4 * clk_ns); while (dut.status[11]) @(posedge clk);
                check(cal_oc_a == j - 2, "cal: CMP_CAL_IDEAL.OC + 4 half codes lowers the OC result by 2 codes");
                spi_wr(7'h3C, 16'h3748);
                // host write of the codes (bench use)
                spi_wr(7'h3A, 16'h0510); spi_rd(7'h3A);
                check(rd_val[13:8] == 6'd5 && rd_val[5:0] == 6'd16 && cal_neg_a == 6'd5 && cal_oc_a == 6'd16,
                      "cal: CMP_CAL_A host write reaches the calibration ports");
                spi_rd(7'h01);
                check(rd_val[4] == 1'b0, "cal: a CMP_CAL_A write clears CAL_VALID (CRC coverage 0x36..0x3C)");
                load_cal_crc; spi_rd(7'h01);
                check(rd_val[4] == 1'b1, "cal: CAL_VALID returns after the new CAL_CRC");
                spi_wr(7'h55, 16'h0081); #(4 * clk_ns); spi_rd(7'h01);
                check(rd_val[4] == 1'b0, "cal: a slice-A ADC weight write clears CAL_VALID (CRC coverage 0x50..0x5D)");
                load_cal_crc; spi_rd(7'h01);
                check(rd_val[4] == 1'b1, "cal: CAL_VALID returns after the new CAL_CRC (slice A weights covered)");
                spi_wr(7'h6D, 16'h0081); #(4 * clk_ns); spi_rd(7'h01);
                check(rd_val[4] == 1'b0, "cal: a slice-B ADC weight write clears CAL_VALID (CRC coverage 0x60..0x6D)");
                load_cal_crc; spi_rd(7'h01);
                check(rd_val[4] == 1'b1, "cal: CAL_VALID returns after the new CAL_CRC (weights covered)");
                cmp_mdl_en = 1'b0;
            end
        end

        // =================================================================
        // Revision 0.5 tests
        // tap: tap_p / tap_n against the integer form of the r1_safe formula (the exhaustive 2 x 4096 check is
        //      tb_tapidx.v); here the chip-level chain: CMP_THR and CMP_CAL words -> adders -> ports
        if (test == "tap") begin
            begin : tp
                integer n, j, seed, ok, o_a, n_a, o_b, n_b, ca_o, ca_n, cb_o, cb_n, lane_ok;
                reg [15:0] e0, e1, e2, e3;
                por_n = 0; #(10 * clk_ns); por_n = 1; #(4 * clk_ns);
                check(tap_p == {4{8'd252}} && tap_n == 32'd0,
                      "tap: reset values (0.7) = taps of THR_OC 63 / THR_NEG 0 / CAL 32 (cell code 63: nP 252 nN 0 on all four)");
                #(30 * clk_ns);
                seed = 5;
                ok = 0;
                for (n = 0; n < 40; n = n + 1) begin
                    if (n == 0) begin o_a = 0;  n_a = 0;  o_b = 63; n_b = 63; ca_o = 0;  ca_n = 63; cb_o = 63; cb_n = 0; end
                    else if (n == 1) begin o_a = 63; n_a = 63; o_b = 0; n_b = 0; ca_o = 63; ca_n = 0; cb_o = 0; cb_n = 63; end
                    else if (n == 2) begin o_a = 14; n_a = 14; o_b = 14; n_b = 14; ca_o = 32; ca_n = 32; cb_o = 32; cb_n = 32; end
                    else begin
                        o_a = $random(seed) & 63; n_a = $random(seed) & 63; o_b = $random(seed) & 63; n_b = $random(seed) & 63;
                        ca_o = $random(seed) & 63; ca_n = $random(seed) & 63; cb_o = $random(seed) & 63; cb_n = $random(seed) & 63;
                    end
                    spi_wr(7'h36, {2'b00, n_a[5:0], 2'b00, o_a[5:0]}); spi_wr(7'h37, {2'b00, n_b[5:0], 2'b00, o_b[5:0]});
                    spi_wr(7'h3A, {2'b00, ca_n[5:0], 2'b00, ca_o[5:0]}); spi_wr(7'h3B, {2'b00, cb_n[5:0], 2'b00, cb_o[5:0]});
                    #(4 * clk_ns);
                    e0 = tapx(0, o_a, ca_o); e1 = tapx(1, n_a, ca_n); e2 = tapx(2, o_b, cb_o); e3 = tapx(3, n_b, cb_n);
                    if (tap_p == {e3[7:0], e2[7:0], e1[7:0], e0[7:0]} && tap_n == {e3[15:8], e2[15:8], e1[15:8], e0[15:8]}) ok = ok + 1;
                    else $display("FAIL tap case %0d: tap_p %h tap_n %h, expected %h %h", n, tap_p, tap_n,
                                  {e3[7:0], e2[7:0], e1[7:0], e0[7:0]}, {e3[15:8], e2[15:8], e1[15:8], e0[15:8]});
                end
                check(ok == 40, "tap: 40 threshold/calibration word sets (corners and random) give the formula taps on all four lanes");
                // a write changes only its own comparators, one tick after the register
                spi_wr(7'h36, 16'h0505); #(4 * clk_ns);
                e0 = tapx(0, 5, ca_o); e1 = tapx(1, 5, ca_n);
                check(tap_p[7:0] == e0[7:0] && tap_n[7:0] == e0[15:8] && tap_p[15:8] == e1[7:0] && tap_n[15:8] == e1[15:8],
                      "tap: CMP_THR_A write moves lanes 0 and 1 only");
                // reset restores the reset taps
                por_n = 0; #(10 * clk_ns); por_n = 1; #(4 * clk_ns);
                check(tap_p == {4{8'd252}} && tap_n == 32'd0, "tap: por_n restores the reset taps");
            end
        end

        // ana: ANA_CTRL decode and reset (register map 0.5, section 4.8) and ADC_CFG reset
        if (test == "ana") begin
            begin : an
                integer g, ok;
                reg [3:0] ex;
                por_n = 0; #(10 * clk_ns); por_n = 1; #(4 * clk_ns);
                check(ana_ctrl == 16'h0028 && pga_c == 4'b0000 && t2f_en && !t2f_mode && bias_en,
                      "ana: reset 0x0028: PGA x1 (c1..c4 = 0000), T2F_EN 1, T2F_MODE 0 (PTAT), BIAS_EN 1");
                #(700 * clk_ns); load_cal_crc; spi_wr(7'h04, 16'h0001);
                spi_rd(7'h0C); check(rd_val == 16'h0028, "ana: ANA_CTRL reads 0x0028 after reset");
                spi_rd(7'h3D); check(rd_val == 16'h0001, "ana: ADC_CFG reads 1 after reset (DISCARD 1)");
                ok = 0;
                for (g = 0; g < 8; g = g + 1) begin
                    case (g) 0: ex = 4'b0000; 1: ex = 4'b0001; 2: ex = 4'b0011; 3: ex = 4'b0111; 4: ex = 4'b1011; default: ex = 4'b1111; endcase
                    spi_wr(7'h0C, 16'h0028 | g); #(4 * clk_ns);
                    if (pga_c == ex) ok = ok + 1; else $display("FAIL ana gain code %0d: pga_c %b expected %b", g, pga_c, ex);
                end
                check(ok == 8, "ana: gain codes 0..5 give c1..c4 = 0000 1000 1100 1110 1101 1111 (c1 first), codes 6 and 7 act as 5");
                spi_wr(7'h0C, 16'h0010); #(4 * clk_ns);
                check(!t2f_en && t2f_mode && !bias_en && pga_c == 4'b0000, "ana: bits 3, 4, 5 drive T2F_EN, T2F_MODE, BIAS_EN independently");
                spi_wr(7'h0C, 16'h0008); #(4 * clk_ns);
                check(t2f_en && !t2f_mode && !bias_en, "ana: T2F_EN alone");
                spi_wr(7'h0C, 16'h0020); #(4 * clk_ns);
                check(!t2f_en && !t2f_mode && bias_en, "ana: BIAS_EN alone");
                spi_wr(7'h0C, 16'hFF80); spi_rd(7'h0C); #(4 * clk_ns);
                check(rd_val == 16'hFF80 && pga_c == 4'b0000 && !t2f_en && !t2f_mode && !bias_en, "ana: reserved bits 15:7 store and read back, no output");
                spi_wr(7'h0C, 16'h0028);
            end
        end

        // disc: first-conversion discard (INTERFACES.md "ADC -> ctrl, first conversion")
        if (test == "disc") begin
            begin : dc
                integer j, nfr, st1, st2, st3;
                real th1, th2, th3;
                // ---- A: after the power-on reset, the first frame (garbage from the ADC model) is dropped
                spi_rd(7'h3D); check(rd_val == 16'h0001, "disc: ADC_CFG DISCARD resets to 1");
                spi_wr(7'h20, 16'd0);                                        // no PWM: encoder frames only
                while (conv_a != 0 || conv_b != 0) @(posedge clk);
                #1; por_n = 0; #(10 * clk_ns);
                mon_en = 1'b0; nidx = 0; ast_e = 0; ast_c = 0; dr_e = 0; dr_c = 0; dv_e = 0; dv_c = 0; dn_all = 0; ndh = 0;
                bad_seen = 1'b0; drop_seen = 1'b0; tb_disc = 1; bad_n = 1; arm_p = 1'b0; mon_en = 1'b1;
                por_n = 1;
                // bootstrap pre-charge sequence (INTERFACES.md, first conversion): adc_hold high for 2 ticks without
                // adc_start, then at least 250 ns of track before the first sampling edge
                @(posedge adc_hold); th1 = $realtime; st1 = ast_e + ast_c;
                @(negedge adc_hold); th2 = $realtime; st2 = ast_e + ast_c;
                @(posedge adc_hold); th3 = $realtime; st3 = ast_e + ast_c;
                $display("INFO disc A: pre-charge hold %0.1f ns, track before the first sampling edge %0.1f ns", th2 - th1, th3 - th2);
                check(th2 - th1 > 1.9 * clk_ns && th2 - th1 < 2.1 * clk_ns && st1 == 0 && st2 == 0,
                      "disc: after the reset release adc_hold is high for 2 ticks with no adc_start (bootstrap pre-charge)");
                check(th3 - th2 >= 250.0, "disc: at least 250 ns of track between the pre-charge hold and the first sampling edge");
                #(4 * clk_ns);
                nfr = 0;
                while (dn_all < 6 && nfr < 400) begin @(posedge clk); nfr = nfr + 1; end
                #(2 * clk_ns);
                $display("INFO disc A: starts %0d (dropped %0d), pairs completed %0d, delivered %0d", ast_e, dr_e, dn_all, dv_e);
                check(dr_e == 1 && ast_e >= 6 && dn_all >= 6, "disc: reset: six frames completed, the first one is the dropped frame");
                check(dv_e == dn_all - 1, "disc: reset: smp_valid pulses = completed pairs - 1 (the first conversion gives no smp_valid)");
                check(!bad_seen, "disc: reset: the garbage first conversion (all-ones decisions, code 4095) never reaches sin/cos or the current words");
                // ---- B: ADC_ARM re-arms the discard, 15 frames, PWM running so that current frames occur in the window
                mon_en = 1'b0; bad_n = 0; ia_inc = 1'b1; npre = 0;
                spi_wr(7'h20, 16'd300); spi_wr(7'h21, 16'd150);
                #(700 * clk_ns);
                spi_wr(7'h3D, 16'h000F);
                tb_disc = 15;
                spi_wr(7'h0C, 16'h0068);                                     // ADC_ARM 1 (+ T2F_EN, BIAS_EN)
                #(4 * clk_ns);
                spi_wr(7'h0C, 16'h0028);                                     // ADC_ARM back to 0
                #(1800 * clk_ns);
                check(npre >= 1, "disc: ADC_ARM starts a pre-charge hold (adc_hold pulse of 2 ticks without adc_start)");
                spi_wr(7'h28, 16'h0000); spi_wr(7'h20, 16'd0);               // stop the encoder frames and the PWM
                #(2000 * clk_ns);
                $display("INFO disc B: starts enc %0d cur %0d, dropped enc %0d cur %0d, in flight at arm enc %0d cur %0d, delivered enc %0d cur %0d",
                         ast_e, ast_c, dr_e, dr_c, fl_e, fl_c, dv_e, dv_c);
                check(dr_c >= 1 && dr_e >= 1 && dr_e + dr_c == 15, "disc: ADC_ARM: the 15 dropped frames contain current and encoder frames");
                check(dv_e == ast_e - dr_e + fl_e, "disc: ADC_ARM: delivered encoder pairs = started - dropped + in flight at the arm");
                check(dv_c == ast_c - dr_c + fl_c, "disc: ADC_ARM: delivered current pairs = started - dropped + in flight at the arm");
                check(ast_c > dr_c && ast_e > dr_e, "disc: ADC_ARM: frames after the dropped ones are delivered (both types)");
                check(!drop_seen, "disc: ADC_ARM: the code of a dropped current frame never reaches i_a");
                // ---- C: DISCARD = 0 drops nothing
                spi_wr(7'h28, 16'h1416);
                #(300 * clk_ns);
                spi_wr(7'h3D, 16'h0000);
                tb_disc = 0;
                spi_wr(7'h0C, 16'h0068); #(4 * clk_ns); spi_wr(7'h0C, 16'h0028);
                #(500 * clk_ns);
                spi_wr(7'h28, 16'h0000);
                #(100 * clk_ns);
                $display("INFO disc C: starts enc %0d cur %0d, dropped enc %0d cur %0d, in flight at arm enc %0d, delivered enc %0d", ast_e, ast_c, dr_e, dr_c, fl_e, dv_e);
                check(dr_e == 0 && dr_c == 0 && ast_e >= 10 && dv_e == ast_e + fl_e, "disc: DISCARD = 0: no frame dropped, every encoder pair delivered");
                spi_wr(7'h3D, 16'h0001); spi_wr(7'h28, 16'h1416);
            end
        end

        // cdc: revision 0.5 clock-domain crossing tests (README, CDC table; findings D and F of the 0.4 sign-off)
        //   (a) SSI at the asynchronous worst phase: the published word changes at EVERY clk tick (two position
        //       patterns that differ in all transmitted bits), the first MA falling edge is moved over 16 phases of
        //       the clk period, at the documented limit of 2 MHz (the freeze needs about 3 ticks). Every received word
        //       must be one complete pattern (no mix of the two). At 10 MHz (outside the limit) the same test is run for information.
        //   (b) the reset of the ma domain changes to 1 only at clk edges (registered release, finding F).
        if (test == "cdc") begin
            begin : cd
                integer ph, nb, n_ok, n_mix, n_p0, n_p1, rep;
                reg [12:0] w0, w1;
                real th;
                spi_wr(7'h05, 16'h004D); bus_idle;               // SSI, MT off, ST 13 bit, binary
                w0 = 13'b1010101010101; w1 = 13'b0101010101010;  // top 13 bits of the two patterns
                alt_pos = 18'h2AAAA;
                force dut.frame_pos = alt_pos;
                cdc_mon = 1'b1;
                n_ok = 0; n_mix = 0; n_p0 = 0; n_p1 = 0;
                for (ph = 0; ph < 16; ph = ph + 1) begin
                    #(ph * clk_ns / 16.0);
                    ssi_frame(250.0, 250.0, 13);                 // 2 MHz
                    if (s_data[12:0] == w0) n_p0 = n_p0 + 1;
                    else if (s_data[12:0] == w1) n_p1 = n_p1 + 1;
                    else begin n_mix = n_mix + 1; $display("INFO cdc: 2 MHz phase %0d mixed word %b", ph, s_data[12:0]); end
                end
                $display("INFO cdc: SSI 2 MHz, 16 clk phases, position changing every tick: pattern 0 %0d, pattern 1 %0d, mixed %0d", n_p0, n_p1, n_mix);
                check(n_mix == 0 && n_p0 + n_p1 == 16, "cdc D: SSI at 2 MHz, 16 asynchronous phases, word changing every tick: 16 of 16 words complete (no mix)");
                check(n_p0 > 0 && n_p1 > 0, "cdc D: both position patterns occur over the phases (the test samples the changing word)");
                n_mix = 0; n_p0 = 0; n_p1 = 0;
                for (ph = 0; ph < 16; ph = ph + 1) begin
                    #(ph * clk_ns / 16.0);
                    ssi_frame(50.0, 50.0, 13);                   // 10 MHz: outside the documented SSI limit
                    if (s_data[12:0] == w0) n_p0 = n_p0 + 1;
                    else if (s_data[12:0] == w1) n_p1 = n_p1 + 1;
                    else n_mix = n_mix + 1;
                end
                $display("INFO cdc: SSI 10 MHz (outside the 2 MHz limit), 16 clk phases: pattern 0 %0d, pattern 1 %0d, mixed %0d (information, not a check)", n_p0, n_p1, n_mix);
                release dut.frame_pos;
                // BiSS frames, an SPI session and the timeout resets in between, for the ma-domain reset monitor
                spi_wr(7'h05, 16'h40B2); bus_idle;
                biss_frame(250.0, 250.0, 20, 1'b0, 0); biss_frame(250.0, 250.0, 20, 1'b0, 0);
                spi_rd(7'h00); bus_idle;
                biss_frame(250.0, 250.0, 20, 1'b0, 0);
                cdc_mon = 1'b0;
                $display("INFO cdc: ma_rst_n rising edges %0d (off a clk edge: %0d), falling edges %0d", n_mr_rise, n_mr_off, n_mr_fall);
                check(n_mr_rise >= 5 && n_mr_off == 0, "cdc F: the reset of the ma domain is released only at clk edges (registered), at least 5 releases observed");
            end
        end

        // calmc: RTL search on the r1_safe MC comparator tables (tb/cmpcal_ref.py)
        if (test == "calmc") begin
            begin : cm
                integer fv, fo, nv, g, j, kk, rc, role, kc, ex, ng;
                reg [1023:0] vfile, ofile;
                real x;
                integer mk [0:3];
                if (!$value$plusargs("vec=%s", vfile)) vfile = "cmpcal_vec.txt";
                if (!$value$plusargs("out=%s", ofile)) ofile = "calmc_rtl.txt";
                fv = $fopen(vfile, "r"); fo = $fopen(ofile, "w");
                rc = $fscanf(fv, "%d", nv);
                spi_wr(7'h20, 16'd300); spi_wr(7'h21, 16'd150);
                spi_wr(7'h38, 16'd200); spi_wr(7'h39, 16'h4E28);
                cmp_tab = 1'b1; cmp_mdl_en = 1'b1;
                ng = 0;
                for (g = 0; g < nv; g = g + 4) begin
                    for (j = 0; j < 4; j = j + 1) begin
                        if (g + j < nv) begin
                            rc = $fscanf(fv, "%d %d %d", role, kc, ex);
                            for (kk = 0; kk < 64; kk = kk + 1) begin rc = $fscanf(fv, "%f", x); tabu[64 * j + kk] = x; end
                            for (kk = 0; kk < 64; kk = kk + 1) begin rc = $fscanf(fv, "%f", x); tabd[64 * j + kk] = x; end
                            if (role != (j % 2)) $display("FAIL calmc vector %0d role %0d on comparator %0d", g + j, role, j);
                        end else
                            for (kk = 0; kk < 64; kk = kk + 1) begin tabu[64 * j + kk] = kk - 30.0; tabd[64 * j + kk] = kk - 34.0; end
                    end
                    spi_wr(7'h04, 16'h0008); #(4 * clk_ns);
                    while (dut.status[11]) @(posedge clk);
                    mk[0] = cal_oc_a; mk[1] = cal_neg_a; mk[2] = cal_oc_b; mk[3] = cal_neg_b;
                    for (j = 0; j < 4; j = j + 1)
                        if (g + j < nv) $fdisplay(fo, "R %0d %0d %0d", g + j, mk[j], dut.cal_exh[j]);
                    ng = ng + 1;
                end
                $fclose(fo); $fclose(fv);
                $display("INFO calmc: %0d vectors in %0d searches written to %0s", nv, ng, ofile);
                check(nv > 0, "calmc: vectors read and RTL results written (compared by cmpcal_ref.py check)");
                cmp_mdl_en = 1'b0; cmp_tab = 1'b0;
            end
        end


        // =================================================================
        // Revision 0.7 tests (README revision 0.7). Only ports and SPI are used, so the group also runs at gate level.
        if (test == "v07") begin
            begin : v7
                integer j, ok, cnt, hi, fast, per;
                // ---- 1. R3: EN/STO_IN synchroniser reset value
                en_pad = 1'b1; por_n = 0; #(10 * clk_ns); por_n = 1; #(20 * clk_ns);
                spi_rd(7'h00); check(rd_val == 16'h5209, "v07: ID reads 0x5209 (RTL revision 0.9)");
                spi_rd(7'h02);
                $display("INFO v07 R3: FAULT after power-up with EN high = 0x%04h", rd_val);
                check(rd_val == 16'h1800, "v07 R3: power-up with EN high: FAULT = 0x1800 (POR, CAL), STO bit 8 clear");
                #(700 * clk_ns); load_cal_crc; spi_wr(7'h04, 16'h0001); #(20 * clk_ns);
                spi_rd(7'h02); check(rd_val == 16'h0000 && fault_n, "v07 R3: CAL_CRC and one CLR clear FAULT to 0 (no STO to clear)");
                en_pad = 1'b0; por_n = 0; #(10 * clk_ns); por_n = 1; #(20 * clk_ns);
                spi_rd(7'h02);
                $display("INFO v07 R3: FAULT after power-up with EN low = 0x%04h", rd_val);
                check(rd_val == 16'h1900 && !fault_n && !gate_a && !gate_b && !gate_c,
                      "v07 R3: power-up with EN low still latches STO: FAULT = 0x1900, gates low");
                spi_wr(7'h04, 16'h0001); #(20 * clk_ns); spi_rd(7'h02);
                check(rd_val[8], "v07 R3: CLR while EN is low keeps STO");
                en_pad = 1'b1; #(700 * clk_ns); load_cal_crc; spi_wr(7'h04, 16'h0001); #(20 * clk_ns);
                spi_rd(7'h02); check(rd_val == 16'h0000 && fault_n, "v07 R3: after EN high, CAL_CRC and CLR the FAULT word is 0");

                // ---- 2. R4: comparator threshold reset at zero current (behavioural comparators, input = zero-current level)
                for (j = 0; j < 4; j = j + 1) begin cofs[j] = 0.0; chy[j] = 4.0; end
                cmp_tab = 1'b0; cmp_vin = 0.0; cmp_mdl_en = 1'b1;
                por_n = 0; #(10 * clk_ns); por_n = 1; #(20 * clk_ns);
                spi_rd(7'h36); ok = (rd_val == 16'h003F); spi_rd(7'h37); ok = ok && (rd_val == 16'h003F);
                check(ok, "v07 R4: CMP_THR_A and CMP_THR_B reset 0x003F (THR_OC 63, THR_NEG 0)");
                check(tap_p == {4{8'd252}} && tap_n == 32'd0, "v07 R4: reset taps nP 252 nN 0 on all four comparators (cell code 63)");
                #(700 * clk_ns); load_cal_crc; spi_wr(7'h04, 16'h0001); #(40 * clk_ns);
                spi_rd(7'h02);
                $display("INFO v07 R4: zero-current power-up, flags %b, FAULT 0x%04h", cmp_mdl, rd_val);
                check(cmp_mdl == 4'b0000 && rd_val == 16'h0000 && fault_n,
                      "v07 R4: zero-current power-up: no OC/NEG flag, CAL_CRC + CLR give FAULT 0");
                // the revision-0.6 reset value reproduces the finding
                spi_wr(7'h36, 16'h3F3F); spi_wr(7'h37, 16'h3F3F); #(40 * clk_ns);
                check(cmp_mdl == 4'b1010, "v07 R4: with the 0.6 value 0x3F3F both NEG flags are high at zero current (finding reproduced)");
                load_cal_crc; spi_wr(7'h04, 16'h0001); #(20 * clk_ns); spi_rd(7'h02);
                check(rd_val[1] && rd_val[3] && !fault_n, "v07 R4: with 0x3F3F, CLR cannot clear FAULT bits 1 and 3");
                spi_wr(7'h36, 16'h003F); spi_wr(7'h37, 16'h003F); #(40 * clk_ns);
                load_cal_crc; spi_wr(7'h04, 16'h0001); #(20 * clk_ns); spi_rd(7'h02);
                check(rd_val == 16'h0000 && fault_n, "v07 R4: back at 0x003F, CLR works");
                cmp_mdl_en = 1'b0; cmp_vin = 100.0; #(20 * clk_ns);

                // ---- 3. reset values of the analog-facing registers (table in README revision 0.7)
                por_n = 0; #(10 * clk_ns); por_n = 1; #(20 * clk_ns);
                ok = 0;
                spi_rd(7'h08); ok = ok + (rd_val == 16'h0016 && osc_trim == 5'd22);
                spi_rd(7'h0C); ok = ok + (rd_val == 16'h0028 && pga_c == 4'b0000 && t2f_en && !t2f_mode && bias_en);
                spi_rd(7'h38); ok = ok + (rd_val == 16'h0000);
                spi_rd(7'h39); ok = ok + (rd_val == 16'h4E00);
                spi_rd(7'h3A); ok = ok + (rd_val == 16'h2020);
                spi_rd(7'h3B); ok = ok + (rd_val == 16'h2020);
                spi_rd(7'h3C); ok = ok + (rd_val == 16'h3748);
                spi_rd(7'h3D); ok = ok + (rd_val == 16'h0001);
                spi_rd(7'h3E); ok = ok + (rd_val == 16'h0078);
                spi_rd(7'h5D); ok = ok + (rd_val == 16'd8130);
                spi_rd(7'h6D); ok = ok + (rd_val == 16'd8130);
                spi_rd(7'h01); ok = ok + (rd_val[14] == 1'b0);
                check(ok == 12 && !az_win && !gate_a && !gate_b && !gate_c,
                      "v07: reset values OSC_CFG 0x16, ANA_CTRL 0x28, AZ_START 0, AZ_CFG 0x4E00, CMP_CAL 0x2020, IDEAL 0x3748, ADC_CFG 1, AZ_EXT 120, W13 8130, TRIM_UNLK 0; az_win and gates low");

                // ---- 4. OSC_TRIM lock (PLAN.md D13 amendment)
                spi_wr(7'h08, 16'h000A); spi_rd(7'h08);
                check(rd_val == 16'h0016 && osc_trim == 5'd22, "v07 lock: code 10 ignored after reset (locked)");
                spi_wr(7'h08, 16'h0013); spi_rd(7'h08);
                check(rd_val == 16'h0013 && osc_trim == 5'd19, "v07 lock: code 19 (>= 18) accepted while locked");
                spi_wr(7'h08, 16'h0016);
                spi_wr(7'h0A, 16'h2814);                            // OSC_WIN LO 20, HI 40 (40 MHz with a 1 MHz reference)
                spi_rd(7'h09); spi_rd(7'h01);
                check(rd_val[14] == 1'b0, "v07 lock: an OSC_COUNT read before OSC_DONE does not unlock");
                spi_wr(7'h0A, 16'h1D14);                            // HI 29: the 30 MHz count is above the window
                spi_wr(7'h08, 16'h0116); sck_half = 500.0; spi_x(24'd0, 40); sck_half = 50.0; #(20 * clk_ns);
                spi_rd(7'h09); cnt = rd_val; spi_rd(7'h01);
                $display("INFO v07 lock: clk %0.3f ns, OSC_COUNT %0d (OSC_COUNT[11:4] = %0d), STATUS 0x%04h", clk_ns, cnt, cnt >> 4, rd_val);
                check(rd_val[10] && (rd_val[14] == ((cnt >> 4) <= 29 && (cnt >> 4) >= 20)),
                      "v07 lock: a completed count unlocks only when it is inside OSC_WIN (HI 29)");
                spi_wr(7'h0A, 16'h2814); spi_rd(7'h09); spi_rd(7'h01);
                fast = ((cnt >> 4) > 40);
                check(rd_val[14] == !fast, "v07 lock: with HI 40, the read unlocks if and only if OSC_COUNT[11:4] <= 40");
                spi_wr(7'h08, 16'h000A); spi_rd(7'h08);
                if (fast) check(rd_val == 16'h0016, "v07 lock: count above 40 MHz: code 10 still ignored");
                else begin
                    check(rd_val == 16'h000A && osc_trim == 5'd10, "v07 lock: code 10 accepted after the qualifying OSC_COUNT read");
                    spi_rd(7'h01); check(rd_val[14] == 1'b0, "v07 lock: the accepted change consumes TRIM_UNLK");
                    spi_wr(7'h08, 16'h0005); spi_rd(7'h08);
                    check(rd_val == 16'h000A, "v07 lock: a second lower code is ignored until the next qualifying read");
                    spi_wr(7'h08, 16'h010A); sck_half = 500.0; spi_x(24'd0, 40); sck_half = 50.0; #(20 * clk_ns);
                    spi_rd(7'h08); check(rd_val == 16'h000A, "v07 lock: MEAS with the same code is accepted (code unchanged)");
                    spi_rd(7'h09); spi_wr(7'h08, 16'h0005); spi_rd(7'h08);
                    check(rd_val == 16'h0005 && osc_trim == 5'd5, "v07 lock: after a new measurement and read, code 5 is accepted");
                end
                spi_wr(7'h0A, 16'h0000); spi_wr(7'h08, 16'h0116); sck_half = 500.0; spi_x(24'd0, 40); sck_half = 50.0; #(20 * clk_ns);
                spi_rd(7'h09); spi_rd(7'h01);
                check(rd_val[14] == 1'b0, "v07 lock: with OSC_WIN = 0 (no window) a read does not unlock");
                por_n = 0; #(10 * clk_ns); por_n = 1; #(20 * clk_ns);
                spi_rd(7'h08); check(rd_val == 16'h0016, "v07 lock: por_n restores code 22 and the lock");

                // ---- 5. comparator mask az_win + AZ_EXT (INTERFACES.md "vref_b disturbance"); CMP_FILT 0 = 1-tick flags latch
                per = 1500;
                #(700 * clk_ns);
                spi_wr(7'h20, per); spi_wr(7'h21, 16'd300); spi_wr(7'h24, 16'd0);
                spi_wr(7'h38, 16'd800); spi_wr(7'h39, 16'h4E28);     // AZ_START 800, AZ_LEN 40
                load_cal_crc; spi_wr(7'h04, 16'h0001); #(20 * clk_ns);
                check(fault_n, "v07 mask: setup, no fault");
                // a 4-tick flag inside az_win
                @(posedge az_win); repeat (5) @(posedge clk); @(negedge clk); cmp[0] = 1'b1; repeat (4) @(negedge clk); cmp[0] = 1'b0;
                #(20 * clk_ns);
                check(fault_n, "v07 mask: a flag inside az_win does not trip");
                // the first sample after the az_win rise is masked
                @(posedge az_win); @(negedge clk); cmp[2] = 1'b1; @(negedge clk); cmp[2] = 1'b0; #(20 * clk_ns);
                check(fault_n, "v07 mask: a 1-tick flag sampled at the first edge after the az_win rise does not trip");
                // 1-tick flag sampled at the edge AZ_EXT = 120 ticks after the az_win fall: masked
                @(negedge az_win); repeat (119) @(posedge clk); @(negedge clk); cmp[0] = 1'b1; @(negedge clk); cmp[0] = 1'b0;
                #(20 * clk_ns);
                check(fault_n, "v07 mask: a flag sampled 120 ticks (AZ_EXT) after the az_win fall does not trip");
                // the same flag one tick later: latches OC_A
                @(negedge az_win); repeat (120) @(posedge clk); @(negedge clk); cmp[0] = 1'b1; @(negedge clk); cmp[0] = 1'b0;
                #(20 * clk_ns); spi_rd(7'h02);
                check(!fault_n && rd_val == 16'h0001, "v07 mask: the same flag 121 ticks after the az_win fall latches OC_A");
                spi_wr(7'h04, 16'h0001); #(20 * clk_ns);
                // programmable: AZ_EXT 30
                spi_wr(7'h3E, 16'd30); spi_rd(7'h3E); check(rd_val == 16'd30, "v07 mask: AZ_EXT write reads back");
                @(negedge az_win); repeat (29) @(posedge clk); @(negedge clk); cmp[1] = 1'b1; @(negedge clk); cmp[1] = 1'b0;
                #(20 * clk_ns);
                check(fault_n, "v07 mask: AZ_EXT 30: a flag 30 ticks after the fall does not trip");
                @(negedge az_win); repeat (30) @(posedge clk); @(negedge clk); cmp[1] = 1'b1; @(negedge clk); cmp[1] = 1'b0;
                #(20 * clk_ns); spi_rd(7'h02);
                check(!fault_n && rd_val == 16'h0002, "v07 mask: AZ_EXT 30: a flag 31 ticks after the fall latches NEG_A");
                spi_wr(7'h04, 16'h0001); #(20 * clk_ns);
                // AZ_EXT 0: only the window itself is masked
                spi_wr(7'h3E, 16'd0);
                @(negedge az_win); @(negedge clk); cmp[3] = 1'b1; @(negedge clk); cmp[3] = 1'b0;
                #(20 * clk_ns); spi_rd(7'h02);
                check(!fault_n && rd_val == 16'h0008, "v07 mask: AZ_EXT 0: a flag at the first edge after the fall latches NEG_B");
                spi_wr(7'h3E, 16'd120); spi_wr(7'h04, 16'h0001); #(20 * clk_ns);
                // a long flag that starts in the window and stays high trips once the mask ends
                @(posedge az_win); repeat (5) @(posedge clk); @(negedge clk); cmp[2] = 1'b1;
                j = 0; while (fault_n && j < 400) begin @(posedge clk); #1; j = j + 1; end
                cmp[2] = 1'b0;
                $display("INFO v07 mask: flag from az_win start + 5 ticks, FAULT_N low after %0d ticks (window 40 + AZ_EXT 120 + 2 sync + 2 latch)", j);
                check(!fault_n && j >= 35 + 120 && j <= 35 + 120 + 6, "v07 mask: a flag held through the window trips 120 + a few ticks after the window ends");
                spi_wr(7'h04, 16'h0001); #(20 * clk_ns);
                check(fault_n, "v07 mask: CLR releases");

                // ---- 6. cur_trk (r1_adc SAR S1): high before the current strobe, low at the encoder frames
                begin : ct
                    integer tk2, run, n_cur, n_cur_ok, n_enc, n_enc_ok, min_run, ovl, n_ovl;
                    reg in_enc;
                    @(posedge az_win); tk2 = 0; run = 0; n_cur = 0; n_cur_ok = 0; n_enc = 0; n_enc_ok = 0;
                    min_run = 9999; ovl = 0; n_ovl = 0; in_enc = 1'b0;
                    while (tk2 < 4 * per) begin
                        @(posedge clk); #1; tk2 = tk2 + 1;
                        if (adc_start && adc_sel) begin
                            n_cur = n_cur + 1;
                            if (cur_trk && run >= 20) n_cur_ok = n_cur_ok + 1;
                            if (run < min_run) min_run = run;
                        end
                        if (adc_start && !adc_sel) begin
                            n_enc = n_enc + 1; if (!cur_trk) n_enc_ok = n_enc_ok + 1;
                            in_enc = 1'b1;
                        end
                        if (in_enc && adc_valid_a) begin in_enc = 1'b0; if (ovl > 0) n_ovl = n_ovl + 1; ovl = 0; end
                        else if (in_enc && cur_trk) ovl = ovl + 1;
                        run = cur_trk ? run + 1 : 0;
                    end
                    $display("INFO v07 cur_trk: %0d current frames, cur_trk high for >= %0d ticks up to each strobe (GUARD 20); %0d encoder frames, %0d with cur_trk low at the start; %0d encoder frames still converting when cur_trk rose",
                             n_cur, min_run, n_enc, n_enc_ok, n_ovl);
                    check(n_cur == 4 && n_cur_ok == 4, "v07 cur_trk: high at every current-frame start and for >= GUARD = 20 ticks before it");
                    check(n_enc > 200 && n_enc_ok == n_enc, "v07 cur_trk: low at the start (sampling edge) of every encoder frame");
                    spi_wr(7'h20, 16'd0); #(50 * clk_ns);
                    check(!cur_trk, "v07 cur_trk: low with the PWM off (no current strobe)");
                end
                spi_wr(7'h20, 16'd0);
            end
        end

        // =================================================================
        if (test == "safe") begin
            begin : sf
                integer src, tk, t_trip, t_exp, kupd, upd_ticks;
                reg [23:0] e_mod;
                reg [15:0] sqv;
                spi_wr(7'h20, 16'd300); spi_wr(7'h21, 16'd150); spi_wr(7'h22, 16'd150);
                spi_wr(7'h25, 16'd150); spi_wr(7'h04, 16'h0002);
                #(2000 * clk_ns);
                check(gate_a === 1'b1 || gate_a === 1'b0, "safe: gates running");
                // comparator flags
                for (src = 0; src < 4; src = src + 1) begin
                    @(negedge clk); cmp[src] = 1'b1;
                    tk = 0; while (fault_n && tk < 20) begin @(posedge clk); #1; tk = tk + 1; end
                    cmp[src] = 1'b0;
                    #(10 * clk_ns);
                    spi_rd(7'h02);
                    $display("INFO safe cmp[%0d]: FAULT 0x%04h, FAULT_N low after %0d ticks", src, rd_val, tk);
                    check(rd_val == (16'h1 << src) && !fault_n && !gate_a && !gate_b && !gate_c,
                          "safe: comparator flag latches its FAULT bit, FAULT_N low, gates low");
                    check(tk <= 6, "safe: comparator to FAULT_N within 6 ticks (< 1 us)");
                    spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                    check(fault_n, "safe: CLR releases the comparator fault");
                end
                // over-temperature: T2F at 2 MHz, window 2^12 ticks
                spi_wr(7'h34, 16'd12); spi_wr(7'h2C, 16'd100);
                fork
                    begin : t2f_gen
                        forever begin #250 t2f_clk = ~t2f_clk; end
                    end
                    begin #(3 * 4096 * clk_ns + 1000); disable t2f_gen; end
                join
                spi_rd(7'h2B);
                $display("INFO safe TEMP count %0d (2 MHz over 4096 ticks, expected %0.1f)", rd_val, 4096.0 * clk_ns / 500.0);
                spi_rd(7'h02);
                check(rd_val[4] && !fault_n, "safe: T2F count >= OT_LIM latches OTEMP");
                spi_wr(7'h2C, 16'hFFFF); #(2 * 4096 * clk_ns); spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                check(fault_n, "safe: OTEMP clears after the count drops below OT_LIM");
                // amplitude loss
                enc_amp = 50.0; #(20000);
                spi_rd(7'h02);
                check(rd_val[5] && !fault_n, "safe: amplitude low latches AMP");
                enc_amp = 1400.0; #(20000); spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                check(fault_n, "safe: AMP clears with the amplitude restored");
                // overspeed: 20 kHz el against a limit of 1 LSB/tick (32 units)
                spi_wr(7'h0F, 16'd32); enc_f = 20000.0; #(100000);
                spi_rd(7'h02);
                check(rd_val[6] && !fault_n, "safe: |VELOCITY| > OVS_LIM latches OVERSPEED");
                enc_f = 1000.0; #(100000); spi_wr(7'h0F, 16'h4000); spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                check(fault_n, "safe: OVERSPEED clears below the limit");
                // watchdog: period 4 x 1024 ticks, no bus traffic
                spi_wr(7'h0B, 16'd4); spi_wr(7'h04, 16'h0006);
                tk = 0; while (fault_n && tk < 10000) begin @(posedge clk); tk = tk + 1; end
                $display("INFO safe watchdog fired %0d ticks after the last SPI frame (period 4096 ticks)", tk);
                spi_rd(7'h02);
                check(rd_val[7] && tk > 3900 && tk < 4300, "safe: watchdog latches WDT after WDT x 1024 ticks without bus traffic");
                spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                check(fault_n, "safe: WDT clears (watchdog disabled, kicked by the SPI frame)");
                // calibration invalid: a write to a cal register
                spi_wr(7'h16, 16'h1234); #(60 * clk_ns);
                spi_rd(7'h02);
                check(rd_val[11] && !fault_n, "safe: write to a calibration register -> CAL invalid fault");
                spi_wr(7'h04, 16'h0003); #(60 * clk_ns);
                check(!fault_n, "safe: CLR does not release the fault while CAL_CRC mismatches");
                load_cal_crc;
                spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                check(fault_n, "safe: CLR releases the fault after the correct CAL_CRC is written");
                spi_wr(7'h03, 16'h0800);
                spi_wr(7'h16, 16'h0000); #(60 * clk_ns);
                check(!fault_n, "safe: CAL fault cannot be masked");
                load_cal_crc; spi_wr(7'h03, 16'h0000); spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                // I2t: |I - I_ZERO| = 800 codes -> i = 50, i^2 = 2500; TAU 6, PRE 0, LIM 2000
                ia_code = 12'd2048; ib_code = 12'd2048;
                spi_wr(7'h2F, 16'd2048); spi_wr(7'h2D, 16'h0000);   // TAU 0: E follows i^2 = 0
                #(10 * 300 * clk_ns);
                spi_wr(7'h2E, 16'd2000); spi_wr(7'h2D, 16'h0006);
                spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                spi_rd(7'h02); $display("INFO safe FAULT before I2t 0x%04h", rd_val);
                ia_code = 12'd2848;
                // model: same integer recursion as the RTL
                e_mod = 24'd0; kupd = 0; sqv = 16'd2500;
                while (e_mod[23:8] < 16'd2000) begin
                    e_mod = e_mod + (($signed({2'b00, sqv, 8'd0}) - $signed({2'b00, e_mod})) >>> 6);
                    kupd = kupd + 1;
                end
                tk = 0; while (fault_n && tk < 200000) begin @(posedge clk); tk = tk + 1; end
                upd_ticks = 300;
                $display("INFO safe I2t: trip after %0d ticks = %0.1f PWM periods; integer model %0d updates; closed form %0.2f updates",
                         tk, tk / 300.0, kupd, $ln(1.0 - 2000.0 / 2500.0) / $ln(1.0 - 1.0 / 64.0));
                spi_rd(7'h02);
                check(rd_val[9] && !rd_val[10], "safe: I2T_A latches (I2T_B stays clear)");
                check(tk >= (kupd - 1) * upd_ticks && tk <= (kupd + 2) * upd_ticks,
                      "safe: I2t trip time = integer-model update count (+-1 PWM period, sample alignment)");
                ia_code = 12'd2048;
                // EN/STO low: gates low at once, fault latched, not maskable
                while (dut.u_safe.e_a[23:8] >= 16'd2000) #(1000);
                spi_wr(7'h03, 16'h0100); spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                check(fault_n, "safe: I2t clears after the model cools below the limit");
                en_pad = 1'b0; #(10 * clk_ns);
                spi_rd(7'h02);
                check(rd_val[8] && !fault_n && !gate_a && !gate_b && !gate_c, "safe: EN low latches STO (mask ignored), gates low");
                en_pad = 1'b1; spi_wr(7'h03, 16'h0000); spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                check(fault_n, "safe: STO clears after EN returns high and CLR");
                // power-on fault
                por_n = 0; #(10 * clk_ns); por_n = 1; #(20 * clk_ns);
                check(!fault_n && dut.u_safe.cause[12] && dut.u_safe.cause[11], "safe: power-on reset latches POR and CAL (gates disabled until CAL_CRC and CLR)");
            end
        end

        // =================================================================
        // Revision 0.8 test d22 (PLAN.md D22). Only ports and SPI are used, so the group also runs at gate level.
        if (test == "d22") begin
            begin : d22t
                integer j, smin, smax, cmin, cmax, os_i, oc_i, gs_i, gc_i;
                real a_s, a_c, a_t, e, e0, e1, ang;
                // ---- 1. ID and reset values of the D22 words
                spi_rd(7'h00); check(rd_val == 16'h5209, "d22: ID reads 0x5209 (RTL revision 0.9)");
                spi_rd(7'h10); j = rd_val; spi_rd(7'h11); j = j | rd_val;
                check(j == 0, "d22: SIN_OFS (0x10) and COS_OFS (0x11) reset 0");
                spi_rd(7'h12); j = rd_val; spi_rd(7'h3F);
                check(j == 16'h4000 && rd_val == 16'h4000, "d22: SIN_GAIN (0x12) and COS_GAIN (0x3F) reset 0x4000 = 1.0");
                // ---- 2. capture clear (encoder frames stopped: PAIR_TICKS 0)
                spi_wr(7'h28, 16'h1400); #(100 * clk_ns);
                spi_rd(7'h5E); smin = rd_val; spi_rd(7'h5F); smax = rd_val; spi_rd(7'h6E); cmin = rd_val; spi_rd(7'h6F); cmax = rd_val;
                $display("INFO d22 capture since reset: SIN %0d..%0d COS %0d..%0d", smin, smax, cmin, cmax);
                check(smin <= smax && cmin <= cmax, "d22: capture runs from reset (encoder pairs captured, MIN <= MAX)");
                spi_wr(7'h5E, 16'h0000); #(5 * clk_ns);
                spi_rd(7'h5E); smin = rd_val; spi_rd(7'h5F); smax = rd_val; spi_rd(7'h6E); cmin = rd_val; spi_rd(7'h6F); cmax = rd_val;
                check(smin == 12'hFFF && smax == 0 && cmin == 12'hFFF && cmax == 0,
                      "d22: a write to RAW_SIN_MIN (0x5E) clears all four: MIN 0xFFF, MAX 0x000");
                // ---- 3. COS_GAIN read/write and CRC coverage
                spi_wr(7'h3F, 16'h4321); spi_rd(7'h3F);
                check(rd_val == 16'h4321, "d22: COS_GAIN read back 0x4321 (16 bit)");
                crc_v07 = 1'b1; load_cal_crc; crc_v07 = 1'b0;
                spi_rd(7'h01);
                check(!rd_val[4], "d22: CAL_CRC over the 43 words of 0.7 (without COS_GAIN) leaves CAL_VALID 0");
                load_cal_crc; spi_rd(7'h01);
                check(rd_val[4], "d22: CAL_CRC over the 0.9 word set (48 words, incl. COS_GAIN 0x3F) sets CAL_VALID");
                spi_wr(7'h3F, 16'h4000); #(20 * clk_ns); spi_rd(7'h01);
                check(!rd_val[4], "d22: a write of COS_GAIN clears CAL_VALID (CRC-covered word)");
                load_cal_crc; spi_wr(7'h04, 16'h0001); #(20 * clk_ns);
                check(fault_n, "d22: CAL_CRC and CLR release the CAL fault");
                // ---- 4. head with D22 errors: +57 / -57 LSB (25 mV), sine gain 1.03, amplitude 1638 LSB; capture 2 periods
                enc_amp = 1638.0; enc_os = 57.0; enc_oc = -57.0; enc_gs = 1.03; enc_gc = 1.0; enc_f = 5000.0;
                spi_wr(7'h6F, 16'hFFFF);
                mm_smin = 4095; mm_smax = 0; mm_cmin = 4095; mm_cmax = 0; mm_n = 0; mm_en = 1'b1;
                spi_wr(7'h28, 16'h1416);
                #(400_000);
                spi_wr(7'h28, 16'h1400); #(100 * clk_ns); mm_en = 1'b0;
                spi_rd(7'h5E); smin = rd_val; spi_rd(7'h5F); smax = rd_val; spi_rd(7'h6E); cmin = rd_val; spi_rd(7'h6F); cmax = rd_val;
                $display("INFO d22 capture: %0d pairs, RTL SIN %0d..%0d COS %0d..%0d, model SIN %0d..%0d COS %0d..%0d",
                         mm_n, smin, smax, cmin, cmax, mm_smin, mm_smax, mm_cmin, mm_cmax);
                check(mm_n > 300 && smin == mm_smin && smax == mm_smax && cmin == mm_cmin && cmax == mm_cmax,
                      "d22: RAW_SIN/COS_MIN/MAX equal the model min/max of the corrected codes (2 periods, exact)");
                spi_wr(7'h6F, 16'h0000); #(5 * clk_ns);
                spi_rd(7'h5E); j = (rd_val == 12'hFFF); spi_rd(7'h5F); j = j && (rd_val == 0);
                spi_rd(7'h6E); j = j && (rd_val == 12'hFFF); spi_rd(7'h6F); j = j && (rd_val == 0);
                check(j, "d22: a write to RAW_COS_MAX (0x6F) clears all four");
                // ---- 5. host calibration (R1_REGISTER_MAP.md 4.4) from the captured values
                os_i = (smax + smin + 1) / 2 - 2048; oc_i = (cmax + cmin + 1) / 2 - 2048;
                a_s = (smax - smin) / 2.0; a_c = (cmax - cmin) / 2.0; a_t = (a_s + a_c) / 2.0;
                gs_i = $rtoi(16384.0 * a_t / a_s + 0.5); gc_i = $rtoi(16384.0 * a_t / a_c + 0.5);
                $display("INFO d22 host calibration: SIN_OFS %0d COS_OFS %0d SIN_GAIN 0x%04h COS_GAIN 0x%04h (A_t %0.1f LSB)",
                         os_i, oc_i, gs_i, gc_i, a_t);
                // ---- 6. static angles: MEAS_ANGLE error before (reset words) and after the correction
                enc_f = 0.0; e0 = 0.0; e1 = 0.0;
                spi_wr(7'h28, 16'h1416);
                for (j = 0; j < 16; j = j + 1) begin
                    enc_ph0 = (j + 0.37) / 16.0; ang = enc_ph0 * 360.0;
                    #(200 * clk_ns); spi_rd(7'h1F);
                    e = rd_val / 65536.0 * 360.0 - ang; e = e - 360.0 * $floor((e + 180.0) / 360.0);
                    if (e < 0) e = -e; if (e > e0) e0 = e;
                end
                spi_wr(7'h10, os_i[15:0] & 16'h0FFF); spi_wr(7'h11, oc_i[15:0] & 16'h0FFF);
                spi_wr(7'h12, gs_i[15:0]); spi_wr(7'h3F, gc_i[15:0]);
                load_cal_crc; spi_wr(7'h04, 16'h0001);
                for (j = 0; j < 16; j = j + 1) begin
                    enc_ph0 = (j + 0.37) / 16.0; ang = enc_ph0 * 360.0;
                    #(200 * clk_ns); spi_rd(7'h1F);
                    e = rd_val / 65536.0 * 360.0 - ang; e = e - 360.0 * $floor((e + 180.0) / 360.0);
                    if (e < 0) e = -e; if (e > e1) e1 = e;
                end
                spi_rd(7'h1C);
                $display("INFO d22 MEAS_ANGLE error at 16 static angles: before %0.3f, after %0.4f deg el; AMPLITUDE %0d LSB",
                         e0, e1, rd_val);
                check(e0 > 1.0, "d22: without correction the 25 mV / 3 % head error gives > 1 deg el");
                check(e1 < 0.1, "d22: with the host correction the error is < 0.1 deg el");
                check(rd_val >= a_t - 4 && rd_val <= a_t + 4, "d22: AMPLITUDE after correction = A_t +- 4 LSB");
                spi_rd(7'h01);
                check(rd_val[4] && fault_n, "d22: CAL_VALID and no fault after the calibration words and CAL_CRC");
                enc_amp = 1400.0; enc_os = 0.0; enc_oc = 0.0; enc_gs = 1.0; enc_f = 1000.0;
            end
        end

        // =================================================================
        // Revision 0.9 test d27 (PLAN.md D27). Only ports and SPI are used, so the group also runs at gate level.
        if (test == "d27") begin
            begin : d27t
                integer j, ok, nmis, va, vb, ea, eb, r0, r1, i0, i1, t0, t1, gw, ow, smn, smx;
                real g_adc, err0, err1;
                // ---- 1. ID and reset values of the D27 words, the capture and I_A/I_B (PWM off since reset: no current pair)
                spi_rd(7'h00); check(rd_val == 16'h5209, "d27: ID reads 0x5209 (RTL revision 0.9)");
                spi_rd(7'h48); j = rd_val; spi_rd(7'h49); j = j | rd_val;
                check(j == 0, "d27: IA_OFS (0x48) and IB_OFS (0x49) reset 0");
                spi_rd(7'h4A); j = rd_val; spi_rd(7'h4B);
                check(j == 16'h4000 && rd_val == 16'h4000, "d27: IA_GAIN (0x4A) and IB_GAIN (0x4B) reset 0x4000 = 1.0");
                spi_rd(7'h4C); j = (rd_val == 12'hFFF); spi_rd(7'h4D); j = j && (rd_val == 0);
                spi_rd(7'h4E); j = j && (rd_val == 12'hFFF); spi_rd(7'h4F); j = j && (rd_val == 0);
                check(j, "d27: RAW_IA/IB_MIN/MAX (0x4C..0x4F) reset MIN 0xFFF, MAX 0x000 (no current pair)");
                spi_rd(7'h29); j = rd_val; spi_rd(7'h2A);
                check(j == 0 && rd_val == 0, "d27: I_A, I_B reset 0 (as revision 0.8)");
                // ---- 2. read/write and CRC coverage
                spi_wr(7'h48, 16'hF123); spi_rd(7'h48); j = (rd_val == 16'h0123);
                spi_wr(7'h49, 16'h0ABC); spi_rd(7'h49); j = j && (rd_val == 16'h0ABC);
                spi_wr(7'h4A, 16'h8765); spi_rd(7'h4A); j = j && (rd_val == 16'h8765);
                spi_wr(7'h4B, 16'h1234); spi_rd(7'h4B); j = j && (rd_val == 16'h1234);
                check(j, "d27: IA_OFS/IB_OFS read back 12 bits, IA_GAIN/IB_GAIN 16 bits");
                crc_v08 = 1'b1; load_cal_crc; crc_v08 = 1'b0; spi_rd(7'h01);
                check(!rd_val[4], "d27: CAL_CRC over the 44 words of 0.8 (without 0x48..0x4B) leaves CAL_VALID 0");
                load_cal_crc; spi_rd(7'h01);
                check(rd_val[4], "d27: CAL_CRC over 48 words incl. 0x48..0x4B sets CAL_VALID");
                ok = 0;
                for (j = 8'h48; j <= 8'h4B; j = j + 1) begin
                    spi_wr(j, 16'h0000); #(20 * clk_ns); spi_rd(7'h01); ok = ok + (!rd_val[4]);
                    load_cal_crc;
                end
                check(ok == 4, "d27: a write of IA_OFS, IB_OFS, IA_GAIN or IB_GAIN clears CAL_VALID (CRC-covered words)");
                spi_wr(7'h4A, 16'h4000); spi_wr(7'h4B, 16'h4000); load_cal_crc; spi_wr(7'h04, 16'h0001); #(20 * clk_ns);
                check(fault_n, "d27: CAL_CRC and CLR release the CAL fault (words back at reset)");
                // ---- 3. current frames (PWM period 300 ticks, strobe at the channel A centre); reset words: I = raw
                spi_wr(7'h20, 16'd300); spi_wr(7'h21, 16'd150); spi_wr(7'h22, 16'd150); spi_wr(7'h25, 16'd150);
                ia_code = 12'd1234; ib_code = 12'd2900; #(700 * clk_ns);
                spi_rd(7'h29); va = rd_val; spi_rd(7'h2A); vb = rd_val;
                $display("INFO d27 reset words: I_A %0d (raw %0d), I_B %0d (raw %0d)", va, adcw_code(sar14(1234)), vb, adcw_code(sar14(2900)));
                check(va == adcw_code(sar14(1234)) && vb == adcw_code(sar14(2900)), "d27: with the reset words I_A, I_B equal the raw codes");
                // ---- 4. bit-exact through the chip: 12 word sets incl. both saturation ends and the rounding half LSB
                nmis = 0;
                for (j = 0; j < 12; j = j + 1) begin
                    case (j)
                        0:  begin ia_code = 822;  ib_code = 1740; ow = 12'hFB8; gw = 16'h3C8E; end  // -72 LSB, 0.9461
                        1:  begin ia_code = 3000; ib_code = 1000; ow = 12'h064; gw = 16'h5000; end  // +100, 1.25
                        2:  begin ia_code = 4095; ib_code = 0;    ow = 12'h800; gw = 16'hFFFF; end  // saturate high / low
                        3:  begin ia_code = 0;    ib_code = 4095; ow = 12'h7FF; gw = 16'h8000; end  // saturate low / high
                        4:  begin ia_code = 2049; ib_code = 2047; ow = 12'h000; gw = 16'h2000; end  // +-0.5 LSB rounding
                        5:  begin ia_code = 2051; ib_code = 2045; ow = 12'h000; gw = 16'h2000; end  // +-1.5 LSB rounding
                        6:  begin ia_code = 1500; ib_code = 2600; ow = 12'hFFF; gw = 16'h0000; end  // gain 0: 2048
                        7:  begin ia_code = 2500; ib_code = 1600; ow = 12'h001; gw = 16'h4001; end
                        8:  begin ia_code = 3700; ib_code = 400;  ow = 12'hF38; gw = 16'h3000; end  // -200, 0.75
                        9:  begin ia_code = 1111; ib_code = 3333; ow = 12'h0C8; gw = 16'h4E35; end
                        10: begin ia_code = 2048; ib_code = 2048; ow = 12'h7FF; gw = 16'h4000; end
                        default: begin ia_code = 600; ib_code = 3500; ow = 12'h123; gw = 16'h6789; end
                    endcase
                    spi_wr(7'h48, ow[15:0]); spi_wr(7'h4A, gw[15:0]);
                    spi_wr(7'h49, (12'h000 - ow) & 12'hFFF); spi_wr(7'h4B, 16'hFFFF - gw[15:0]);
                    #(700 * clk_ns);
                    ea = icor_m(adcw_code(sar14(ia_code)), ow, gw);
                    eb = icor_m(adcw_code(sar14(ib_code)), (12'h000 - ow) & 12'hFFF, 16'hFFFF - gw);
                    spi_rd(7'h29); va = rd_val; spi_rd(7'h2A); vb = rd_val;
                    if (va != ea || vb != eb) nmis = nmis + 1;
                    $display("INFO d27 vector %0d: raw %0d / %0d, I_A %0d (model %0d), I_B %0d (model %0d)",
                             j, adcw_code(sar14(ia_code)), adcw_code(sar14(ib_code)), va, ea, vb, eb);
                end
                check(nmis == 0, "d27: I_A and I_B equal the integer model for 12 word sets (24 values, saturation and rounding)");
                // ---- 5. raw-code capture against the model (random currents, corrected words active)
                spi_wr(7'h20, 16'd0); #(400 * clk_ns);                      // current frames stopped for the clear checks
                spi_rd(7'h5E); smn = rd_val; spi_rd(7'h5F); smx = rd_val;
                spi_wr(7'h4D, 16'h0000); #(5 * clk_ns);
                spi_rd(7'h4C); j = (rd_val == 12'hFFF); spi_rd(7'h4D); j = j && (rd_val == 0);
                spi_rd(7'h4E); j = j && (rd_val == 12'hFFF); spi_rd(7'h4F); j = j && (rd_val == 0);
                spi_rd(7'h5E); va = rd_val; spi_rd(7'h5F);
                check(j && va <= smn && rd_val >= smx && va != 12'hFFF, "d27: a write to RAW_IA_MAX (0x4D) clears the four current words, not the encoder capture");
                // the constant codes of vector 11 are captured after the clear (>= 2 current pairs): the model starts with them
                spi_wr(7'h20, 16'd300); spi_wr(7'h4C, 16'h0000); #(700 * clk_ns);
                im_amin = adcw_code(sar14(ia_code)); im_amax = im_amin; im_bmin = adcw_code(sar14(ib_code)); im_bmax = im_bmin; im_n = 0;
                @(negedge adc_sel); im_en = 1'b1; im_rnd = 1'b1;            // aligned to a frame boundary
                #(24 * 300 * clk_ns);
                @(negedge adc_sel); im_rnd = 1'b0; #(2 * clk_ns); im_en = 1'b0;
                spi_wr(7'h20, 16'd0); #(400 * clk_ns);                      // stopped: no pair during the reads
                spi_rd(7'h4C); r0 = rd_val; spi_rd(7'h4D); r1 = rd_val; spi_rd(7'h4E); i0 = rd_val; spi_rd(7'h4F); i1 = rd_val;
                $display("INFO d27 capture: %0d current pairs, RTL IA %0d..%0d IB %0d..%0d, model IA %0d..%0d IB %0d..%0d",
                         im_n, r0, r1, i0, i1, im_amin, im_amax, im_bmin, im_bmax);
                check(im_n >= 20 && r0 == im_amin && r1 == im_amax && i0 == im_bmin && i1 == im_bmax,
                      "d27: RAW_IA/IB_MIN/MAX equal the model min/max of the raw current codes (exact, words not applied)");
                spi_wr(7'h5E, 16'h0000); #(5 * clk_ns); spi_rd(7'h4C);
                check(rd_val == im_amin, "d27: a write to RAW_SIN_MIN (0x5E) does not clear the current capture");
                spi_wr(7'h4E, 16'h0000); #(5 * clk_ns);
                spi_rd(7'h4C); j = (rd_val == 12'hFFF); spi_rd(7'h4D); j = j && (rd_val == 0);
                spi_rd(7'h4E); j = j && (rd_val == 12'hFFF); spi_rd(7'h4F); j = j && (rd_val == 0);
                check(j, "d27: a write to RAW_IB_MIN (0x4E) clears all four current words");
                spi_wr(7'h20, 16'd300);
                // ---- 6. host calibration of an ADC gain error 1.057 (r1_top test 3, PLAN.md D27): ideal codes 822 / 1740
                spi_wr(7'h48, 16'h0000); spi_wr(7'h49, 16'h0000); spi_wr(7'h4A, 16'h4000); spi_wr(7'h4B, 16'h4000);
                g_adc = 1.0570; t0 = 822; t1 = 1740;
                ia_code = $rtoi(2048.0 + g_adc * (t0 - 2048) + 0.5); ib_code = ia_code;     // rounded to the nearest code
                #(700 * clk_ns); spi_wr(7'h4C, 16'h0000); #(700 * clk_ns); spi_rd(7'h4C); r0 = rd_val; spi_rd(7'h4D); j = rd_val;
                check(r0 == j, "d27: constant current: RAW_IA_MIN = RAW_IA_MAX");
                ia_code = $rtoi(2048.0 + g_adc * (t1 - 2048) + 0.5); ib_code = ia_code;
                #(700 * clk_ns); spi_wr(7'h4C, 16'h0000); #(700 * clk_ns); spi_rd(7'h4C); r1 = rd_val;
                err0 = (r1 - r0) * 1.0 / (t1 - t0) - 1.0;
                // host: gain from the two levels, offset so that level 0 reads t0 (register map 0.9 section 4.7)
                gw = $rtoi(16384.0 * (t1 - t0) / (r1 - r0) + 0.5);
                ow = $rtoi(r0 - 2048.0 - (t0 - 2048.0) * 16384.0 / gw + ((r0 - 2048.0 - (t0 - 2048.0) * 16384.0 / gw) >= 0 ? 0.5 : -0.5));
                $display("INFO d27 host calibration: raw %0d / %0d, IA_GAIN 0x%04h, IA_OFS %0d", r0, r1, gw, ow);
                spi_wr(7'h48, ow[15:0] & 16'h0FFF); spi_wr(7'h4A, gw[15:0]);
                spi_wr(7'h49, ow[15:0] & 16'h0FFF); spi_wr(7'h4B, gw[15:0]);
                ia_code = $rtoi(2048.0 + g_adc * (t0 - 2048) + 0.5); ib_code = ia_code; #(700 * clk_ns); spi_rd(7'h29); i0 = rd_val;
                ia_code = $rtoi(2048.0 + g_adc * (t1 - 2048) + 0.5); ib_code = ia_code; #(700 * clk_ns); spi_rd(7'h29); i1 = rd_val;
                spi_rd(7'h2A); j = rd_val;
                err1 = (i1 - i0) * 1.0 / (t1 - t0) - 1.0;
                $display("INFO d27 current step: before %+0.3f %%, after %+0.3f %% (I_A %0d -> %0d, ideal %0d -> %0d, I_B %0d)",
                         100.0 * err0, 100.0 * err1, i0, i1, t0, t1, j);
                check(err0 > 0.05, "d27: without correction the 1.057 ADC gain gives a current step error > 5 %");
                check(err1 < 0.0025 && err1 > -0.0025 && i0 >= t0 - 1 && i0 <= t0 + 1 && j == i1,
                      "d27: after the host calibration the step error is within +-0.25 % and level 0 within 1 LSB");
                // ---- 7. I2t over-current trip on the corrected sample (I_ZERO 2048, TAU 0: E = i^2 every period, I2T_LIM 3000)
                spi_wr(7'h2F, 16'd2048); spi_wr(7'h2D, 16'h0000); spi_wr(7'h2E, 16'd3000);
                ia_code = 12'd3048; ib_code = 12'd2048;
                spi_wr(7'h48, 16'h0000); spi_wr(7'h4A, 16'h3000);           // A: 0.75, raw 3048 -> 2048 + 750 = 2798 (i 46)
                spi_wr(7'h49, 16'h0CE0); spi_wr(7'h4B, 16'h4000);           // B: offset -800 -> 2848 (i 50)
                load_cal_crc; spi_wr(7'h04, 16'h0001); #(6 * 300 * clk_ns);
                spi_wr(7'h04, 16'h0001); #(20 * clk_ns);
                spi_rd(7'h02); j = rd_val; spi_rd(7'h29); va = rd_val; spi_rd(7'h2A); vb = rd_val;
                spi_rd(7'h30); ea = rd_val; spi_rd(7'h31); eb = rd_val;
                $display("INFO d27 I2t below the limit: FAULT 0x%04h, I_A %0d, I_B %0d, I2T_A %0d, I2T_B %0d (raw A %0d alone would give %0d)",
                         j, va, vb, ea, eb, adcw_code(sar14(3048)), ((adcw_code(sar14(3048)) - 2048) >> 4) * ((adcw_code(sar14(3048)) - 2048) >> 4));
                check(j == 0 && fault_n && va == 2798 && vb == 2848 && ea == 46 * 46 && eb == 50 * 50,
                      "d27: corrected samples 2798 / 2848 below I2T_LIM 3000: no trip; I2T_A/B = i^2 of the corrected samples");
                spi_wr(7'h4A, 16'h5000);                                     // A: 1.25 -> 2048 + 1250 = 3298 (i 78)
                #(4 * 300 * clk_ns); spi_rd(7'h02); j = rd_val; spi_rd(7'h29); va = rd_val; spi_rd(7'h30); ea = rd_val;
                $display("INFO d27 I2t IA_GAIN 1.25: FAULT 0x%04h, I_A %0d, I2T_A %0d", j, va, ea);
                check(j[9] && !j[10] && !fault_n && va == 3298 && ea == 78 * 78,
                      "d27: IA_GAIN 1.25 on the same raw current trips I2T_A (corrected sample in the compare), I2T_B clear");
                spi_wr(7'h4B, 16'h5000);                                     // B: (0 + 800) x 1.25 -> 3048 (i 62)
                #(4 * 300 * clk_ns); spi_rd(7'h02); j = rd_val; spi_rd(7'h2A); vb = rd_val; spi_rd(7'h31); eb = rd_val;
                $display("INFO d27 I2t IB_GAIN 1.25 with IB_OFS -800: FAULT 0x%04h, I_B %0d, I2T_B %0d", j, vb, eb);
                check(j[10] && vb == 3048 && eb == 62 * 62, "d27: IB_OFS -800 and IB_GAIN 1.25 at zero raw current trip I2T_B");
                // restore
                ia_code = 12'd2048; ib_code = 12'd2048;
                spi_wr(7'h2E, 16'hFFFF); spi_wr(7'h48, 16'h0000); spi_wr(7'h49, 16'h0000); spi_wr(7'h4A, 16'h4000); spi_wr(7'h4B, 16'h4000);
                #(4 * 300 * clk_ns); load_cal_crc; spi_wr(7'h04, 16'h0001); #(20 * clk_ns);
                spi_rd(7'h02);
                check(rd_val == 0 && fault_n, "d27: words restored, CAL_CRC and CLR: FAULT 0");
                spi_wr(7'h20, 16'd0);
            end
        end

        #(1000);
        $display("# %0d checks, %0d failed", checks, errors);
        if (errors == 0) $display("ALL TESTS PASSED");
        else             $display("TESTS FAILED: %0d", errors);
        $finish;
    end
    // global time limit
    initial begin #(200_000_000); $display("TESTS FAILED: timeout"); $finish; end
endmodule
