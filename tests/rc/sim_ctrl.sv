`include "svreal.sv"

module sim_ctrl #(
    `DECL_REAL(v_in),
    `DECL_REAL(v_out)
) (
    `OUTPUT_REAL(v_in),
    `INPUT_REAL(v_out)
);
    `include "anasymod.sv"

    // test parameters
    localparam real dt=0.1e-6;
    localparam real tau=1e-6;
    localparam real abs_tol=1e-3;

    // wire input
    real v_in_int = 1.0;
    assign `FORCE_REAL(v_in_int, v_in);

    // wire output
    real v_out_int;
    assign v_out_int = `TO_REAL(v_out);

    // control variables
    integer k;
    real t_sim, expt_val, meas_val;
    initial begin
        // wait for reset to finish
        wait_emu_reset();

        // walk through simulation values
        t_sim = 0.0;
        for (k=0; k<25; k=k+1) begin
            // get the emulation time
            t_sim = get_emu_time();

            // print the current simulation state
            $display("t_sim: %0e, v_in_int: %0f, v_out_int: %0f", t_sim, v_in_int, v_out_int);

            // check results
            meas_val = v_out_int;
            expt_val = v_in_int*(1.0 - $exp(-t_sim/tau));
            if (!(((expt_val - abs_tol) <= meas_val) && (meas_val <= (expt_val + abs_tol)))) begin
                $error("Measured value is out of range.");
            end

            // run emulation forward by a certain amount of time
            sleep_emu(dt);
        end

        // end simulation
        $finish;
    end
endmodule
