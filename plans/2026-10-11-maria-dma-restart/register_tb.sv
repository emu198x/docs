module register_tb;
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
 function automatic [7:0] register_value(input integer r);
   case(r)
     'h0c: register_value=dut.ZP[15:8];
     'h10: register_value=dut.ZP[7:0];
     'h14: register_value=dut.char_base;
     'h1c: register_value=dut.ctrl;
     default: register_value=dut.color_map[dut.control_inst.color_ram_index[r]];
   endcase
 endfunction
 integer t,i,slow,target,mirror,index=0,writes=0,commits=0;
 reg idle_cycle=0,advance_cpu=0;
 reg [7:0] observed[0:31];
 initial begin
   dut.dma_inst.LONGHDR=0;dut.dma_inst.IND=0;dut.dma_inst.sel5_cnt=0;
   dut.old_men=0;dut.men_count=0;dut.pclk=0;dut.dma_inst.noslow=0;
   if(!$value$plusargs("slow=%d",slow))slow=0;
   if(!$value$plusargs("target=%d",target))target=11000;
   if(!$value$plusargs("mirror=%d",mirror))mirror=0;
   if($test$plusargs("pal"))pal=1;
   for(i=0;i<65536;i=i+1)memory[i]=0;
   for(t=0;t<13000;t=t+1)begin
     reset=t<32;enabled=t>=32;
     if(t<256)begin
       rw=0;
       if(t<80)begin cpu_address='h003c;cpu_data='h60;end
       else if(t<128)begin cpu_address='h002c;cpu_data='h18;end
       else if(t<176)begin cpu_address='h0030;cpu_data=0;end
       else if(t<224)begin cpu_address='h003c;cpu_data='h60;end
       else begin cpu_address='h0034;cpu_data='h80;end
     end
     if(t==256)begin
       rw=1;cpu_address=slow ? 'h0280 : 'h8000;
       for(i=0;i<32;i=i+1)observed[i]=register_value(i);
     end
     #5;
     advance_cpu=t>=256 && phi1;
     if(t>256 && (drive || !halt_n))$fatal(1,"unexpected DMA during register capture");
     clk=1;#1;
     if(t>256)begin
       for(i=0;i<32;i=i+1)begin
         if(i!=4 && i!=8 && i!=24 && register_value(i)!==observed[i])begin
           $display("%0d G %02h %02h",t,i[7:0],register_value(i));commits=commits+1;
         end
         observed[i]=register_value(i);
       end
     end
     if(advance_cpu)begin
       rw=1;cpu_address=slow ? 'h0280 : 'h8000;
       if(t>=target && index<32)begin
         if(idle_cycle)idle_cycle=0;
         else begin
           cpu_address='h20+index+mirror;cpu_data=index==28 ? 'h40 : 'h40+3*index;
           rw=0;writes=writes+1;
           $display("%0d W %04h %02h",t,cpu_address,cpu_data);
           index=index+1;
           if(index==4 || index==8 || index==24)index=index+1;
           idle_cycle=1;
         end
       end
     end
     #4;clk=0;
   end
   if(writes!=29 || commits!=29)$fatal(1,"incomplete registers: %0d %0d",writes,commits);
   $display("RESULT writes=%0d commits=%0d",writes,commits);
   $finish;
 end
endmodule
