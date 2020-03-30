`include "svreal.sv"

module sim_ctrl #(
    `DECL_REAL(v_in),
    `DECL_REAL(v_out)
) (
    `OUTPUT_REAL(v_in),
    `INPUT_REAL(v_out),
    output reg go_vio,
    output reg rst_vio
);
    // test parameters
    localparam real tau=1e-6;
    localparam real abs_tol=1e-3;

    // wire input
    real v_in_int;
    assign `FORCE_REAL(v_in_int, v_in);

    // wire output
    real v_out_int;
    assign v_out_int = `TO_REAL(v_out);

    // control variables
    integer k;
    real t_sim, expt_val, meas_val;
    initial begin
        // wait for emulator reset to complete
        #(10us);

        // initialize signals
        go_vio = 1'b0;
        rst_vio = 1'b1;
        v_in_int = 1.0;
        #(1us);

        // pulse the clock
        go_vio = 1'b1;
        #(1us);
        go_vio = 1'b0;
        #(1us);

        // release from reset
        rst_vio = 1'b0;
        #(1us);

        // walk through simulation values
        t_sim = 0.0;
        for (k=0; k<25; k=k+1) begin
            // print the current simulation state
            $display("t_sim: %0e, v_in_int: %0f, v_out_int: %0f", t_sim, v_in_int, v_out_int);

            // check results
            meas_val = v_out_int;
            expt_val = 1.0 - $exp(-t_sim/tau);
            if (!(((expt_val - abs_tol) <= meas_val) && (meas_val <= (expt_val + abs_tol)))) begin
                $error("Measured value is out of range.");
            end

            // pulse the clock
            go_vio = 1'b1;
            #(0.5us);
            go_vio = 1'b0;
            #(0.5us);

            // update the time variable
            t_sim = t_sim + (`DT_MSDSL);
        end

        // end simulation
        $finish;
    end
endmodule
