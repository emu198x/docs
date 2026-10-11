 // Independent equations qualified against the recovered 32-row PLA table.
 // Return {reset, set, enable, next_state[1:0]}.
 function automatic [4:0] edge_transfer(input [1:0] state,
                                        input dli, halt, event_input);
   reg [4:0] result;
   begin
     result=0;
     case(state)
       0: begin
         result[1:0]=(halt && event_input) ? 2 : 0;
         result[2]=halt && event_input;
         result[4]=event_input;
       end
       2: result[1:0]=(halt || (dli && !event_input)) ? 2 : dli ? 3 : 0;
       3: begin result[1:0]=event_input ? 0 : 3; result[3]=event_input; end
       default: result=0;
     endcase
     edge_transfer=result;
   end
 endfunction
 reg [1:0] edge_state[0:2], edge_next[0:2];
 reg edge_halt=1, edge_dli=1, previous_level=0;
 reg [2:0] observed_nmi=3'b111, previous_nmi=3'b111;
 reg [2:0] previous_event=0;
 wire physical_level=~dut.dma_inst.PCLKEDGE;
 wire [2:0] event_input={(!physical_level && previous_level),
   ($test$plusargs("wide_edge") ? physical_level : physical_level && !previous_level),
   physical_level};
 wire [4:0] edge_word[0:2];
 genvar observer;
 generate for(observer=0;observer<3;observer=observer+1)begin
   assign edge_word[observer]=edge_transfer(edge_state[observer],edge_dli,edge_halt,event_input[observer]);
 end endgenerate
 integer edge_assertions[0:2], edge_releases[0:2], edge_start[0:2];
 integer phase1_count=0, edge_cpu_start[0:2];
 reg [4:0] edge_clock_start[0:2];
 integer event_count[0:2], event_high[0:2], sample_count=0;
 integer update_index, monitor_index;
 initial begin
   for(update_index=0;update_index<3;update_index=update_index+1)begin
     edge_state[update_index]=3;edge_next[update_index]=0;
     edge_assertions[update_index]=0;edge_releases[update_index]=0;
     edge_start[update_index]=-1;event_count[update_index]=0;event_high[update_index]=0;
     edge_cpu_start[update_index]=0;
     edge_clock_start[update_index]=0;
   end
 end
 always @(posedge clk_sys)begin
   if(reset)phase1_count<=0;
   else if(phi1)phase1_count<=phase1_count+1;
   if(reset)begin
     edge_halt<=1;edge_dli<=1;previous_level<=0;observed_nmi<=3'b111;
     previous_event<=0;
     for(update_index=0;update_index<3;update_index=update_index+1)begin
       edge_state[update_index]<=3;edge_next[update_index]<=0;
     end
   end else if(mclk0)begin
     if(t>256)begin
       if(edge_word[0] !== {dut.dma_inst.sel[0],dut.dma_inst.sel[6],dut.dma_inst.sel[5],
                            (|dut.dma_inst.sel[5:1]),(|dut.dma_inst.sel[2:1])})
         $fatal(1,"shadow selector differs from reference");
       if((^event_input)===1'bx)$fatal(1,"unknown observer edge");
       sample_count=sample_count+1;
       for(update_index=0;update_index<3;update_index=update_index+1)begin
         if(event_input[update_index])event_high[update_index]=event_high[update_index]+1;
         if(event_input[update_index] && !previous_event[update_index])
           event_count[update_index]=event_count[update_index]+1;
         if(update_index>0 && event_input[update_index] && previous_event[update_index])
           $fatal(1,"candidate edge wider than one MARIA step");
       end
     end
     previous_event<=event_input;
     previous_level<=physical_level;
     for(update_index=0;update_index<3;update_index=update_index+1)begin
       edge_next[update_index]<=edge_word[update_index][1:0];
       if(edge_word[update_index][3])observed_nmi[update_index]<=0;
       if(edge_word[update_index][4])observed_nmi[update_index]<=1;
     end
     if($test$plusargs("suppress_edge_observer"))observed_nmi[1]<=1;
   end else if(mclk1)begin
     edge_halt<=dut.dma_inst.vbe_halt || dut.dma_inst.hbs_halt;
     edge_dli<=dut.dma_inst.DLI;
     for(update_index=0;update_index<3;update_index=update_index+1)
       edge_state[update_index]<=edge_next[update_index];
   end
 end
