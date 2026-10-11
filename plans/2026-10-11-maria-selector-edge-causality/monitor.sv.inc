       if(t>256)begin
         if(observed_nmi[0]!==selector_nmi_n)$fatal(1,"shadow NMI differs from reference selector observer");
         for(monitor_index=0;monitor_index<3;monitor_index=monitor_index+1)begin
           if(observed_nmi[monitor_index]!==previous_nmi[monitor_index])begin
             $display("EDGE_NMI observer=%0d tick=%0d row=%0d col=%0d level=%b halt=%b delay=%0d width=%0d cpu_cycles=%0d same_phase=%b",monitor_index,t,dut.sync_inst.row,dut.sync_inst.col,observed_nmi[monitor_index],halt_n,t-last_release,t-edge_start[monitor_index],phase1_count-edge_cpu_start[monitor_index],edge_clock_start[monitor_index]==={dut.clock_div,dut.pclk_toggle,dut.pclk});
             if(!observed_nmi[monitor_index])begin
               edge_assertions[monitor_index]=edge_assertions[monitor_index]+1;
               edge_start[monitor_index]=t;
               edge_cpu_start[monitor_index]=phase1_count;
               edge_clock_start[monitor_index]={dut.clock_div,dut.pclk_toggle,dut.pclk};
             end else edge_releases[monitor_index]=edge_releases[monitor_index]+1;
           end
         end
       end
       previous_nmi=observed_nmi;
