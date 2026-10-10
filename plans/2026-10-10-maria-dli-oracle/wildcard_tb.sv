module wildcard_tb;
  logic [13:0] condition;
  wire match_state = condition ==? 14'b10100xxxxxxxxx;
  wire match_mask = (condition & 14'b11111000000000) == 14'b10100000000000;
  initial begin
    condition=14'h288f;
    #1 $display("condition=%h wildcard=%b masked=%b",condition,match_state,match_mask);
    condition=14'h2887;
    #1 $display("condition=%h wildcard=%b masked=%b direct=%b",condition,match_state,match_mask,condition ==? 14'b10100xxxxxxxxx);
    if(match_state !== match_mask) $fatal(1,"wildcard comparator differs from explicit mask on known inputs");
    $finish;
  end
endmodule
