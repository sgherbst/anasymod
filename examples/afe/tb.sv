`timescale 1s/1ns

`include "svreal.sv"

`define MAKE(arg1, arg2, k) `MAKE_REAL(``arg1``_``k``, arg2)
`define PASS(arg1, arg2, k) `PASS_REAL(``arg1``_``k``, ``arg2``_``k``)
`define CONNECT(arg1, arg2, k) .``arg1``_``k``(``arg2``_``k``)
`define NONLIN(arg1, arg2, k) \
    nonlin #( \
        `PASS_REAL(in_, ``arg1``_``k``), \
        `PASS_REAL(out, ``arg2``_``k``) \
    ) ``nonlin``_``arg1``_``arg2``_``k`` ( \
        .in_(``arg1``_``k``), \
        .out(``arg2``_``k``) \
    )

`define REPLICATE_MACRO_SEMICOLON(name, arg1, arg2) \
    `name(arg1, arg2, 0); \
    `name(arg1, arg2, 1); \
    `name(arg1, arg2, 2); \
    `name(arg1, arg2, 3)

`define REPLICATE_MACRO_COMMA(name, arg1, arg2) \
    `name(arg1, arg2, 0), \
    `name(arg1, arg2, 1), \
    `name(arg1, arg2, 2), \
    `name(arg1, arg2, 3)

module tb;
    // parameters
    localparam real ui = 62.5e-12;
    localparam real dtmax = 31.25e-12;

    // uncomment to force a maximum timestep
    // (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] ext_dt;
    // assign ext_dt = 25e-12*(1e15);

    // emulator control infrastructure
    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] dt_req;
    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] emu_dt;
    (* dont_touch = "true" *) logic emu_clk;
    (* dont_touch = "true" *) logic emu_rst;

    // PRBS signals
    logic prbs_o;
    logic [20:0] sr;

    // oscillator period signals
    (* dont_touch = "true" *) `MAKE_REAL(tlo, ui);
    (* dont_touch = "true" *) `MAKE_REAL(thi, ui);
    `MAKE_REAL(osc_period, ui);

    // oscillator signals
    logic clk_en;

    // dt scaling signals
    `MAKE_REAL(dt, ui);
    `MAKE_REAL(dt_rel, 1.1);

    // real-valued in signal chain
    `REPLICATE_MACRO_SEMICOLON(MAKE, chan_o, 1.5);
    `REPLICATE_MACRO_SEMICOLON(MAKE, ctle1_o, 1.5);
    `REPLICATE_MACRO_SEMICOLON(MAKE, nl1_o, 1.5);
    `REPLICATE_MACRO_SEMICOLON(MAKE, ctle2_o, 1.5);
    `REPLICATE_MACRO_SEMICOLON(MAKE, nl2_o, 1.5);
    `REPLICATE_MACRO_SEMICOLON(MAKE, ctle3_o, 1.5);
    `REPLICATE_MACRO_SEMICOLON(MAKE, nl3_o, 1.5);

    // PRBS (adapted from DaVE)
    always @(posedge emu_clk) begin
        if (emu_rst) begin
            sr <= '1;
        end else if (clk_en) begin
            sr[20:1] <= sr[19:0];
            sr[0] <= sr[20] ^ sr[1];
        end else begin
            sr <= sr;
        end
    end
    assign prbs_o = sr[6];

    // Timestep generator

    unfm #(
        `PASS_REAL(min_val, tlo),
        `PASS_REAL(max_val, thi),
        `PASS_REAL(out, osc_period)
    ) unfm_i (
        .min_val(tlo),
        .max_val(thi),
        .out(osc_period),
        .emu_clk(emu_clk),
        .emu_rst(emu_rst)
    );

    // Oscillator

    osc #(
        `PASS_REAL(period, osc_period)
    ) osc_i (
        .period(osc_period),
        .dt_req(dt_req),
        .emu_dt(emu_dt),
        .clk_en(clk_en),
        .emu_clk(emu_clk),
        .emu_rst(emu_rst)
    );

    // Generate dt and dt_rel signals
    // TODO: cleanup

    logic signed [16:0] emu_dt_sint;
    assign emu_dt_sint = emu_rst ? 0 : {1'b0, emu_dt[15:0]};  // 65.535 ps full scale
    `INT_TO_REAL(emu_dt_sint, 17, emu_dt_real);
    `MUL_CONST_INTO_REAL((`DT_SCALE), emu_dt_real, dt);
    `MUL_CONST_INTO_REAL(((`DT_SCALE)/dtmax), emu_dt_real, dt_rel);

    // TX driver

    `MAKE_CONST_REAL(1.0, txp);
    `MAKE_CONST_REAL(-1.0, txn);
    `MAKE_SHORT_REAL(tx_drv_o, 1.1);  // short real used to reduce DSP utilization
    `ITE_INTO_REAL(prbs_o, txp, txn, tx_drv_o);

    // channel

    channel #(
        `PASS_REAL(dt, dt),
        `PASS_REAL(in_, tx_drv_o),
        `REPLICATE_MACRO_COMMA(PASS, out, chan_o)
    ) channel_i (
        .dt(dt),
        .in_(tx_drv_o),
        `REPLICATE_MACRO_COMMA(CONNECT, out, chan_o),
        .emu_clk(emu_clk),
        .emu_rst(emu_rst)
    );

    // ctle1

    ctle1 #(
        `PASS_REAL(dt, dt_rel),
        `REPLICATE_MACRO_COMMA(PASS, in, chan_o),
        `REPLICATE_MACRO_COMMA(PASS, out, ctle1_o)
    ) ctle1_i (
        .dt(dt_rel),
        `REPLICATE_MACRO_COMMA(CONNECT, in, chan_o),
        `REPLICATE_MACRO_COMMA(CONNECT, out, ctle1_o),
        .emu_clk(emu_clk),
        .emu_rst(emu_rst)
    );

    // nonlin

    `REPLICATE_MACRO_SEMICOLON(NONLIN, ctle1_o, nl1_o);

    // ctle2

    ctle2 #(
        `PASS_REAL(dt, dt_rel),
        `REPLICATE_MACRO_COMMA(PASS, in, nl1_o),
        `REPLICATE_MACRO_COMMA(PASS, out, ctle2_o)
    ) ctle2_i (
        .dt(dt_rel),
        `REPLICATE_MACRO_COMMA(CONNECT, in, nl1_o),
        `REPLICATE_MACRO_COMMA(CONNECT, out, ctle2_o),
        .emu_clk(emu_clk),
        .emu_rst(emu_rst)
    );

    // nonlin2

    `REPLICATE_MACRO_SEMICOLON(NONLIN, ctle2_o, nl2_o);

    // ctle3

    ctle3 #(
        `PASS_REAL(dt, dt_rel),
        `REPLICATE_MACRO_COMMA(PASS, in, nl2_o),
        `REPLICATE_MACRO_COMMA(PASS, out, ctle3_o)
    ) ctle3_i (
        .dt(dt_rel),
        `REPLICATE_MACRO_COMMA(CONNECT, in, nl2_o),
        `REPLICATE_MACRO_COMMA(CONNECT, out, ctle3_o),
        .emu_clk(emu_clk),
        .emu_rst(emu_rst)
    );

    // nonlin3

    `REPLICATE_MACRO_SEMICOLON(NONLIN, ctle3_o, nl3_o);

endmodule
