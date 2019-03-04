`timescale 1ns/1ps

`include "msdsl.sv"

`default_nettype none

module top(
    `ifndef SIMULATION_MODE_MSDSL
        input wire logic ext_clk
    `endif // `ifndef SIMULATION_MODE_MSDSL
);

// create ext_clk signal when running in simulation mode
`ifdef SIMULATION_MODE_MSDSL
    logic ext_clk;
`endif // `ifdef SIMULATION_MODE_MSDSL

// emulation clock and reset declarations
logic emu_clk, emu_rst;

// VIO
logic [(`DEC_BITS_MSDSL-1):0] emu_dec_thr;
vio_gen #(
    .dec_bits(`DEC_BITS_MSDSL)
) vio_gen_i(
    .emu_clk(emu_clk),
    .emu_rst(emu_rst),
    .emu_dec_thr(emu_dec_thr)
);

// Clock generator
clk_gen clk_gen_i(
    .ext_clk(ext_clk),
    .emu_clk(emu_clk)
);

// make probes needed for emulation control
`MAKE_EMU_CTRL_PROBES;

// instantiate testbench
tb tb_i();

// simulation control
`ifdef SIMULATION_MODE_MSDSL
    // stop simulation after some time
    initial begin
        #((`TSTOP_MSDSL)*1s);
        $finish;
    end

    // dump waveforms to a specified VCD file
    `define ADD_QUOTES_TO_MACRO(macro) `"macro`"
    initial begin
        $dumpfile(`ADD_QUOTES_TO_MACRO(`VCD_FILE_MSDSL));
    end
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule

`default_nettype wire