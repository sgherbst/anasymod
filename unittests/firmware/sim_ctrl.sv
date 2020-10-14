`timescale 1s/1ns

module sim_ctrl (
    output reg [7:0] a_in,
    output reg [7:0] b_in,
    output reg [7:0] mode_in,
    input [7:0] c_out
);
    `include "anasymod.sv"

    task run_test(input [7:0] a, input [7:0] b, input [7:0] mode, input [7:0] expct);
        a_in = a;
        b_in = b;
        mode_in = mode;
        #(10e-9*1s);
        $display("a=%0d,\tb=%0d,\tmode=%0d\t->\tc=%0d\t(expct=%0d)",
                 a, b, mode, c_out, expct);
        if (!(c_out === expct)) begin
            $error("Output mismatch.");
        end
        #(10e-9*1s);
    endtask

    initial begin
        // wait for reset to finish
        wait_emu_reset();

        // try out different operating modes
        run_test(12, 34, 0, 46);
        run_test(45, 10, 1, 35);
        run_test(10, 44, 2, 34);
        run_test(3, 7, 3, 21);
        run_test(9, 1, 4, 4);
        run_test(9, 1, 5, 18);
        run_test(2, 32, 6, 8);
        run_test(3, 3, 7, 24);
        run_test(56, 78, 8, 42);

        // end simulation
        $finish;
    end
endmodule