`include "svreal.sv"

module tb;
    // analog signals
    `MAKE_REAL(v_in, 10.0);
    `MAKE_REAL(v_out, 10.0);

    // filter
    model #(
       `PASS_REAL(v_in, v_in),
       `PASS_REAL(v_out, v_out) 
    ) model_i (
        .v_in(v_in),
        .v_out(v_out)
    );
endmodule
