module fetch_tb;
 reg clk_sys=0, reset=1, ce=0, enabled=0, rw=1, pal=0;
 reg [15:0] cpu_ab=16'h8000;
 reg [7:0] cpu_data=0;
 wire [15:0] dma_ab;
 wire [7:0] data_out,yc;
 wire phi1,phi2,mclk0,mclk1,halt_n,nmi_n,drive,ready,vblank;
 reg [7:0] memory[0:65535];
 reg cpu_halt_latch=1, cpu_released=0;
 reg [15:0] last_address=0;
 reg [7:0] memory_data=0;
 reg [15:0] memory_address=0;
 wire bad_bus=$test$plusargs("old_bus");
 wire [15:0] ab=bad_bus ? (drive ? dma_ab : cpu_ab) : cpu_released ? (drive ? dma_ab : last_address) : (drive ? (cpu_ab & dma_ab) : cpu_ab);
 wire [7:0] data_in=bad_bus ? memory[ab] : memory_data;
 wire [15:0] fetched_address=bad_bus ? ab : memory_address;
 always @(posedge clk_sys)begin
   last_address <= ab;
   memory_data <= memory[ab];
   memory_address <= ab;
   cpu_released <= ~cpu_halt_latch;
   if(reset)begin cpu_halt_latch<=1;cpu_released<=0;end
   else if(phi1)cpu_halt_latch<=halt_n;
 end
 integer t,i,sub,edges,starts,releases,last_release,last_assert,last_line_tick,last_row,last_col;
 integer height,flag,slow,expected,measured_lines,completed_pulses;
 integer object_mode,width,graphics,last_fetch,trace_reads;
 integer line_graphics,zone_offset,expected_address,hpos_reads;
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
   if (!$value$plusargs("object=%d",object_mode)) object_mode=1;
   if (!$value$plusargs("width=%d",width)) width=1;
   trace_reads=$test$plusargs("trace_reads");
   graphics=0;last_fetch=-1;line_graphics=0;hpos_reads=0;
   expected=flag==0 ? 0 : (flag==1 ? 1+23/height : 1);
   measured_lines=0; completed_pulses=0;
   if ($test$plusargs("suppress_nmi")) force dut.NMI_ung_n=1;
   edges=0;starts=0;releases=0;last_release=-1;last_assert=-1;last_line_tick=-1;last_row=-1;last_col=-1;
   for(i=0;i<65536;i=i+1)memory[i]=0;
   for(i=0;i<256;i=i+1)begin
     memory['h1800+3*i]=((flag==1 || (flag==2 && i==1))?'h80:0)|(height-1);
     memory['h1801+3*i]='h1c;memory['h1802+3*i]=0;
   end
   if(object_mode>0)begin
     memory['h1c00]=0;
     memory['h1c01]=object_mode==1 ? (32-width) : (object_mode==2 ? 'h40 : 'h60);
     memory['h1c02]='h90;
     if(object_mode>1) memory['h1c03]=32-width;
     for(i='h8000;i<'ha000;i=i+1)memory[i]='h55;
   end
   for(t=0;t<908*40;t=t+1)begin
     reset=t<32;enabled=t>=32;
     // Hold each setup write through several CPU phases in vertical blank.
     rw=0;
     if(t<80)begin cpu_ab='h003c;cpu_data='h60;end
     else if(t<128)begin cpu_ab='h002c;cpu_data='h18;end
     else if(t<176)begin cpu_ab='h0030;cpu_data='h00;end
     else if(t<224)begin cpu_ab='h003c;cpu_data=object_mode==4 ? 'h50 : 'h40;end
     else if(t<256)begin cpu_ab='h0034;cpu_data='h80;end
     else begin rw=1;cpu_ab=slow ? 16'h0280 : 16'h8000;end
     if(t==256) $display("SETUP t=%0d ctrl=%h zp=%h row=%0d col=%0d mclk=%b%b phi=%b%b pclk=%b men=%h old=%b div=%d toggle=%b",t,dut.ctrl,dut.ZP,dut.sync_inst.row,dut.sync_inst.col,mclk0,mclk1,phi1,phi2,dut.pclk,dut.men_count,dut.old_men,dut.clock_div,dut.pclk_toggle);
     for(sub=0;sub<1;sub=sub+1)begin
       ce=1;
       #5;
       if(t>256 && drive && !cpu_released) $fatal(1,"CPU/MARIA bus collision");
       if(t>256 && mclk0)begin
         if(dut.dma_inst.data_en && dut.dma_inst.DPRLLD && data_in!==8'h00)
           $fatal(1,"wrong descriptor low byte: address=%h data=%h",fetched_address,data_in);
         if(dut.latch_hpos)begin
           hpos_reads=hpos_reads+1;
           if(trace_reads)$display("HPOS tick=%0d row=%0d col=%0d address=%h data=%h",t,dut.sync_inst.row,dut.sync_inst.col,fetched_address,data_in);
         end
         if(dut.dma_inst.data_en && trace_reads && |{dut.dma_inst.DLILDF,dut.dma_inst.OFFLD,dut.dma_inst.DPRHLD,dut.dma_inst.DPRLLD,dut.dma_inst.WLD1F,dut.dma_inst.WLATLDF,dut.dma_inst.PPHLD,dut.dma_inst.PPLLD,dut.dma_inst.TLD})
           $display("READ tick=%0d row=%0d col=%0d drive=%b ab=%h data=%h reload=%h offset=%d",t,dut.sync_inst.row,dut.sync_inst.col,drive,ab,data_in,{dut.dma_inst.DLILDF,dut.dma_inst.OFFLD,dut.dma_inst.DPRHLD,dut.dma_inst.DPRLLD,dut.dma_inst.WLD1F,dut.dma_inst.WLATLDF,dut.dma_inst.PPHLD,dut.dma_inst.PPLLD,dut.dma_inst.TLD},dut.dma_inst.OFFSET);
         if(dut.latch_byte)begin
           zone_offset=height-1-((starts-2)%height);
           expected_address=object_mode<3 ? 'h9000+(zone_offset<<8)+line_graphics : 'h8055+(zone_offset<<8)+(object_mode==4 ? line_graphics%2 : 0);
           if(data_in!==8'h55 || fetched_address!=expected_address)
             $fatal(1,"wrong graphics read: expected=%h actual=%h data=%h",expected_address,fetched_address,data_in);
           graphics=graphics+1;line_graphics=line_graphics+1;
           if(trace_reads)$display("GFX tick=%0d row=%0d col=%0d drive=%b ab=%h data=%h",t,dut.sync_inst.row,dut.sync_inst.col,drive,ab,data_in);
         end
       end
       clk_sys=1;#1;
       if(t>256 && (halt_n===1'bx || nmi_n===1'bx || drive===1'bx))$fatal(1,"unknown bus control");
       if(t>256 && halt_n!==last_halt)begin
         $display("HALT tick=%0d sub=%0d row=%0d col=%0d level=%b ab=%h",t,sub,dut.sync_inst.row,dut.sync_inst.col,halt_n,ab);
         if(!halt_n)begin starts=starts+1;line_graphics=0;end
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
   $display("FETCH_RESULT object=%0d width=%0d graphics=%0d",object_mode,width,graphics);
   if(graphics != 23*width*(object_mode==4 ? 2 : 1)) $fatal(1,"wrong graphics count");
   $finish;
 end
endmodule
