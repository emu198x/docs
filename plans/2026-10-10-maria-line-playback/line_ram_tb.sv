// Own output-only probe; compile against the separately qualified reference.
module line_ram_tb;
 reg clk=0, reset=0, wm=0, border=1, latch_byte=0, latch_hpos=0;
 reg kangaroo=0, lrc=0;
 reg [2:0] palette=0;
 reg [7:0] data=0;
 reg [1:0] rm=0;
 reg [24:0][7:0] colours;
 wire [7:0] playback;
 wire [7:0] observed=$test$plusargs("drop_pixel") ? 0 : playback;
 integer w,k,p,r,b,x,i,pos,case_count=0,pixel_count=0;
 line_ram dut(.clk_sys(clk),.RESET(reset),.PLAYBACK(playback),
   .PALETTE(palette),.d_in(data),.WM(wm),.border(border),
   .latch_byte(latch_byte),.latch_hpos(latch_hpos),.COLOR_MAP(colours),
   .RM(rm),.KANGAROO_MODE(kangaroo),.BORDER_CONTROL(1'b0),
   .COLOR_KILL(1'b0),.lrc(lrc),.LRAM_OUT_COL(9'b0),
   .mclk0(1'b1),.mclk1(1'b0),.cram_write(1'b0));

 task step;
   begin #5;clk=1;#1;clk=0;#4;end
 endtask
 task position(input integer h);
   begin latch_hpos=1;data=h;step();latch_hpos=0;end
 endtask
 task graphics(input integer value);
   begin latch_byte=1;data=value;step();latch_byte=0;end
 endtask
 task transfer;
   begin border=1;lrc=1;step();lrc=0;end
 endtask
 task pixel;
   begin
     step();
     if (^observed===1'bx) $fatal(1,"unknown playback");
     $write("%02h",observed);
     pixel_count=pixel_count+1;
   end
 endtask

 initial begin
   colours[0]='h0e;
   for(i=1;i<25;i=i+1)colours[i]='h40+i;
   reset=1;step();reset=0;
   transfer();transfer();
   for(w=0;w<2;w=w+1)for(k=0;k<2;k=k+1)for(p=0;p<8;p=p+1)for(r=0;r<4;r=r+1)begin
     $write("VECTOR %0d %0d %0d %0d ",w,k,p,r);
     for(b=0;b<256;b=b+1)begin
       // Existing opaque object underneath the incoming byte.
       border=1;position(0);wm=0;palette=3;kangaroo=0;graphics('haa);
       position(0);wm=w;palette=p;kangaroo=k;graphics(b);
       transfer();rm=r;border=0;
       for(x=0;x<8;x=x+1)begin
         pixel();
         if(w==0 && k==0 && p==0 && r==0 && b=='h55 && observed!='h41)
           $fatal(1,"known 160A colour missing");
         if(w==0 && k==0 && p==0 && r==0 && b==0 && observed!='h4b)
           $fatal(1,"transparent byte erased the earlier object");
       end
       case_count=case_count+1;
     end
     $write("\n");
   end
   for(w=0;w<2;w=w+1)for(r=0;r<4;r=r+1)for(pos=0;pos<6;pos=pos+1)begin
     border=1;position(0);wm=0;palette=3;kangaroo=0;
     for(i=0;i<40;i=i+1)graphics('haa);
     case(pos)
       0:position(1);1:position(158);2:position(159);
       3:position(160);4:position(254);5:position(255);
     endcase
     wm=w;palette=5;graphics('hb6);graphics('h6d);
     transfer();rm=r;border=0;
     $write("BOUND %0d %0d %0d ",w,r,pos);
     for(x=0;x<320;x=x+1)pixel();
     $write("\n");
   end
   if(case_count!=32768 || pixel_count!=277504)$fatal(1,"incomplete inventory");
   $display("RESULT cases=%0d pixels=%0d",case_count,pixel_count);
   $finish;
 end
endmodule
