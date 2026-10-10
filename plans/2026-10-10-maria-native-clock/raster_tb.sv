module raster_tb;
 reg clk_sys=0, reset=1, ce=0, enabled=0, rw=1, pal=0;
 reg [15:0] cpu_ab=16'h8000;
 reg [7:0] cpu_data=0;
 wire [15:0] dma_ab;
 wire [7:0] data_out,yc;
 wire phi1,phi2,mclk0,mclk1,halt_n,nmi_n,drive,ready,vblank;
 reg [7:0] memory[0:65535];
 wire [15:0] ab=drive ? dma_ab : cpu_ab;
 wire [7:0] data_in=memory[ab];
 integer t,i,sub,edges,starts,releases,last_release,last_assert,last_line_tick,last_row,last_col;
 integer height,flag,slow,expected,measured_lines,completed_pulses;
 reg last_halt=1,last_nmi=1;
 maria dut(.AB_in(ab),.AB_out(dma_ab),.d_in(data_in),.write_DB_in(cpu_data),.DB_out(data_out),
 .reset(reset),.clk_sys(clk_sys),.ce(ce),.mclk0(mclk0),.mclk1(mclk1),.pclk0(phi2),.pclk1(phi1),.pclk2(phi2),
 .RW(rw),.maria_en(enabled),.YC(yc),.vblank(vblank),.NMI_n(nmi_n),.halt_n(halt_n),.ready(ready),
 .drive_AB(drive),.hide_border(1'b0),.bypass_bios(1'b0),.PAL(pal));
 initial begin
   dut.dma_inst.LONGHDR=0; dut.dma_inst.IND=0; dut.dma_inst.sel5_cnt=0;
   // Clock-generator registers also omitted from the reference's reset.
   dut.old_men=0; dut.men_count=0; dut.pclk=0;
   if (!$value$plusargs("height=%d",height)) height=2;
   if (!$value$plusargs("flag=%d",flag)) flag=2;
   if (!$value$plusargs("slow=%d",slow)) slow=0;
   if ($test$plusargs("pal")) pal=1;
   expected=flag==0 ? 0 : (flag==1 ? 1+23/height : 1);
   measured_lines=0; completed_pulses=0;
   if ($test$plusargs("suppress_nmi")) force dut.NMI_ung_n=1;
   edges=0;starts=0;releases=0;last_release=-1;last_assert=-1;last_line_tick=-1;last_row=-1;last_col=-1;
   for(i=0;i<65536;i=i+1)memory[i]=0;
   for(i=0;i<256;i=i+1)begin
     memory['h1800+3*i]=((flag==1 || (flag==2 && i==1))?'h80:0)|(height-1);
     memory['h1801+3*i]='h1c;memory['h1802+3*i]=0;
   end
   for(t=0;t<908*40;t=t+1)begin
     reset=t<32;enabled=t>=32;
     // Hold each setup write through several CPU phases in vertical blank.
     rw=0;
     if(t<80)begin cpu_ab='h003c;cpu_data='h60;end
     else if(t<128)begin cpu_ab='h002c;cpu_data='h18;end
     else if(t<176)begin cpu_ab='h0030;cpu_data='h00;end
     else if(t<224)begin cpu_ab='h003c;cpu_data='h40;end
     else begin rw=1;cpu_ab=slow ? 16'h0280 : 16'h8000;end
     if(t==256) $display("SETUP t=%0d ctrl=%h zp=%h row=%0d col=%0d mclk=%b%b phi=%b%b pclk=%b men=%h old=%b div=%d toggle=%b",t,dut.ctrl,dut.ZP,dut.sync_inst.row,dut.sync_inst.col,mclk0,mclk1,phi1,phi2,dut.pclk,dut.men_count,dut.old_men,dut.clock_div,dut.pclk_toggle);
     for(sub=0;sub<1;sub=sub+1)begin
       ce=1;
       #5 clk_sys=1;#1;
       if(t>256 && (halt_n===1'bx || nmi_n===1'bx || drive===1'bx))$fatal(1,"unknown bus control");
       if(t>256 && halt_n!==last_halt)begin
         $display("HALT tick=%0d sub=%0d row=%0d col=%0d level=%b ab=%h",t,sub,dut.sync_inst.row,dut.sync_inst.col,halt_n,ab);
         if(!halt_n)starts=starts+1;
         else begin releases=releases+1;last_release=t;end
       end
       if(t>256 && nmi_n!==last_nmi)begin
         $display("NMI tick=%0d sub=%0d row=%0d col=%0d level=%b release_delay=%0d",t,sub,dut.sync_inst.row,dut.sync_inst.col,nmi_n,t-last_release);
         if(!nmi_n)begin
           if(!halt_n || last_release<0) $fatal(1,"NMI precedes HALT release");
           if(flag==2 && dut.sync_inst.row!=16+height) $fatal(1,"wrong zone handoff");
           edges=edges+1;last_assert=t;
         end else begin
           completed_pulses=completed_pulses+1;
           if(t-last_assert != (slow ? 24 : 16)) $fatal(1,"wrong pulse width");
           $display("WIDTH %0d",t-last_assert);
         end
       end
       if(dut.sync_inst.row!==last_row && t>256 && dut.sync_inst.col==0)begin
         if(last_line_tick>=0 && t-last_line_tick!=908)$fatal(1,"wrong line length");
         if(last_line_tick>=0) measured_lines=measured_lines+1;
         last_row=dut.sync_inst.row;last_line_tick=t;
       end
       last_halt=halt_n;last_nmi=nmi_n;
       #4 clk_sys=0;
     end
   end
   $display("RESULT height=%0d flag=%0d slow=%0d pal=%b starts=%0d releases=%0d edges=%0d",height,flag,slow,pal,starts,releases,edges);
   if(edges!=expected || completed_pulses!=expected || !nmi_n || starts!=24 || releases!=24 || measured_lines!=38)
     $fatal(1,"wrong inventory: expected=%0d pulses=%0d lines=%0d",expected,completed_pulses,measured_lines);
   $finish;
 end
endmodule
