from anasymod.templ import JinjaTempl
from anasymod.structures.signal_base import SignalBase
from anasymod.structures.port_base import PortBase
from anasymod.blocks.clk_wiz import TemplClkWiz
from anasymod.targets import FPGATarget
from anasymod.config import EmuConfig

class ModuleClkManager(JinjaTempl):
    def __init__(self, cfg: EmuConfig, target: FPGATarget, num_out_clks=3, ext_clk_name='ext_clk', emu_clk_name='emu_clk', dbg_clk_name='dbg_hub_clk', clk_out_name='clk_out'):
        super().__init__(trim_blocks=True, lstrip_blocks=True)
        self.prj_cfg = cfg
        self.target = target
        self.num_out_clks = num_out_clks
        self.ext_clk_name = ext_clk_name
        self.emu_clk_name = emu_clk_name

        self.clk_wiz = TemplVIO(cfg=self.prj_cfg, target=target, num_out_clks=self.num_out_clks)
        self.clk_wiz_ports = self.clk_wiz.ports

TEMPLATE_TEXT = '''
`timescale 1ns/1ps

`default_nettype none
module vio_gen #(
    parameter dec_bits = 1
)(
	input wire logic emu_clk,
	output wire logic emu_rst,
	output wire logic [(dec_bits-1):0] emu_dec_thr
);

`ifdef SIMULATION_MODE_MSDSL
	// reset sequence
	logic emu_rst_state = 1'b1;
	initial begin
		#((`DT_MSDSL)*1s);
		emu_rst_state = 1'b0;
	end

	// output assignment
	assign emu_rst = emu_rst_state;
	`ifndef DEC_THR_VAL_MSDSL
	    `define DEC_THR_VAL_MSDSL 0
	`endif // `ifdef DEC_THR_VAL_MSDSL
	assign emu_dec_thr = `DEC_THR_VAL_MSDSL;
`else
	// VIO instantiation
	vio_0 vio_0_i (
		.clk(emu_clk),
		.probe_out0(emu_rst),
		.probe_out1(emu_dec_thr)
	);
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule
`default_nettype wire
'''