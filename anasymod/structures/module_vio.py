from anasymod.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.enums import PortDir
from anasymod.gen_api import SVAPI
from anasymod.structures.structure_config import StructureConfig

class ModuleVIOManager(JinjaTempl):
    def __init__(self, str_cfg: StructureConfig):
        super().__init__(trim_blocks=True, lstrip_blocks=True)
        self.str_cfg = str_cfg

        #####################################################
        # Create module interface
        #####################################################
        self.module_ifc = SVAPI()

        vio_i_ports = self.str_cfg.vio_i_ports + [self.str_cfg.clk_m_ports[0]]
        for port in vio_i_ports:
            port.direction = PortDir.IN
            self.module_ifc.gen_port(port)

        vio_o_ports = self.str_cfg.vio_r_ports + self.str_cfg.vio_s_ports + self.str_cfg.vio_o_ports
        for port in vio_o_ports:
            port.direction = PortDir.OUT
            self.module_ifc.gen_port(port)

        #####################################################
        # Instantiate vio wizard
        #####################################################
        # set number of clk cycles for initial reset
        self.rst_clkcycles = self.str_cfg.cfg.rst_clkcycles

        self.vio_wiz_ifc = SVAPI()

        for k, port in enumerate(self.str_cfg.vio_i_ports):
            port.connection = port.name
            self.vio_wiz_ifc.println(f".probe_in{k}({port.connection})")

        for k, port in enumerate(self.str_cfg.vio_r_ports + self.str_cfg.vio_s_ports + self.str_cfg.vio_o_ports):
            port.connection = port.name
            self.vio_wiz_ifc.println(f".probe_out{k}({port.connection})")

        # add master clk to vio instantiation
        vio_clk_port = self.str_cfg.clk_m_ports[0]
        vio_clk_port.connect = vio_clk_port.name
        self.vio_wiz_ifc.println(f".clk({vio_clk_port.connection})")

    TEMPLATE_TEXT = '''
`timescale 1ns/1ps

`default_nettype none
module vio_gen (
{% for line in subst.module_ifc.text.splitlines() %}
    {{line}}{{ "," if not loop.last }}
{% endfor %}
);

`ifdef SIMULATION_MODE_MSDSL
	// reset sequence
	logic emu_rst_state = 1'b1;
	initial begin
		#((`DT_MSDSL)*{{subst.rst_clkcycles}}*1s);
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
    {% for line in subst.vio_wiz_ifc.text.splitlines() %}
        {{line}}{{ "," if not loop.last }}
    {% endfor %}
	);
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule
`default_nettype wire
'''

def main():
    print(ModuleVIOManager(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()