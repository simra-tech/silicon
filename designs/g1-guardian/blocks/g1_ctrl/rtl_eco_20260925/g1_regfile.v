// G1_CTRL: register file and address decode.
// Map: designs/g1-guardian/specification/G1_REGISTER_MAP.md, section 4.
// All registers live in the osc_clk domain; wr_en/rd_en are one-cycle pulses
// from g1_serial. Reading the low byte of a 16-bit value copies the high byte
// into hi_hold so that the L/H pair is consistent.
// ECO 2026-09-25 (blocks/g1_ctrl/ECO_20260925.md): osc_en is a constant 1 and
// OSC_CTRL bit 4 writes are ignored (change 1); SOFT_TIME_H writes go to a
// shadow that is committed together with the SOFT_TIME_L write (change 3);
// reset values INRUSH = 0x02 and MODE = 0x23, i.e. FAST_EN = 1 (change 5);
// VERSION = 0x12.
// SPDX-License-Identifier: Apache-2.0

module g1_regfile (
    input  wire        clk,
    input  wire        rst_n,
    // serial port (osc_clk domain)
    input  wire        wr_en,
    input  wire [6:0]  wr_addr,
    input  wire [7:0]  wr_data,
    input  wire        rd_en,
    input  wire [6:0]  rd_addr,
    output reg  [7:0]  rd_data,
    // trip configuration
    output reg  [7:0]  dac_soft_code,
    output reg  [7:0]  dac_hard_code,
    output wire [15:0] soft_time,
    output wire [1:0]  decay,
    output wire        hyst_en,
    output wire        hyst_2,
    output reg  [7:0]  hard_n,
    output reg  [7:0]  inrush,
    output reg  [7:0]  hold_time,
    output reg  [7:0]  retry_max,
    output wire        soft_en,
    output wire        hard_en,
    output wire        retrig,
    output wire        trip_set_sel,
    output wire        force_trip,
    output wire        fast_en,       // MODE[5]: analog fast path cmp_hard -> G1_GATE latch
    output reg  [7:0]  sense_ofs,     // signed sense offset trim added to both DAC codes
    // trip commands (one-cycle pulses)
    output wire        clear,
    output wire        clr_trip_cnt,
    output wire        clr_peak,
    // trip status
    input  wire        trip,
    input  wire [1:0]  trip_cause,
    input  wire        inrush_active,
    input  wire        holding,
    input  wire        gave_up,
    input  wire        soft_armed,
    input  wire        cmp_soft_s,
    input  wire        cmp_hard_s,
    input  wire        gate_en,
    input  wire        tripped_a_s,   // synchronised G1_GATE latch state
    input  wire [7:0]  dac_soft_eff,  // effective DAC codes driven to G1_TRIP (readback)
    input  wire [7:0]  dac_hard_eff,
    input  wire [7:0]  retry_cnt,
    input  wire [15:0] trip_cnt,
    input  wire [15:0] soft_peak,
    // SEU configuration and commands
    output wire        scrub_en,
    output wire [1:0]  pattern,
    output wire        seu_clr_cnt,
    output wire        seu_inj_plain,
    output wire        seu_inj_tmr,
    // SEU telemetry
    input  wire [15:0] seu_cnt_plain,
    input  wire [15:0] seu_cnt_corr,
    input  wire [7:0]  seu_cnt_unc,
    input  wire [7:0]  seu_run_max,
    input  wire        seu_active,
    input  wire        seu_filling,
    // oscillator control and test output
    output wire        osc_en,
    output wire [3:0]  osc_trim,
    output wire        clk_div_out,
    // sensor / bandgap control bits (to the 3.3 V domain through g1_ls_up)
    output wire        t2f_en,
    output wire        t2f_mode,
    output wire        bgr_r4
);

    // ---------------- addresses ----------------
    localparam [6:0] A_CHIP_ID     = 7'h00, A_VERSION     = 7'h01,
                     A_DAC_SOFT    = 7'h02, A_DAC_HARD    = 7'h03,
                     A_SOFT_TIME_L = 7'h04, A_SOFT_TIME_H = 7'h05,
                     A_SOFT_CFG    = 7'h06, A_HARD_N      = 7'h07,
                     A_INRUSH      = 7'h08, A_HOLD_TIME   = 7'h09,
                     A_RETRY_MAX   = 7'h0A, A_MODE        = 7'h0B,
                     A_CTRL        = 7'h0C, A_STATUS      = 7'h0D,
                     A_STATUS2     = 7'h0E, A_TRIP_CNT_L  = 7'h0F,
                     A_TRIP_CNT_H  = 7'h10, A_SOFT_PEAK_L = 7'h11,
                     A_SOFT_PEAK_H = 7'h12,
                     A_SEU_CTRL    = 7'h18, A_SEU_CMD     = 7'h19,
                     A_SEU_STATUS  = 7'h1A, A_SEU_PLAIN_L = 7'h1B,
                     A_SEU_PLAIN_H = 7'h1C, A_SEU_CORR_L  = 7'h1D,
                     A_SEU_CORR_H  = 7'h1E, A_SEU_UNC     = 7'h1F,
                     A_SEU_RUN     = 7'h20,
                     A_OSC_CNT_L   = 7'h24, A_OSC_CNT_H   = 7'h25,
                     A_OSC_DIV     = 7'h26,
                     // appended in map version 1.1 (2026-09-19)
                     A_SENSE_OFS   = 7'h27, A_OSC_CTRL    = 7'h28,
                     A_TEMP_CTRL   = 7'h29, A_DAC_SOFT_EFF = 7'h2A,
                     A_DAC_HARD_EFF = 7'h2B;

    localparam [7:0] CHIP_ID = 8'h47, VERSION = 8'h12;   // map 1.2 (ECO 2026-09-25)

    // ---------------- read/write registers ----------------
    reg [7:0] soft_time_l, soft_time_h;
    reg [7:0] soft_time_h_sh;   // staged SOFT_TIME_H, committed by the SOFT_TIME_L write
    reg [3:0] soft_cfg;
    reg [5:0] mode;
    reg [2:0] seu_ctrl;
    reg [2:0] osc_div;
    reg [3:0] osc_ctrl;         // OSC_TRIM only; OSC_EN is not a register any more
    reg [2:0] temp_ctrl;

    assign soft_time    = {soft_time_h, soft_time_l};
    assign decay        = soft_cfg[1:0];
    assign hyst_en      = soft_cfg[2];
    assign hyst_2       = soft_cfg[3];
    assign soft_en      = mode[0];
    assign hard_en      = mode[1];
    assign retrig       = mode[2];
    assign trip_set_sel = mode[3];
    assign force_trip   = mode[4];
    assign fast_en      = mode[5];
    assign osc_trim     = osc_ctrl[3:0];
    assign osc_en       = 1'b1;           // the oscillator cannot be stopped from the core
    assign t2f_en       = temp_ctrl[0];
    assign t2f_mode     = temp_ctrl[1];
    assign bgr_r4       = temp_ctrl[2];
    assign scrub_en     = seu_ctrl[0];
    assign pattern      = seu_ctrl[2:1];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // reset codes from blocks/g1_trip/INTERFACE.md: 153 = 30.0 mV (1.2 x 25 mV
            // nominal), 254 = 49.8 mV shunt-referred
            dac_soft_code <= 8'h99;
            dac_hard_code <= 8'hFE;
            soft_time_l   <= 8'h27;
            soft_time_h   <= 8'h00;
            soft_time_h_sh <= 8'h00;
            soft_cfg      <= 4'h0;
            hard_n        <= 8'h04;
            inrush        <= 8'h02;   // 1024 cycles, ~0.1 ms (was 0x14)
            hold_time     <= 8'h0C;
            retry_max     <= 8'h03;
            mode          <= 6'h23;   // SOFT_EN, HARD_EN, FAST_EN (was 0x03)
            seu_ctrl      <= 3'h1;
            osc_div       <= 3'h0;
            sense_ofs     <= 8'h00;
            osc_ctrl      <= 4'h8;    // OSC_TRIM = 8 (mid code)
            temp_ctrl     <= 3'h1;    // T2F_EN = 1, T2F_MODE = 0 (PTAT), BGR_R4 = 0
        end else if (wr_en) begin
            case (wr_addr)
                A_DAC_SOFT:    dac_soft_code <= wr_data;
                A_DAC_HARD:    dac_hard_code <= wr_data;
                A_SOFT_TIME_L: begin            // both bytes take effect on this edge
                                   soft_time_l <= wr_data;
                                   soft_time_h <= soft_time_h_sh;
                               end
                A_SOFT_TIME_H: soft_time_h_sh <= wr_data;
                A_SOFT_CFG:    soft_cfg      <= wr_data[3:0];
                A_HARD_N:      hard_n        <= wr_data;
                A_INRUSH:      inrush        <= wr_data;
                A_HOLD_TIME:   hold_time     <= wr_data;
                A_RETRY_MAX:   retry_max     <= wr_data;
                A_MODE:        mode          <= wr_data[5:0];
                A_SEU_CTRL:    seu_ctrl      <= wr_data[2:0];
                A_OSC_DIV:     osc_div       <= wr_data[2:0];
                A_SENSE_OFS:   sense_ofs     <= wr_data;
                A_OSC_CTRL:    osc_ctrl      <= wr_data[3:0];   // bit 4 (OSC_EN) ignored
                A_TEMP_CTRL:   temp_ctrl     <= wr_data[2:0];
                default: ;
            endcase
        end
    end

    // ---------------- self-clearing command bits ----------------
    wire wr_ctrl    = wr_en && (wr_addr == A_CTRL);
    wire wr_seu_cmd = wr_en && (wr_addr == A_SEU_CMD);
    assign clear         = wr_ctrl    & wr_data[0];
    assign clr_trip_cnt  = wr_ctrl    & wr_data[1];
    assign clr_peak      = wr_ctrl    & wr_data[2];
    wire   clr_osc_cnt   = wr_ctrl    & wr_data[3];
    assign seu_clr_cnt   = wr_seu_cmd & wr_data[0];
    assign seu_inj_plain = wr_seu_cmd & wr_data[1];
    assign seu_inj_tmr   = wr_seu_cmd & wr_data[2];

    // ---------------- oscillator counter ----------------
    reg  [14:0] osc_pre;
    reg  [15:0] osc_cnt;
    wire [14:0] pre_mask = (15'd1 << (osc_div + 4'd8)) - 15'd1;
    wire        osc_tick = ((osc_pre & pre_mask) == pre_mask);
    assign clk_div_out = osc_pre[osc_div + 4'd8];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            osc_pre <= 15'd0;
            osc_cnt <= 16'd0;
        end else begin
            osc_pre <= osc_pre + 15'd1;
            if (clr_osc_cnt)
                osc_cnt <= 16'd0;
            else if (osc_tick)
                osc_cnt <= osc_cnt + 16'd1;
        end
    end

    // ---------------- read mux and L/H hold ----------------
    wire [7:0] status  = {1'b1, soft_armed, gave_up, holding, inrush_active, trip_cause, trip};
    wire [7:0] status2 = {(retry_cnt > 8'd15) ? 4'hF : retry_cnt[3:0], tripped_a_s, gate_en, cmp_hard_s, cmp_soft_s};
    wire [7:0] seu_status = {6'h00, seu_filling, seu_active};

    reg [7:0] hi_hold;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            hi_hold <= 8'h00;
        end else if (rd_en) begin
            case (rd_addr)
                A_TRIP_CNT_L:  hi_hold <= trip_cnt[15:8];
                A_SOFT_PEAK_L: hi_hold <= soft_peak[15:8];
                A_SEU_PLAIN_L: hi_hold <= seu_cnt_plain[15:8];
                A_SEU_CORR_L:  hi_hold <= seu_cnt_corr[15:8];
                A_OSC_CNT_L:   hi_hold <= osc_cnt[15:8];
                default: ;
            endcase
        end
    end

    always @* begin
        case (rd_addr)
            A_CHIP_ID:     rd_data = CHIP_ID;
            A_VERSION:     rd_data = VERSION;
            A_DAC_SOFT:    rd_data = dac_soft_code;
            A_DAC_HARD:    rd_data = dac_hard_code;
            A_SOFT_TIME_L: rd_data = soft_time_l;
            A_SOFT_TIME_H: rd_data = soft_time_h;
            A_SOFT_CFG:    rd_data = {4'h0, soft_cfg};
            A_HARD_N:      rd_data = hard_n;
            A_INRUSH:      rd_data = inrush;
            A_HOLD_TIME:   rd_data = hold_time;
            A_RETRY_MAX:   rd_data = retry_max;
            A_MODE:        rd_data = {2'b00, mode};
            A_CTRL:        rd_data = 8'h00;
            A_STATUS:      rd_data = status;
            A_STATUS2:     rd_data = status2;
            A_TRIP_CNT_L:  rd_data = trip_cnt[7:0];
            A_TRIP_CNT_H:  rd_data = hi_hold;
            A_SOFT_PEAK_L: rd_data = soft_peak[7:0];
            A_SOFT_PEAK_H: rd_data = hi_hold;
            A_SEU_CTRL:    rd_data = {5'b00000, seu_ctrl};
            A_SEU_CMD:     rd_data = 8'h00;
            A_SEU_STATUS:  rd_data = seu_status;
            A_SEU_PLAIN_L: rd_data = seu_cnt_plain[7:0];
            A_SEU_PLAIN_H: rd_data = hi_hold;
            A_SEU_CORR_L:  rd_data = seu_cnt_corr[7:0];
            A_SEU_CORR_H:  rd_data = hi_hold;
            A_SEU_UNC:     rd_data = seu_cnt_unc;
            A_SEU_RUN:     rd_data = seu_run_max;
            A_OSC_CNT_L:   rd_data = osc_cnt[7:0];
            A_OSC_CNT_H:   rd_data = hi_hold;
            A_OSC_DIV:     rd_data = {5'b00000, osc_div};
            A_SENSE_OFS:   rd_data = sense_ofs;
            A_OSC_CTRL:    rd_data = {3'b000, 1'b1, osc_ctrl};   // OSC_EN reads 1
            A_TEMP_CTRL:   rd_data = {5'b00000, temp_ctrl};
            A_DAC_SOFT_EFF: rd_data = dac_soft_eff;
            A_DAC_HARD_EFF: rd_data = dac_hard_eff;
            default:       rd_data = 8'h00;
        endcase
    end

endmodule
