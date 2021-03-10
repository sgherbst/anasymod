`timescale 1s/1ns
`include "svreal.sv"

module sim_ctrl #(
    `DECL_REAL(tlo),
    `DECL_REAL(thi)
) (
    `OUTPUT_REAL(tlo),
    `OUTPUT_REAL(thi)
);
    `include "anasymod.sv"

    `ASSIGN_CONST_REAL(62.5e-12, tlo);
    `ASSIGN_CONST_REAL(62.5e-12, thi);

    initial begin
        // clamp the maximum emulator timestep
	set_max_emu_dt(100e-12);	

        // wait a certain amount of time
	#(10us);

        // end simulation
        $finish;
    end
endmodule
