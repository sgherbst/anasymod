`timescale 1ns/1ps

`ifndef BOARD_CLOCK_FREQ
    `define BOARD_CLOCK_FREQ 125000000
`endif


module test;
    // clock generator
    logic clk=1'b0;
    
	localparam real half_period = 0.5/real'(`BOARD_CLOCK_FREQ);
	
    always begin
        #(half_period*1s) clk = 1'b1;
        #(half_period*1s) clk = 1'b0;
    end

    // instantiate testbench
    top top_i(.SYSCLK(clk));
endmodule