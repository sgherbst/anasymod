`timescale 1ns/1ps

`default_nettype none

module top (
    input wire logic SYSCLK
);

    logic clk;
    logic rst;

    tb tb_i (
        .clk(clk),
        .rst(rst)
    );

    clkgen clkgen_i (
        .SYSCLK(SYSCLK),
        .clk(clk)
    );

    vio vio_i (
	    .clk(clk),
		.rst(rst)
	);

endmodule

`default_nettype wire

