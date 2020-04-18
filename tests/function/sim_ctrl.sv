`include "svreal.sv"

module sim_ctrl #(
    `DECL_REAL(in_),
    `DECL_REAL(out)
) (
    `OUTPUT_REAL(in_),
    `INPUT_REAL(out)
);
    `include "anasymod.sv"

    // parameters
    localparam real m_pi = 3.1415926535;
    localparam real err_tol = 0.001;

    // wire input
    real in_int;
    assign `FORCE_REAL(in_int, in_);

    // wire output
    real out_int;
    assign out_int = `TO_REAL(out);

    // clipping to range
    function real clip(input real x, input real min, input real max);
        if (x < min) begin
            clip = min;
        end else if (x > max) begin
            clip = max;
        end else begin
            clip = x;
        end
    endfunction

    // run simulation
    real expct, sum_err_sqrd, rms_err;
    integer n_samp;
    initial begin
        // wait for emulator reset to complete
        wait_emu_reset();

        // walk through simulation values
        sum_err_sqrd = 0.0;
        n_samp = 0;
        for (in_int=-1.2*m_pi; in_int<=+1.2*m_pi; in_int = in_int + 0.05) begin
            // wait
            wait_emu_cycle();
            // compute expected output
            expct = $sin(clip(in_int, -m_pi, +m_pi));
            // print simulation state
            $display("in_int: %0f, out_int: %0f, expct: %0f", in_int, out_int, expct);
            // accumulate error
            sum_err_sqrd = sum_err_sqrd + ((expct - out_int)**2);
            n_samp = n_samp + 1;
        end

        // check result
        rms_err = $sqrt((1.0/n_samp)*sum_err_sqrd);
        $display("RMS error: %0f", rms_err);
        if (!(rms_err <= err_tol)) begin
            $error("RMS error is too high.");
        end

        // end simulation
        $finish;
    end
endmodule
