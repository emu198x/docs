module restart_tb;
 reg clk=0,reset=1,enabled=0,rw=1,pal=0;
 reg [15:0] cpu_address='h8000;
 reg [7:0] cpu_data=0;
 wire [15:0] dma_address;
 wire [7:0] data_out,yc;
 wire phi1,phi2,mclk0,mclk1,halt_n,nmi_n,drive,ready,vblank;
 reg [7:0] memory[0:65535];
 reg sampled_halt=1,released=0;
 reg [15:0] held_address=0,memory_address=0;
 reg [7:0] memory_data=0;
 wire [15:0] address=released ? (drive ? dma_address : held_address) : (drive ? cpu_address & dma_address : cpu_address);
 integer t,i,object_mode=1,width=2,height,slow,objects,base,stride,reads=0,starts=0,releases=0;
 integer target,scenario,write_count=0,next_write=0;
 reg advance_cpu=0;
 reg [7:0] old_ctrl,old_shadow;
 reg old_halt=1,old_drive=0,old_released=0;
 reg [15:0] old_address=0;
 maria dut(.AB_in(address),.AB_out(dma_address),.d_in(memory_data),
   .write_DB_in(cpu_data),.DB_out(data_out),.reset(reset),.clk_sys(clk),
   .ce(1'b1),.mclk0(mclk0),.mclk1(mclk1),.pclk0(phi2),.pclk1(phi1),.pclk2(phi2),
   .RW(rw),.maria_en(enabled),.YC(yc),.vblank(vblank),.NMI_n(nmi_n),
   .halt_n(halt_n),.ready(ready),.drive_AB(drive),.hide_border(1'b0),
   .bypass_bios(1'b0),.PAL(pal));
 always @(posedge clk)begin
   held_address<=address;memory_address<=address;memory_data<=memory[address];
   released<=~sampled_halt;
   if(reset)begin sampled_halt<=1;released<=0;end
   else if(phi1)sampled_halt<=halt_n;
 end
 initial begin
   dut.dma_inst.LONGHDR=0;dut.dma_inst.IND=0;dut.dma_inst.sel5_cnt=0;
   dut.old_men=0;dut.men_count=0;dut.pclk=0;dut.dma_inst.noslow=0;
   if(!$value$plusargs("height=%d",height))height=1;
   if(!$value$plusargs("slow=%d",slow))slow=0;
   if(!$value$plusargs("objects=%d",objects))objects=1;
   if(!$value$plusargs("target=%d",target))target=15420;
   if(!$value$plusargs("scenario=%d",scenario))scenario=0;
   if($test$plusargs("pal"))pal=1;
   for(i=0;i<65536;i=i+1)memory[i]=0;
   for(i=0;i<256;i=i+1)begin
     memory['h1800+3*i]=height-1;memory['h1801+3*i]='h1c;
   end
   stride=object_mode==1 ? 4 : 5;
   for(i=0;i<objects;i=i+1)begin
     base='h1c00+i*stride;memory[base]=0;
     memory[base+1]=object_mode==1 ? 32-width : (object_mode==2 ? 'h40 : 'h60);
     memory[base+2]='h90;
     if(object_mode!=1)memory[base+3]=32-width;
   end
   for(i='h8000;i<'ha000;i=i+1)memory[i]='h55;
   for(t=0;t<908*24;t=t+1)begin
     reset=t<32;enabled=t>=32;
     if(t<256)begin
     rw=0;
     if(t<80)begin cpu_address='h003c;cpu_data='h60;end
     else if(t<128)begin cpu_address='h002c;cpu_data='h18;end
     else if(t<176)begin cpu_address='h0030;cpu_data=0;end
     else if(t<224)begin cpu_address='h003c;cpu_data=scenario==1 ? 'h60 : 'h40;end
     else if(t<256)begin cpu_address='h0034;cpu_data='h80;end
     end
     if(t==256)begin
       rw=1;cpu_address=slow ? 'h0280 : 'h8000;
       $display("BASE %04h %04h %01h %02h",dut.dma_inst.ZONE_PTR,dut.dma_inst.DL,dut.dma_inst.OFFSET,dut.ctrl);
     end
     #5;
     advance_cpu=t>=256 && phi1 && halt_n && !drive;
     old_ctrl=dut.ctrl;old_shadow=dut.control_inst.ctrl_1;
     if($test$plusargs("debug") && t>=target-8 && t<target+48)
       $display("DEBUG %0d phase=%b%b ctrl=%h state=%b%b%b%b%b mode=%b%b reset=%b request=%b%b halt=%b sel5=%b drive=%b",t,mclk0,mclk1,dut.ctrl,dut.dma_inst.PLA0,dut.dma_inst.PLA1,dut.dma_inst.PLA2,dut.dma_inst.PLA3,dut.dma_inst.PLA4,dut.dma_inst.cond2[7],dut.dma_inst.cond2[6],dut.dma_inst.HALTRST,dut.dma_inst.vbe_halt,dut.dma_inst.hbs_halt,halt_n,dut.dma_inst.sel_5,drive);
     if(t>256 && drive && !released)$fatal(1,"bus collision");
     if(t>14000)begin
       if(mclk0 && (dut.latch_byte || dut.latch_hpos ||
           (dut.dma_inst.data_en && |{dut.dma_inst.DLILDF,dut.dma_inst.OFFLD,
           dut.dma_inst.DPRHLD,dut.dma_inst.DPRLLD,dut.dma_inst.WLD1F,
           dut.dma_inst.WLATLDF,dut.dma_inst.PPHLD,dut.dma_inst.PPLLD,dut.dma_inst.TLD})))begin
         if(^memory_data===1'bx)$fatal(1,"unknown read");
         $display("%0d R %04h %02h",t,memory_address,memory_data);reads=reads+1;
       end
     end
     clk=1;#1;
     if(t>256)begin
       if(dut.ctrl!==old_ctrl)$display("%0d C %02h",t,dut.ctrl);
       if(dut.control_inst.ctrl_1!==old_shadow)$display("%0d S %02h",t,dut.control_inst.ctrl_1);
     end
     if(advance_cpu)begin
       rw=1;cpu_address=slow ? 'h0280 : 'h8000;
       if((next_write==0 && t>=target) || (scenario==0 && next_write==1 && t>=target+96))begin
         if(drive)$fatal(1,"CPU write during MARIA ownership");
         cpu_address='h003c;cpu_data=(scenario==1 || next_write==1) ? 'h40 : 'h60;
         rw=0;next_write=next_write+1;write_count=write_count+1;
         $display("%0d W %04h %02h",t,cpu_address,cpu_data);
       end
     end
     // Let the combinational address bus settle after CPU pin changes before
     // recording the post-edge ownership/address stream.
     #1;
     if(t>14000)begin
       if(^address===1'bx || halt_n===1'bx || drive===1'bx)$fatal(1,"unknown output");
       if(address!==old_address)$display("%0d A %04h",t,address);
       if(drive!==old_drive || released!==old_released)$display("%0d B %b %b",t,drive,released);
       if(halt_n!==old_halt)begin
         $display("%0d H %b",t,halt_n);
         if(halt_n)releases=releases+1;else starts=starts+1;
       end
       if(t>15000 && mclk1 && dut.sync_inst.col==430)begin
         $display("%0d Z %04h %04h %01h",t,dut.dma_inst.ZONE_PTR,dut.dma_inst.DL,dut.dma_inst.OFFSET);
         $write("%0d L ",t);
         for(i=0;i<160;i=i+1)$write("%02h",{3'b0,dut.line_ram_inst.lram_in[i]});
         $write(" ");
         for(i=0;i<160;i=i+1)$write("%02h",{3'b0,dut.line_ram_inst.lram_out[i]});
         $write("\n");
       end
     end
     old_address=address;old_drive=drive;old_released=released;old_halt=halt_n;
     #3;clk=0;
   end
   if(reads<10 || starts==0 || starts!=releases || !halt_n || drive || write_count!=(scenario==0 ? 2 : 1))
     $fatal(1,"incomplete bus cycles: %0d %0d writes=%0d",starts,releases,write_count);
   $display("RESULT reads=%0d starts=%0d releases=%0d writes=%0d",reads,starts,releases,write_count);
   $finish;
 end
endmodule
