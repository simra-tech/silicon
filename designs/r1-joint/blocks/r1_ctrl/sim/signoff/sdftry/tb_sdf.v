`timescale 1ns/1ps
module tb_sdf;
  reg clk=0, por_n=0, cs_n=1, ma=1, sdi=0, en_pad=1, t2f=0; reg [3:0] cmp=0;
  reg av_a=0, av_b=0; reg [13:0] ra=0, rb=0;
  wire slo_sdo, fault_n, gate_a, gate_b, gate_c, adc_hold, is_smp, adc_start, adc_sel, az_win;
  wire [4:0] osc_trim; wire [15:0] ana_ctrl; wire [5:0] a,b,c,d,e,f,g,h;
  r1_ctrl_top dut(.clk(clk),.por_n(por_n),.cs_n(cs_n),.ma_sclk(ma),.sdi(sdi),.slo_sdo(slo_sdo),.en_pad(en_pad),.fault_n(fault_n),
   .gate_a(gate_a),.gate_b(gate_b),.gate_c(gate_c),.adc_hold(adc_hold),.is_smp(is_smp),.adc_start(adc_start),.adc_sel(adc_sel),
   .adc_valid_a(av_a),.adc_raw_a(ra),.adc_valid_b(av_b),.adc_raw_b(rb),.cmp(cmp),.thr_oc_a(a),.thr_neg_a(b),.thr_oc_b(c),.thr_neg_b(d),
   .cal_oc_a(e),.cal_neg_a(f),.cal_oc_b(g),.cal_neg_b(h),.az_win(az_win),.t2f_clk(t2f),.osc_trim(osc_trim),.ana_ctrl(ana_ctrl));
  reg [2047:0] sdf_file;
  initial begin
    if ($value$plusargs("sdf=%s", sdf_file)) begin
      $sdf_annotate(sdf_file, tb_sdf.dut, , "sdf_annotate.log", "MAXIMUM");
      $display("annotated");
    end
    #10 $finish;
  end
endmodule
