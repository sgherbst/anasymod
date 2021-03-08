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
        // wait for emulator reset to complete
        wait_emu_reset();

        // wait a certain amount of time
        sleep_emu(10e-9);

        // end simulation
        $finish;
    end
endmodule