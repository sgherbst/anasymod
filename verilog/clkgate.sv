// Gated clock model
// *** ONLY FOR SIMULATION ***

`timescale 1ns/1ps

`default_nettype none

module ana_clkgate(
	input wire en,
	input wire clk,
	output wire gated
);
	
	reg en_latched = 0;

	always @* begin
		if (clk == 1'b0) begin
			en_latched <= en;
		end
	end

	assign gated = clk & en_latched;

endmodule

`default_nettype wire