module holey_tb;
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
 integer t,i,object_mode,width,height,slow,mask,gfx,kangaroo,base,stride,reads=0,starts=0,releases=0;
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
   if(!$value$plusargs("mode=%d",object_mode))object_mode=1;
   if(!$value$plusargs("width=%d",width))width=2;
   if(!$value$plusargs("height=%d",height))height=1;
   if(!$value$plusargs("slow=%d",slow))slow=0;
   if(!$value$plusargs("mask=%d",mask))mask=1;
   if(!$value$plusargs("gfx=%d",gfx))gfx='h8800;
   if(!$value$plusargs("kangaroo=%d",kangaroo))kangaroo=0;
   if($test$plusargs("pal"))pal=1;
   for(i=0;i<65536;i=i+1)memory[i]=0;
   for(i=0;i<256;i=i+1)begin
     memory['h1800+3*i]=(height-1)|(mask<<5);memory['h1801+3*i]='h1c;
   end
   memory['h1c00]=0;memory['h1c01]='h1e;memory['h1c02]='h50;memory['h1c03]=0;
   memory['h5000]='haa;memory['h5001]='haa;
   stride=object_mode==1 ? 4 : 5;
   base='h1c04;
   memory[base]=object_mode<3 ? gfx[7:0] : 0;
   memory[base+1]=object_mode==1 ? 32-width : (object_mode==2 ? 'h40 : 'h60);
   memory[base+2]=object_mode<3 ? gfx[15:8] : 'h40;
   if(object_mode!=1)memory[base+3]=32-width;
   base=base+stride;
   memory[base]=0;memory[base+1]='h5f;memory[base+2]='h60;memory[base+3]='h08;
   for(i=0;i<32;i=i+1)memory['h4000+i]=gfx[7:0];
   for(i=0;i<16;i=i+1)begin
     memory['h5000+i*256]='haa;memory['h5001+i*256]='haa;
     memory['h6000+i*256]='hff;
     for(base=0;base<32;base=base+1)memory[(gfx+i*256+base)&'hffff]='h55;
   end
   for(t=0;t<908*24;t=t+1)begin
     reset=t<32;enabled=t>=32;rw=0;
     if(t<80)begin cpu_address='h003c;cpu_data='h60;end
     else if(t<128)begin cpu_address='h002c;cpu_data='h18;end
     else if(t<176)begin cpu_address='h0030;cpu_data=0;end
     else if(t<224)begin cpu_address='h003c;cpu_data=(object_mode==4 ? 'h50 : 'h40)|(kangaroo<<2);end
     else if(t<256)begin cpu_address='h0034;cpu_data=gfx[15:8];end
     else begin rw=1;cpu_address=slow ? 'h0280 : 'h8000;end
     #5;
     if(t>256 && drive && !released)$fatal(1,"bus collision");
     if(t>14000)begin
       if(mclk0 && (dut.latch_byte || dut.latch_hpos ||
           (dut.dma_inst.data_en && |{dut.dma_inst.DLILDF,dut.dma_inst.OFFLD,
           dut.dma_inst.DPRHLD,dut.dma_inst.DPRLLD,dut.dma_inst.WLD1F,
           dut.dma_inst.WLATLDF,dut.dma_inst.PPHLD,dut.dma_inst.PPLLD,dut.dma_inst.TLD})))begin
         if(^memory_data===1'bx)$fatal(1,"unknown read");
         $display("%0d R %04h %02h",t,memory_address,memory_data);reads=reads+1;
       end
       if($test$plusargs("debug") && t>=16285 && t<16335)
         $display("DEBUG %0d phase=%b%b lrc=%b rss=%b%b sel=%h cond=%h latch=%b%b data=%b drive=%b off=%h ptr=%h",t,mclk0,mclk1,dut.lrc,dut.dma_inst.RSS1,dut.dma_inst.RSS0,dut.dma_inst.sel,dut.dma_inst.cond2,dut.latch_byte,dut.latch_hpos,dut.dma_inst.data_en,drive,dut.dma_inst.OFFSET,dut.dma_inst.ZONE_PTR);
     end
     clk=1;#1;
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
     #4;clk=0;
   end
   if(reads<10 || starts!=8 || releases!=8 || !halt_n || drive)$fatal(1,"incomplete bus cycles: %0d %0d",starts,releases);
   $display("RESULT reads=%0d starts=%0d releases=%0d",reads,starts,releases);
   $finish;
 end
endmodule
