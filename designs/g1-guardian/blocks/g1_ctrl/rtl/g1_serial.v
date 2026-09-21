// G1_CTRL: three-wire serial slave (SPI mode 0, no chip select).
// Protocol: designs/g1-guardian/specification/G1_REGISTER_MAP.md, section 1.
//
// Derived from ChipDesign-BV/spi-slave-ihp spi_slave.v
// (https://github.com/ChipDesign-BV/spi-slave-ihp, commit
// 7eb03a4bdd7b9409f290261f301f80747fe8d437, Apache-2.0, Koen Van Caekenberghe):
// the command-byte convention (bit 7 = R/nW, bits 6:0 = address), the mode-0
// edge usage (SDI on rising, SDO on falling SCLK) and the two-flop
// synchroniser discipline are taken from it. The original oversamples SCLK in
// the system clock; this version clocks the shift logic on SCLK itself and
// hands off to osc_clk with toggle synchronisers, adds the 24-clock read frame
// (turnaround byte) and the idle-timeout frame reset that replaces SSEL.
// SPDX-License-Identifier: Apache-2.0

module g1_serial (
    // osc_clk domain
    input  wire       osc_clk,
    input  wire       rst_n,        // async assert, released synchronously to osc_clk
    output reg        wr_en,        // one-cycle pulse; wr_addr/wr_data valid
    output wire [6:0] wr_addr,
    output wire [7:0] wr_data,
    output reg        rd_en,        // one-cycle pulse; rd_addr valid, rd_data captured this cycle
    output wire [6:0] rd_addr,
    input  wire [7:0] rd_data,      // combinational read mux from the register file
    // pads
    input  wire       sclk,
    input  wire       sdi,
    output wire       sdo
);

    // ------------------------------------------------------------------
    // osc_clk domain: idle-timeout frame reset
    // ------------------------------------------------------------------
    wire sclk_s;
    g1_sync2 u_sync_sclk (.clk(osc_clk), .rst_n(rst_n), .d(sclk), .q(sclk_s));

    reg [6:0] idle_cnt;      // saturating count of osc_clk cycles with SCLK low
    reg       frame_rst;     // registered: glitch-free asynchronous clear for the bit counter
    always @(posedge osc_clk or negedge rst_n) begin
        if (!rst_n) begin
            idle_cnt  <= 7'd0;
            frame_rst <= 1'b0;
        end else begin
            if (sclk_s)
                idle_cnt <= 7'd0;
            else if (idle_cnt != 7'd127)
                idle_cnt <= idle_cnt + 7'd1;
            // asserted for idle counts 64..79 (16 cycles), then released while SCLK is still idle
            frame_rst <= (idle_cnt >= 7'd63) && (idle_cnt < 7'd79);
        end
    end

    // ------------------------------------------------------------------
    // SCLK domain, rising edge: bit counter, input shift, command latch
    // ------------------------------------------------------------------
    wire sclk_rst_n = rst_n & ~frame_rst;

    reg [4:0] bit_cnt;       // rising edges seen in this frame (0..23), wraps at 16 (write) or 24 (read)
    reg       rd_frame;      // set at edge 8 when the command is a read
    reg [6:0] shreg;         // last seven SDI bits; with the current SDI they form a byte
    always @(posedge sclk or negedge sclk_rst_n) begin
        if (!sclk_rst_n) begin
            bit_cnt  <= 5'd0;
            rd_frame <= 1'b0;
        end else begin
            if (bit_cnt == 5'd7) begin
                rd_frame <= shreg[6];                 // R/nW bit of the command byte
                bit_cnt  <= 5'd8;
            end else if (bit_cnt == 5'd15 && !rd_frame) begin
                bit_cnt  <= 5'd0;                     // write frame complete
            end else if (bit_cnt == 5'd23) begin
                bit_cnt  <= 5'd0;                     // read frame complete
                rd_frame <= 1'b0;
            end else begin
                bit_cnt  <= bit_cnt + 5'd1;
            end
        end
    end

    // Holding registers and toggles are NOT touched by the frame reset: a
    // reset of a toggle would look like a transaction to the osc_clk side.
    reg [6:0] cmd_addr;
    reg [6:0] wr_addr_r, rd_addr_r;
    reg [7:0] wr_data_r;
    reg       wr_tog, rd_tog;
    always @(posedge sclk or negedge rst_n) begin
        if (!rst_n) begin
            shreg     <= 7'd0;
            cmd_addr  <= 7'd0;
            wr_addr_r <= 7'd0;
            rd_addr_r <= 7'd0;
            wr_data_r <= 8'h00;
            wr_tog    <= 1'b0;
            rd_tog    <= 1'b0;
        end else begin
            shreg <= {shreg[5:0], sdi};
            if (bit_cnt == 5'd7) begin
                cmd_addr <= {shreg[5:0], sdi};
                if (shreg[6]) begin                   // read: hand the address over now
                    rd_addr_r <= {shreg[5:0], sdi};
                    rd_tog    <= ~rd_tog;
                end
            end
            if (bit_cnt == 5'd15 && !rd_frame) begin  // write: hand address and data over
                wr_addr_r <= cmd_addr;
                wr_data_r <= {shreg[6:0], sdi};
                wr_tog    <= ~wr_tog;
            end
        end
    end

    // ------------------------------------------------------------------
    // osc_clk domain: toggle synchronisers, register access pulses, read hold
    // ------------------------------------------------------------------
    wire wr_tog_s, rd_tog_s;
    g1_sync2 u_sync_wr (.clk(osc_clk), .rst_n(rst_n), .d(wr_tog), .q(wr_tog_s));
    g1_sync2 u_sync_rd (.clk(osc_clk), .rst_n(rst_n), .d(rd_tog), .q(rd_tog_s));

    reg       wr_tog_d, rd_tog_d;
    reg [7:0] rd_hold;       // quasi-static by the time the SCLK domain reads it
    always @(posedge osc_clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_tog_d <= 1'b0;
            rd_tog_d <= 1'b0;
            wr_en    <= 1'b0;
            rd_en    <= 1'b0;
            rd_hold  <= 8'h00;
        end else begin
            wr_tog_d <= wr_tog_s;
            rd_tog_d <= rd_tog_s;
            wr_en    <= wr_tog_s ^ wr_tog_d;
            rd_en    <= rd_tog_s ^ rd_tog_d;
            if (rd_en)
                rd_hold <= rd_data;
        end
    end

    // Address/data holding registers are written in the SCLK domain at least
    // 16 SCLK periods before they can change again; the osc_clk side samples
    // them 3 cycles after the toggle (see register map, section 1.3).
    assign wr_addr = wr_addr_r;
    assign wr_data = wr_data_r;
    assign rd_addr = rd_addr_r;

    // ------------------------------------------------------------------
    // SCLK domain, falling edge: output shift register and SDO
    // ------------------------------------------------------------------
    reg [6:0] tx;
    reg       sdo_r;
    always @(negedge sclk or negedge rst_n) begin
        if (!rst_n) begin
            tx    <= 7'd0;
            sdo_r <= 1'b0;
        end else if (rd_frame && bit_cnt == 5'd16) begin
            sdo_r <= rd_hold[7];                      // first data bit, after rising edge 16
            tx    <= rd_hold[6:0];
        end else if (rd_frame && bit_cnt > 5'd16) begin
            sdo_r <= tx[6];
            tx    <= {tx[5:0], 1'b0};
        end else begin
            sdo_r <= 1'b0;
        end
    end
    assign sdo = sdo_r;

endmodule
