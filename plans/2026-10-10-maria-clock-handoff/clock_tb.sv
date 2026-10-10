// Own testbench: observe the qualified reference's CPU phase strobes.
module clock_tb;
 reg clk_sys=0, reset=1, ce=1, enabled=0, rw=0, pal=0;
 reg [15:0] ab=16'h003c;
 reg [7:0] data=8'h60;
 wire phi1,phi2,mclk0,mclk1,halt_n,drive;
 integer t,mode,phase_count,current_slow,phase_offset,slow_address;
 maria dut(.AB_in(ab),.AB_out(),.d_in(8'h00),.write_DB_in(data),.DB_out(),
 .reset(reset),.clk_sys(clk_sys),.ce(ce),.mclk0(mclk0),.mclk1(mclk1),.pclk0(phi2),.pclk1(phi1),.pclk2(phi2),
 .RW(rw),.maria_en(enabled),.YC(),.vblank(),.NMI_n(),.halt_n(halt_n),.ready(),
 .drive_AB(drive),.hide_border(1'b0),.bypass_bios(1'b0),.PAL(pal));
 initial begin
  dut.dma_inst.LONGHDR=0;dut.dma_inst.IND=0;dut.dma_inst.sel5_cnt=0;
  dut.old_men=0;dut.men_count=0;dut.pclk=0;
  // Reference omits reset for this inhibit, normally cleared at DMA release.
  // This bench deliberately has no DMA, so start with slow accesses enabled.
  dut.dma_inst.noslow=0;
  if($test$plusargs("unknown_clocks"))force dut.sel_slow_clock=1'bx;
  if($test$plusargs("force_fast"))force dut.sel_slow_clock=1'b0;
  mode=0;phase_offset=0;phase_count=0;current_slow=0;
  slow_address='h0280;
  if($value$plusargs("mode=%d",mode))begin end
  if($value$plusargs("offset=%d",phase_offset))begin end
  if($value$plusargs("address=%h",slow_address))begin end
  if($test$plusargs("pal"))pal=1;
  for(t=0;t<1024;t=t+1)begin
   reset=t<32;enabled=t>=32;
   if(t>=256)begin
    rw=1;
    case(mode)
     0: current_slow=0;
     1: current_slow=1;
     2: current_slow=(t>=512+phase_offset);
     3: current_slow=(t<512+phase_offset);
     4: current_slow=(phase_count/3)%2;
    endcase
    ab=current_slow ? slow_address[15:0] : 16'h8000;
   end
   #5;
   if(t>=256)begin
    if(halt_n!==1'b1 || drive!==1'b0)$fatal(1,"unexpected DMA");
    if(phi1===1'bx || phi2===1'bx)$fatal(1,"unknown CPU phase");
    if(dut.sel_slow_clock===1'bx || dut.slow_clk_latch===1'bx)$fatal(1,"unknown clock selection");
    if(phi1 || phi2)
     $display("PHASE tick=%0d phase=%0d address=%h slow=%b latched=%b",t,phi2?2:1,ab,dut.sel_slow_clock,dut.slow_clk_latch);
    if(phi1)phase_count=phase_count+1;
   end
   clk_sys=1;#5;clk_sys=0;
  end
  if(phase_count<60)$fatal(1,"missing clock edges");
  $display("CLOCK_RESULT mode=%0d offset=%0d cycles=%0d",mode,phase_offset,phase_count);
  $finish;
 end
endmodule
