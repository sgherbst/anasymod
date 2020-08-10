`timescale 1s/1ns

module sim_ctrl (
    input clk_i,
    output reg [31:0] t_lo,
    output reg [31:0] t_hi
);
    `include "anasymod.sv"

    // set t_lo and t_hi
    parameter real t_lo_val = 0.123e-12;
    parameter real t_hi_val = 0.234e-12;
    initial begin
        t_lo = t_lo_val/(`DT_SCALE);
        t_hi = t_hi_val/(`DT_SCALE);
    end

    // checking of the low and high periods
    integer i;
    real t_last_rise, t_rise;
    real t_last_fall, t_fall;
    real t_dur_lo, t_dur_hi;

    function integer isclose (
        input real meas,
        input real expct,
        input real abstol
    );
        isclose = ((expct-abstol)<=meas) && (meas<=(expct+abstol));
    endfunction

    initial begin
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
	for (i=0; i<10; i=i+1) begin
            // check the low duration
            @(posedge clk_i);
            #(1e-9*1s);
            t_rise = get_emu_time();
	    t_dur_lo = t_rise - t_last_fall;
	    if (!isclose(t_dur_lo, t_lo_val, 1e-15)) begin
                $error("%0d(a) Low duration out of spec: %0e", i, t_dur_lo);
	    end else begin
                $display("%0d(a) Low duration in spec: %0e", i, t_dur_lo);
	    end
            t_last_rise = t_rise;

            // check the high duration
            @(negedge clk_i);
            #(1e-9*1s);
            t_fall = get_emu_time();
            t_dur_hi = t_fall - t_last_rise;
	    if (!isclose(t_dur_hi, t_hi_val, 1e-15)) begin
                $error("%0d(b) High duration out of spec: %0e", i, t_dur_hi);
	    end else begin
                $display("%0d(b) High duration in spec: %0e", i, t_dur_hi);
	    end
            t_last_fall = t_fall;
        end

	// finish the simulation
	$finish;
    end
endmodule
