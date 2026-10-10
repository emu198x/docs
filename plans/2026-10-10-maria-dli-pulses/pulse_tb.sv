// Isolate the vendored DMA module's HALT-release -> NMI pulse logic.
// HALT and DLI are controlled stimuli; this is not a full-DMA timing oracle.
module pulse_tb;
  reg clk_sys=0, reset=1, mclk0=0, pclk1=0;
  reg halt_stimulus=0, dli_stimulus=0;
  wire nmi_n;
  integer t, phase, flag, pulse, edge_count, high_ticks, assertion_tick;
  reg previous;
  dma dut(.clk_sys(clk_sys), .reset(reset), .mclk0(mclk0), .mclk1(1'b0),
    .vblank(1'b1), .vbe(1'b0), .hbs(1'b0), .lrc(1'b0), .pclk1(pclk1),
    .pclk0(1'b0), .ZP(16'h0), .char_width(1'b0), .char_base(8'h0),
    .bypass_bios(1'b0), .d_in(8'h0), .DM(2'b00), .PCLKEDGE(1'b0),
    .pclk(1'b0), .nmi_n(nmi_n));
  initial begin
    force dut.HALT=halt_stimulus;
    force dut.DLI=dli_stimulus;
    for(flag=0;flag<2;flag=flag+1) begin
      for(phase=0;phase<8;phase=phase+1) begin
        previous=1; edge_count=0; high_ticks=0; assertion_tick=-1;
        for(t=0;t<600;t=t+1) begin
          reset=t<32;
          mclk0=t%2==0; pclk1=t%8==0;
          dli_stimulus=flag;
          halt_stimulus=(t>=64 && t<128+phase) || (t>=256 && t<320+phase);
          #5 clk_sys=1; #1;
          if(t>=64) begin
            if(nmi_n===1'bx) $fatal(1,"unknown NMI after warm-up");
            if(!nmi_n) high_ticks=high_ticks+1;
            if(!nmi_n && previous) begin
              edge_count=edge_count+1;
              if(assertion_tick<0) assertion_tick=t;
            end
          end
          previous=nmi_n;
          #4 clk_sys=0;
        end
        $display("flag=%0d release_phase=%0d edges=%0d active_master_ticks=%0d first_assertion=%0d",flag,phase,edge_count,high_ticks,assertion_tick);
        if(edge_count!=2*flag || high_ticks!=32*flag)
          $fatal(1,"each HALT release must yield one two-CPU-cycle pulse when DLI is set");
      end
    end
    $finish;
  end
endmodule
