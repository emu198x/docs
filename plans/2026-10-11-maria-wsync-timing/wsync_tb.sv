module wsync_tb;
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
 integer t,i,target,mirror,slow,dma_mode,burst,writes=0,falls=0,rises=0;
 reg advance_cpu=0,old_ready=1,old_halt=1,old_drive=0,old_released=0;
 initial begin
   dut.dma_inst.LONGHDR=0;dut.dma_inst.IND=0;dut.dma_inst.sel5_cnt=0;
   dut.old_men=0;dut.men_count=0;dut.pclk=0;dut.dma_inst.noslow=0;
   if(!$value$plusargs("slow=%d",slow))slow=0;
   if(!$value$plusargs("target=%d",target))target=15372;
   if(!$value$plusargs("mirror=%d",mirror))mirror=0;
   if(!$value$plusargs("mode=%d",dma_mode))dma_mode=0;
   if(!$value$plusargs("burst=%d",burst))burst=1;
   if($test$plusargs("pal"))pal=1;
   for(i=0;i<65536;i=i+1)memory[i]=0;
   for(i=0;i<256;i=i+1)begin memory['h1800+3*i]=0;memory['h1801+3*i]='h1c;end
   for(i=0;i<(dma_mode==2 ? 128 : 1);i=i+1)begin
     memory['h1c00+4*i]=0;memory['h1c01+4*i]='h1e;memory['h1c02+4*i]='h90;
   end
   for(i='h9000;i<'ha000;i=i+1)memory[i]='h55;
   for(t=0;t<908*21;t=t+1)begin
     reset=t<32;enabled=t>=32;
     if(t<256)begin
       rw=0;
       if(t<80)begin cpu_address='h003c;cpu_data='h60;end
       else if(t<128)begin cpu_address='h002c;cpu_data='h18;end
       else if(t<176)begin cpu_address='h0030;cpu_data=0;end
       else if(t<224)begin cpu_address='h003c;cpu_data=dma_mode==0 ? 'h60 : 'h40;end
       else begin cpu_address='h0034;cpu_data='h80;end
     end
     if(t==256)begin rw=1;cpu_address=slow ? 'h0280 : 'h8000;end
     #5;
     advance_cpu=t>=256 && phi1 && halt_n && !drive;
     if(t>256 && drive && !released)$fatal(1,"bus collision");
     if(t>14000 && (phi1 || phi2))$display("%0d P %0d",t,phi1 ? 1 : 2);
     clk=1;#1;
     if(t>14000)begin
       if(ready===1'bx)$fatal(1,"unknown READY");
       if(ready!==old_ready)begin
         $display("%0d Q %b",t,ready);
         if(ready)rises=rises+1;else falls=falls+1;
       end
       if(halt_n!==old_halt)$display("%0d H %b",t,halt_n);
       if(drive!==old_drive || released!==old_released)$display("%0d B %b %b",t,drive,released);
       if($test$plusargs("debug") && t>=15360 && t<=15410)
         $display("DEBUG %0d lrc=%b pclk=%b phases=%b%b wsync=%b ri=%b ro=%b q=%b",t,dut.lrc,dut.pclk,phi1,phi2,dut.wsync,dut.ready_int,dut.old_ready,ready);
     end
     if(advance_cpu)begin
       rw=1;cpu_address=slow ? 'h0280 : 'h8000;
       if(t>=target && writes<burst)begin
         cpu_address='h24+mirror;cpu_data=writes;rw=0;writes=writes+1;
         $display("%0d W %04h %02h",t,cpu_address,cpu_data);
       end
     end
     old_ready=ready;old_halt=halt_n;old_drive=drive;old_released=released;
     #4;clk=0;
   end
   if(writes!=burst || falls<1 || rises!=falls || !ready)$fatal(1,"incomplete WSYNC: %0d %0d %0d",writes,falls,rises);
   $display("RESULT writes=%0d falls=%0d rises=%0d",writes,falls,rises);
   $finish;
 end
endmodule
