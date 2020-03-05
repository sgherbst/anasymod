`include "svreal.sv"

module sim_ctrl #(
    parameter real tau=1e-6,
    parameter real abs_tol=1e-3
) (
    input wire logic signed [24:0] v_out_vio,
    output var logic signed [24:0] v_in_vio='d0,
    output var logic go_vio=1'b0,
    output var logic rst_vio=1'b1
);
    integer k;
    real t_sim, expt_val, meas_val;

    initial begin
        // wait for emulator reset to complete
        #(10us);

        // initialize signals
        go_vio = 1'b0;
        rst_vio = 1'b1;
        v_in_vio = `FLOAT_TO_FIXED(1.0, `ANALOG_EXPONENT);
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
            $display(
                "t_sim: %0e, v_in_vio: %0f, v_out_vio: %0f",
                t_sim,
                `FIXED_TO_FLOAT(v_in_vio, `ANALOG_EXPONENT),
                `FIXED_TO_FLOAT(v_out_vio, `ANALOG_EXPONENT)
            );

            // check results
            meas_val = `FIXED_TO_FLOAT(v_out_vio, `ANALOG_EXPONENT);
            expt_val = 1.0 - $exp(-t_sim/tau);
            assert (((expt_val - abs_tol) <= meas_val) && (meas_val <= (expt_val + abs_tol))) else
                $error("Measured value is out of range.");

            // pulse the clock
            go_vio = 1'b1;
            #(1us);
            go_vio = 1'b0;
            #(1us);

            // update the time variable
            t_sim += `DT_MSDSL;
        end

        // end simulation
        $finish;
    end
endmodule
