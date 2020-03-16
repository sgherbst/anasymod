module gen_emu_clks #(
    parameter integer n=2
) (
    (* dont_touch="true" *) input wire logic emu_clk_2x,
    (* dont_touch="true" *) output wire logic emu_clk,
    (* dont_touch="true" *) input wire logic clk_vals [n],
    (* dont_touch="true" *) output wire logic clks [n]
);

    // generate emu_clk
    logic emu_clk_unbuf = 0;
    always @(posedge emu_clk_2x) begin
        emu_clk_unbuf <= ~emu_clk_unbuf;
    end
    `ifndef SIMULATION_MODE_MSDSL
        BUFG buf_emu_clk (.I(emu_clk_unbuf), .O(emu_clk));
    `else
        assign emu_clk = emu_clk_unbuf;
    `endif

    // generate other clocks
    logic clk_unbufs [n];
    genvar k;
    generate
        for (k=0; k<n; k=k+1) begin : gen_other
            always @(posedge emu_clk_2x) begin
                if (emu_clk_unbuf == 1'b0) begin
                    clk_unbufs[k] <= clk_vals[k];
                end else begin
                    clk_unbufs[k] <= clk_unbufs[k];
                end
            end
            `ifndef SIMULATION_MODE_MSDSL
                BUFG buf_i (.I(clk_unbufs[k]), .O(clks[k]));
            `else
                assign clks[k] = clk_unbufs[k];
            `endif
        end
    endgenerate

endmodule
