module split_driver_tb;
  logic clk=0;
  logic [3:0] offset=0;
  logic [13:0] condition;
  assign condition[3:2] = {~|offset, 1'b1};
  always @(posedge clk) begin
    condition[13:4] <= 10'h288;
    condition[1:0] <= 2'b11;
  end
  wire match_state = condition ==? 14'b10100xxxxxxxxx;
  wire match_mask = (condition & 14'b11111000000000) == 14'b10100000000000;
  initial begin
    #1 clk=1;
    #1 $display("before condition=%h wildcard=%b masked=%b",condition,match_state,match_mask);
    offset=1;
    #1 $display("after condition=%h wildcard=%b masked=%b direct=%b",condition,match_state,match_mask,condition ==? 14'b10100xxxxxxxxx);
    if(match_state !== match_mask) $fatal(1,"continuous wildcard differs from mask on split-driven vector");
    $finish;
  end
endmodule
