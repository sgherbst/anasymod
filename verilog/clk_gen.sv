`timescale 1ns/1ps

`default_nettype none
module clk_gen(
	input wire logic clk_port_p,
	output wire logic emu_clk
);

`ifdef SIMULATION_MODE_MSDSL
	// emulator clock sequence
	logic emu_clk_state = 1'b0;
	initial begin
		// since the reset signal is initially "1", this delay+posedge will
		// cause the MSDSL blocks to be reset
	    #((0.5*`DT_MSDSL)*1s);
	    emu_clk_state = 1'b1;

	    // clock runs forever
	    forever begin
	        #((0.5*`DT_MSDSL)*1s);
	        emu_clk_state = ~emu_clk_state;
	    end
	end

	// output assignment
	assign emu_clk = emu_clk_state;
`else
	logic dbg_hub_clk, locked;
	clk_wiz_0 clk_wiz_0_i(
		// input clock
		.clk_in1(clk_port_p),
		// output clocks
		.clk_out1(emu_clk),
		.clk_out2(dbg_hub_clk),
		// other signals
		.reset(1'b0),
		.locked(locked)
	);
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule
`default_nettype wire