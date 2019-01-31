`timescale 1ns/1ps

`define ADD_QUOTES_TO_MACRO(macro) `"macro`"

module top;

    // clock and reset
    logic emu_clk = 1'b0;
    logic emu_rst = 1'b1;

    // timestep
    real timestep;

    // clock generator
    initial begin
        // set clk to generate posedge
        // this will cause the synchronous reset to take effect
        #0 emu_clk = 1'b1;

        // clear reset
        #0 emu_rst = 1'b0;

        forever begin
            // advance simulation time by the requested amount
            timestep = `DT_MSDSL;
            #(timestep*1s);

            // set clk to generate posedge
            emu_clk = 1'b1;

            // clear clk
            #0 emu_clk = 1'b0;
        end
    end

    // instantiate testbench
    tb tb_i(.clk(emu_clk), .rst(emu_rst));

    // stop simulation after a specified amount of time
    initial begin
        #((`TSTOP_MSDSL)*1s);
        $finish;
    end

    // dump waveforms to a specified VCD file
    initial begin
        $dumpfile(`ADD_QUOTES_TO_MACRO(`VCD_FILE_MSDSL));
    end

endmodule