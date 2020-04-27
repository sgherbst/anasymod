`include "svreal.sv"

module tb;
    // signals
    `MAKE_REAL(in_, 10.0);
    `MAKE_REAL(out, 10.0);

    // function
    model #(
       `PASS_REAL(in_, in_),
       `PASS_REAL(out, out)
    ) model_i (
        .in_(in_),
        .out(out)
    );
endmodule
