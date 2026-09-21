// Digital phase/reset/clock-loss screening. No metastability MTBF claim.
`timescale 1ns/1ps
module tb_cdc_contract;
    real osc_t=100.0, serial_t=100.0;
    reg osc=0, run_clock=1, en=0, sclk=0, sdi=0;
    wire sdo, cmp_clk;
    integer rate, phase, cut, i, errors=0, checks=0;
    reg [7:0] value;
    reg [23:0] frame;
    g1_digital_top dut(.osc_clk(osc),.por_n(1'b1),.en(en),
        .sclk(sclk),.sdi(sdi),.sdo(sdo),.cmp_clk(cmp_clk),
        .cmp_soft(1'b0),.cmp_hard(1'b0),.tripped(1'b0));
    always begin #(osc_t/2); if(run_clock) osc=~osc; end
    task pulse(input bit data);
        begin
            // Explicit fixture: data arrives 2 ns after the preceding falling
            // edge; SCLK arrives 1 ns later than its nominal source edge.
            #2 sdi=data; #(serial_t/2-1) sclk=1;
            #(serial_t/2-1) sclk=0;
        end
    endtask
    task byte_out(input [7:0] b);
        integer j;
        begin for(j=7;j>=0;j=j-1)pulse(b[j]);end
    endtask
    task write_reg(input [6:0] addr,input [7:0] b);
        begin byte_out({1'b0,addr});byte_out(b); #(8*osc_t);end
    endtask
    task read_reg(input [6:0] addr,output [7:0] b);
        integer j;
        begin
            byte_out({1'b1,addr});byte_out(8'd0);
            for(j=7;j>=0;j=j-1)begin
                #(serial_t/2+1) sclk=1; #2 b[j]=sdo;
                #(serial_t/2-3) sclk=0;
            end
            #(8*osc_t);
        end
    endtask
    task reset;
        begin en=0;sclk=0;sdi=0;run_clock=1;#(5*osc_t);en=1;#(130*osc_t);end
    endtask
    task expect_byte(input [7:0] got,input [7:0] wanted);
        begin
            checks=checks+1;
            if(got!==wanted)begin
                errors=errors+1;
                if(errors<30)$display("FAIL rate=%0d phase=%0d cut=%0d got=%h wanted=%h",rate,phase,cut,got,wanted);
            end
        end
    endtask
    initial begin
        for(rate=0;rate<3;rate=rate+1)begin
            osc_t=(rate==0)?125.0:(rate==1)?100.0:83.333333;
            serial_t=osc_t;
            for(phase=0;phase<16;phase=phase+1)begin
                reset;#(osc_t*phase/16.0);
                write_reg(7'h03,8'hA5);read_reg(7'h03,value);expect_byte(value,8'hA5);
                write_reg(7'h03,8'h5A);read_reg(7'h03,value);expect_byte(value,8'h5A);
                read_reg(7'h00,value);expect_byte(value,8'h47);
            end
            // Async EN reset after every partial read-frame position.
            for(cut=0;cut<24;cut=cut+1)begin
                reset;frame=24'h830000;
                for(i=23;i>23-cut;i=i-1)pulse(frame[i]);
                #7 en=0;#(5*osc_t);sclk=0;sdi=0;en=1;#(130*osc_t);
                read_reg(7'h03,value);expect_byte(value,8'hFE);
                write_reg(7'h03,8'hC8);read_reg(7'h03,value);expect_byte(value,8'hC8);
            end
            // A stopped core cannot consume writes. EN reset must recover
            // framing and defaults even if a complete write was sent while stopped.
            reset;write_reg(7'h03,8'hA5);
            @(negedge osc);run_clock=0;
            write_reg(7'h03,8'h5A);#(10*osc_t);
            expect_byte(dut.dac_hard_code,8'hA5);
            en=0;#(5*osc_t);run_clock=1;#(5*osc_t);en=1;#(130*osc_t);
            read_reg(7'h03,value);expect_byte(value,8'hFE);
        end
        $display("CDC_CONTRACT checks=%0d errors=%0d; 8/10/12MHz,16 phases,24 reset positions per frequency",checks,errors);
        if(errors)$fatal(1,"CDC screening failed");
        $display("ALL TESTS PASSED");$finish;
    end
    initial begin #100000000;$fatal(1,"testbench timeout");end
endmodule
