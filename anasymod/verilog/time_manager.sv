module time_manager #(
    parameter integer n=-1,
    parameter integer width=-1,
    parameter integer time_width=-1
) (
    input wire logic signed [(width-1):0] dt_req [n],
    output wire logic signed [(width-1):0] emu_dt,
    output var logic signed [(time_width-1):0] emu_time,
    input wire logic emu_clk,
    input wire logic emu_rst
);
    // create array of intermediate results and assign the endpoints
    wire logic signed [(width-1):0] dt_arr [n];
    assign dt_arr[0] = dt_req[0];
    assign emu_dt = dt_arr[n-1];

    // assign intermediate results
    genvar k;
    generate
        for (k=1; k<n; k=k+1) begin
            assign dt_arr[k] = dt_req[k] < dt_arr[k-1] ? dt_req[k] : dt_arr[k-1];
        end
    endgenerate

    // calculate emulation time
    always @(posedge emu_clk) begin
        if (emu_rst == 1'b1) begin
            emu_time <= '0;
        end else begin
            emu_time <= emu_time + emu_dt;
        end
    end
endmodule