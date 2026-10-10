module raster_tb;
 reg clk=0, reset=1, enabled=0, rw=1, pal=0;
 reg [15:0] cpu_address='h8000;
 reg [7:0] cpu_data=0;
 wire [15:0] dma_address;
 wire [7:0] data_out,yc;
 wire phi1,phi2,mclk0,mclk1,halt_n,nmi_n,drive,ready,vblank;
 reg [7:0] memory[0:65535];
 reg sampled_halt=1,released=0;
 reg [15:0] held_address=0;
 reg [7:0] memory_data=0;
 wire [15:0] address=released ? (drive ? dma_address : held_address) : cpu_address;
 integer t,i,w,r,h,slow,live,setup,palette_index,colour_index,samples=0,transfers=0;
 integer left,width,transfer_tick=0,transfer_row=0;
 reg [7:0] old_control,old_background,old_colour;
 integer register_ticks[32],register_addresses[32],register_values[32],register_count=0;
 maria dut(.AB_in(address),.AB_out(dma_address),.d_in(memory_data),
   .write_DB_in(cpu_data),.DB_out(data_out),.reset(reset),.clk_sys(clk),
   .ce(1'b1),.mclk0(mclk0),.mclk1(mclk1),.pclk0(phi2),.pclk1(phi1),.pclk2(phi2),
   .RW(rw),.maria_en(enabled),.YC(yc),.vblank(vblank),.NMI_n(nmi_n),
   .halt_n(halt_n),.ready(ready),.drive_AB(drive),.hide_border(1'b0),
   .bypass_bios(1'b0),.PAL(pal));
 always @(posedge clk)begin
   held_address<=address;memory_data<=memory[address];released<=~sampled_halt;
   if(reset)begin sampled_halt<=1;released<=0;end
   else if(phi1)sampled_halt<=halt_n;
 end
 initial begin
   dut.dma_inst.LONGHDR=0;dut.dma_inst.IND=0;dut.dma_inst.sel5_cnt=0;
   dut.old_men=0;dut.men_count=0;dut.pclk=0;dut.dma_inst.noslow=0;
   if(!$value$plusargs("wm=%d",w))w=0;
   if(!$value$plusargs("rm=%d",r))r=0;
   if(!$value$plusargs("hpos=%d",h))h=0;
   if(!$value$plusargs("slow=%d",slow))slow=0;
   if(!$value$plusargs("live=%d",live))live=0;
   if($test$plusargs("pal"))pal=1;
   left=pal ? 24 : 27;width=320+2*left;
   for(i=0;i<65536;i=i+1)memory[i]=0;
   for(i=0;i<256;i=i+1)begin
     memory['h1800+3*i]=1;memory['h1801+3*i]='h1c;
   end
   memory['h1c00]=0;memory['h1c01]='h40|(w<<7);memory['h1c02]='h90;
   memory['h1c03]='hbe;memory['h1c04]=h; // palette 5, width 2
   memory['h9000]='h1b;memory['h9001]='h96;
   memory['h9100]='he4;memory['h9101]='h69;
   for(t=0;t<32+908*22;t=t+1)begin
     reset=t<32;enabled=t>=32;rw=0;
     if(t<80)begin cpu_address='h003c;cpu_data='h60;end
     else if(t<128)begin cpu_address='h002c;cpu_data='h18;end
     else if(t<176)begin cpu_address='h0030;cpu_data=0;end
     else if(t<224)begin cpu_address='h003c;cpu_data='h48|r;end
     else if(t<256)begin cpu_address='h0020;cpu_data='h02;end
     else if(t<1024)begin
       setup=(t-256)/32;palette_index=setup/3;colour_index=setup%3+1;
       cpu_address='h20+palette_index*4+colour_index;cpu_data='h20+(setup+1)*6;
     end else if(live && t>=16560 && t<16576)begin cpu_address='h0037;cpu_data='hbe;end
     else if(live && t>=16576 && t<16592)begin cpu_address='h003c;cpu_data='h48|((r+1)&3);end
     else if(live && t>=16600 && t<16616)begin cpu_address='h0020;cpu_data='h04;end
     else begin rw=1;cpu_address=slow ? 'h0280 : 'h8000;end
     #5;
     if(t>2048 && drive && !released)$fatal(1,"bus collision");
     if(t>2048 && mclk0 && dut.lrc && dut.sync_inst.row>=16 && dut.sync_inst.row<=21)begin
       transfer_tick=t;transfer_row=dut.sync_inst.row;transfers=transfers+1;
     end
     old_control=dut.ctrl;old_background=dut.color_map[0];old_colour=dut.color_map[18];
     clk=1;#1;
     if(t>2048)begin
       if(dut.ctrl!==old_control)begin
         register_ticks[register_count]=t;register_addresses[register_count]='h3c;
         register_values[register_count]=dut.ctrl;register_count=register_count+1;
       end
       if(dut.color_map[0]!==old_background)begin
         register_ticks[register_count]=t;register_addresses[register_count]='h20;
         register_values[register_count]=dut.color_map[0];register_count=register_count+1;
       end
       if(dut.color_map[18]!==old_colour)begin
         register_ticks[register_count]=t;register_addresses[register_count]='h37;
         register_values[register_count]=dut.color_map[18];register_count=register_count+1;
       end
     end
     if(mclk1 && dut.sync_inst.row>=16 && dut.sync_inst.row<=21 && dut.sync_inst.col>=93-left && dut.sync_inst.col<413+left)begin
       if(^yc===1'bx)$fatal(1,"unknown pixel");
       if(dut.sync_inst.col==93-left)$write("ROW %0d ",dut.sync_inst.row);
       $write("%02h",yc);samples=samples+1;
       if(dut.sync_inst.col==412+left)begin
         $write("\n");$display("TRANSFER %0d %0d",transfer_tick,transfer_row);
       end
     end
     #4;clk=0;
   end
   if(samples!=6*width || transfers!=6)$fatal(1,"incomplete output");
   if(register_count!=(live ? 3 : 0))$fatal(1,"incomplete live register changes");
   for(i=0;i<register_count;i=i+1)$display("REGISTER %0d %02h %02h",register_ticks[i],register_addresses[i][7:0],register_values[i][7:0]);
   $display("RESULT pixels=%0d transfers=%0d",samples,transfers);
   $finish;
 end
endmodule
