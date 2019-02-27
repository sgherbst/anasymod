`timescale 1ns/1ps

`default_nettype none
module vio_gen #(
    parameter dec_bits = 1
)(
	input wire logic emu_clk,
	output wire logic emu_rst,
	output wire logic [(dec_bits-1):0] emu_dec_thr
);

`ifdef SIMULATION_MODE_MSDSL
	// reset sequence
	logic emu_rst_state = 1'b1;
	initial begin
		#((`DT_MSDSL)*1s);
		emu_rst_state = 1'b0;
	end

	// output assignment
	assign emu_rst = emu_rst_state;
	`ifndef DEC_THR_VAL_MSDSL
	    `define DEC_THR_VAL_MSDSL 0
	`endif // `ifdef DEC_THR_VAL_MSDSL
	assign emu_dec_thr = `DEC_THR_VAL_MSDSL;
`else
	// VIO instantiation
	vio_0 vio_0_i (
		.clk(emu_clk),
		.probe_out0(emu_rst),
		.probe_out1(emu_dec_thr)
	);
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule
`default_nettype wire