`timescale 1ns/1ns

module osc_checker #(
    parameter integer index=0,
    parameter integer num_periods = 10,
    parameter real precision = 1e-15
) (
    input clk_i,
    input real t_lo_val,
    input real t_hi_val,
    output reg done
);
    // include anasymod control functions
    `include "anasymod.sv"

    // variable declaration
    integer i;
    real t_last_rise, t_rise;
    real t_last_fall, t_fall;
    real t_dur_lo, t_dur_hi;

    // convenience function
    function integer isclose (
        input real meas,
        input real expct,
        input real abstol
    );
        isclose = ((expct-abstol)<=meas) && (meas<=(expct+abstol));
    endfunction

    // main logic
    initial begin
        done = 1'b0;
        wait_emu_reset();

        // get the time of the first rising edge
        @(posedge clk_i);
        #(1e-9*1s);
        t_last_rise = get_emu_time();

        // get the time of the first falling edge
        @(negedge clk_i);
        #(1e-9*1s);
        t_last_fall = get_emu_time();

        // check several periods
        for (i=0; i<num_periods; i=i+1) begin
            // check the low duration
            @(posedge clk_i);
            #(1e-9*1s);
            t_rise = get_emu_time();
            t_dur_lo = t_rise - t_last_fall;
            if (!isclose(t_dur_lo, t_lo_val, precision)) begin
                $error("[osc_%0d] Low duration out of spec: %0e", index, t_dur_lo);
            end else begin
                $display("[osc_%0d] Low duration in spec: %0e", index, t_dur_lo);
            end
            t_last_rise = t_rise;

            // check the high duration
            @(negedge clk_i);
            #(1e-9*1s);
            t_fall = get_emu_time();
            t_dur_hi = t_fall - t_last_rise;
            if (!isclose(t_dur_hi, t_hi_val, precision)) begin
                $error("[osc_%0d] High duration out of spec: %0e", index, t_dur_hi);
            end else begin
                $display("[osc_%0d] High duration in spec: %0e", index, t_dur_hi);
            end
            t_last_fall = t_fall;
        end

	    // mark the test as complete
	    done = 1'b1;
    end
endmodule
