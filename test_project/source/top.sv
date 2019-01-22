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

	`ifdef SIMULATION_TARGET
		initial begin
			rst = 1'b1;
			#3000 rst = 1'b0;
		end
	`else
		vio vio_i (
			.clk(clk),
			.rst(rst)
		);
	`endif

endmodule

`default_nettype wire

