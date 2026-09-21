// Exhaustive RTL threshold arithmetic and interior calibration model check.
// The calibration plant below is synthetic, not a transistor mismatch model.
`timescale 1ns/1ps
module tb_trim_contract;
    reg clk=0, rst_n=0;
    always #5 clk=~clk;
    reg [7:0] nominal=0, ofs=0;
    reg hyst_en=0, hyst_2=0;
    wire [7:0] soft_out, hard_out;
    integer c, o, h, expected, base, checks=0, errors=0;
    integer offset, crossing, correction, ideal, threshold;
    g1_trip_timer dut (
        .clk(clk), .rst_n(rst_n), .cmp_clk(1'b0),
        .cmp_soft(1'b0), .cmp_hard(1'b0), .tripped_a(1'b0),
        .soft_en(1'b0), .hard_en(1'b0), .retrig(1'b0), .force_trip(1'b0),
        .soft_time(16'd0), .decay(2'd0), .hyst_en(hyst_en), .hyst_2(hyst_2),
        .hard_n(8'd4), .inrush(8'd0), .hold_time(8'd1), .retry_max(8'd0),
        .dac_soft_code(nominal), .dac_hard_code(nominal), .sense_ofs(ofs),
        .clear(1'b0), .clr_trip_cnt(1'b0), .clr_peak(1'b0),
        .dac_soft_out(soft_out), .dac_hard_out(hard_out));
    function integer saturate(input integer x);
        saturate = x < 0 ? 0 : x > 255 ? 255 : x;
    endfunction
    task check(input integer got, input integer want);
        begin
            checks=checks+1;
            if (got !== want) begin
                errors=errors+1;
                if (errors<10) $display("FAIL c=%0d ofs=%0d hyst=%0d got=%0d want=%0d",c,o,h,got,want);
            end
        end
    endtask
    initial begin
        #1; rst_n=1;
        // Charged accumulator is a controlled test fixture for hysteresis.
        force dut.soft_cnt=24'd1;
        for (h=0; h<3; h=h+1) begin
            hyst_en=(h!=0); hyst_2=(h==2);
            for (c=0; c<256; c=c+1) begin
                nominal=c;
                for (o=-128; o<128; o=o+1) begin
                    ofs=o; #1;
                    check(hard_out,saturate(c+o));
                    base=c-h; if (base<0) base=0;
                    check(soft_out,saturate(base+o));
                end
            end
        end
        release dut.soft_cnt;
        hyst_en=0;
        nominal=254; ofs=20; #1;
        check(hard_out,255);
        $display("HEADROOM nominal=254 correction=20 effective=%0d lost_codes=19",hard_out);
        nominal=235; #1; check(hard_out,255);
        $display("HEADROOM nominal=235 correction=20 effective=%0d lost_codes=0",hard_out);
        // Known-current input is ideal code 128, with independent signed offset.
        // Plant decision: above = (input_code + offset > effective_DAC).
        // Sweeping the DAC crosses at ideal + offset, so correction is POSITIVE
        // crossing minus ideal. This only tests policy arithmetic.
        for(offset=-100; offset<=100; offset=offset+1) begin
            ideal=128; crossing=0;
            while(crossing < ideal+offset) crossing=crossing+1;
            correction=crossing-ideal;
            nominal=ideal; ofs=correction; #1;
            threshold=hard_out-offset;
            check(threshold,ideal);
        end
        $display("CALIBRATION synthetic interior sign/range checks=201; analog qualification NOT RUN");
        $display("TRIM_CONTRACT checks=%0d errors=%0d",checks,errors);
        if(errors) $fatal(1,"trim contract failed");
        $display("ALL TESTS PASSED"); $finish;
    end
endmodule
