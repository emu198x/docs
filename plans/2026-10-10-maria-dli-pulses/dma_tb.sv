module dma_tb;
  reg clk_sys=0, reset=1;
  reg mclk0=0, mclk1=0, vblank=1, vbe=0, hbs=0, lrc=0;
  reg pclk1=0, pclk0=0, pclk=1, pclkedge=0;
  wire halt, dli, nmi_n, aben;
  wire [15:0] ab;
  reg [7:0] memory [0:65535];
  wire [7:0] din = memory[ab];
  integer i, t, phase, line, dot, idle;
  integer height, flag, start_phase, expected, edges, starts, releases, assertion_tick, last_release, pulse_width;
  reg last_halt, last_nmi;
  dma dut(.clk_sys(clk_sys), .reset(reset), .mclk0(mclk0), .mclk1(mclk1),
    .vblank(vblank), .vbe(vbe), .hbs(hbs), .lrc(lrc), .pclk1(pclk1),
    .pclk0(pclk0), .ZP(16'h1800), .char_width(1'b0), .char_base(8'h00),
    .bypass_bios(1'b0), .d_in(din), .DM(2'b10), .PCLKEDGE(pclkedge),
    .pclk(pclk), .HALT(halt), .DLI(dli), .AB(ab), .ABEN(aben), .nmi_n(nmi_n));
  initial begin
    // These three controls have no reset assignments in the FPGA module.
    // Explicit zero power-up assumption, before exercising its actual reset.
    dut.LONGHDR=0; dut.IND=0; dut.sel5_cnt=0;
    if (!$value$plusargs("height=%d", height)) height=1;
    if (!$value$plusargs("flag=%d", flag)) flag=1;
    if (!$value$plusargs("phase=%d", start_phase)) start_phase=0;
    expected=flag==0 ? 0 : (flag==1 ? 1+39/height : 1);
    edges=0; starts=0; releases=0; assertion_tick=-1; last_release=-1;
    if ($test$plusargs("suppress_nmi")) force dut.nmi_n=1;
    for (i=0; i<65536; i=i+1) memory[i]=0;
    for (i=0; i<256; i=i+1) begin
      memory['h1800+3*i]=((flag==1 || (flag==2 && i==1)) ? 'h80 : 0) | (height-1);
      memory['h1801+3*i]='h1c;
      memory['h1802+3*i]=0;
    end
    last_halt=0; last_nmi=1;
    for (t=0;t<912*40+start_phase;t=t+1) begin
      phase=t%8; line=(t-64-start_phase)/912; dot=(t-64-start_phase)%912;
      reset=(t<32); vblank=(t<64+start_phase);
      mclk0=(t%2==0); mclk1=!mclk0;
      pclk1=(phase==0); pclk0=(phase==4);
      pclk=(phase==0 || phase>=5); pclkedge=(phase<4);
      vbe=(t==64+start_phase); hbs=(t>64+start_phase && dot==0); lrc=0;
      #5 clk_sys=1;
      #1;
      if (t>=64+start_phase && halt!==last_halt)
        $display("HALT t=%0d line=%0d dot=%0d level=%b zone=%h offset=%h dli=%b",t-64-start_phase,line,dot,halt,dut.ZONE_PTR,dut.OFFSET,dli);
      if (t>=64+start_phase && nmi_n!==last_nmi)
        $display("NMI t=%0d line=%0d dot=%0d level=%b zone=%h offset=%h dli=%b",t-64-start_phase,line,dot,nmi_n,dut.ZONE_PTR,dut.OFFSET,dli);
      if (t>=64+start_phase) begin
        if (halt===1'bx || nmi_n===1'bx) $fatal(1,"unknown output after startup");
        if (halt && !last_halt) starts=starts+1;
        if (!halt && last_halt) begin last_release=t; releases=releases+1; end
        if (!nmi_n && last_nmi) begin
          if (halt || last_release<0) $fatal(1,"NMI precedes DMA shutdown");
          if(flag==2 && line!=height) $fatal(1,"DLI is not at the preceding zone's shutdown");
          assertion_tick=t; edges=edges+1;
          $display("ASSERT after_shutdown=%0d",t-last_release);
        end
        if (nmi_n && !last_nmi) begin
          pulse_width=t-assertion_tick;
          if(pulse_width!=16) $fatal(1,"wrong NMI width %0d",pulse_width);
        end
      end
      last_halt=halt; last_nmi=nmi_n;
      #4 clk_sys=0;
      mclk0=0; mclk1=0; pclk0=0; pclk1=0; vbe=0; hbs=0;
      for (idle=0;idle<3;idle=idle+1) begin
        #5 clk_sys=1; #5 clk_sys=0;
      end
    end
    $display("RESULT height=%0d flag=%0d phase=%0d edges=%0d expected=%0d",height,flag,start_phase,edges,expected);
    if(starts!=40 || releases!=40) $fatal(1,"incomplete DMA: starts=%0d releases=%0d",starts,releases);
    if(edges!=expected || !nmi_n) $fatal(1,"missing/repeated/unterminated NMI");
    $finish;
  end
endmodule
