from anasymod.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.gen_api import SVAPI
from anasymod.enums import PortDir

class ModuleClkManager(JinjaTempl):
    """
    This is the generator for clk_gen.sv wrapper.
    """
    def __init__(self, target):
        #, num_out_clks=3, ext_clk_name='ext_clk', emu_clk_name='emu_clk', dbg_clk_name='dbg_hub_clk', clk_out_name='clk_out'
        super().__init__(trim_blocks=True, lstrip_blocks=True)
        self.target = target
        self.str_cfg = target.str_cfg

        #####################################################
        # Create module interface
        #####################################################
        self.module_ifc = SVAPI()

        for port in self.str_cfg.clk_i_ports:
            port.direction = PortDir.IN
            self.module_ifc.gen_port(port)

        for port in self.str_cfg.clk_o_ports:
            port.direction = PortDir.OUT
            self.module_ifc.gen_port(port)

        for port in self.str_cfg.clk_d_ports:
            port.direction = PortDir.OUT
            self.module_ifc.gen_port(port)

        for port in self.str_cfg.clk_m_ports:
            port.direction = PortDir.OUT
            self.module_ifc.gen_port(port)

        for port in self.str_cfg.clk_g_ports:
            port.direction = PortDir.IN
            self.module_ifc.gen_port(port)

        #####################################################
        # Instantiate clk wizard
        #####################################################
        self.clk_wiz_ifc = SVAPI()

        for k, port in enumerate(self.str_cfg.clk_i_ports):
            port.connection = port.name
            self.clk_wiz_ifc.println(f".{port.name}({port.connection})")

        for k, port in enumerate(self.str_cfg.clk_o_ports + self.str_cfg.clk_m_ports + self.str_cfg.clk_d_ports + self.str_cfg.clk_g_ports):
            port.connection = port.name
            self.clk_wiz_ifc.println(f".clk_out{k+1}({port.connection})")

        #####################################################
        # Add additional attributes for instantiation of sim clk gates
        #####################################################

        self.clk_outs_zipped = zip(self.str_cfg.clk_o_ports, self.str_cfg.clk_g_ports)

    TEMPLATE_TEXT = '''
`timescale 1ns/1ps

`default_nettype none
module clk_gen(
{% for line in subst.module_ifc.text.splitlines() %}
    {{line}}{{ "," if not loop.last }}
{% endfor %}
);

`ifdef SIMULATION_MODE_MSDSL
	// emulator clock sequence
	logic emu_clk_state = 1'b1;
	initial begin
		// since the reset signal is initially "1", this delay+posedge will
		// cause the MSDSL blocks to be reset
	    #((0.5*`DT_MSDSL)*1s);
	    emu_clk_state = 1'b0;

	    // clock runs forever
	    forever begin
	        #((0.5*`DT_MSDSL)*1s);
	        emu_clk_state = ~emu_clk_state;
	    end
	end
	
	// output assignment
	assign emu_clk = emu_clk_state;
	
	{% for clk, clk_en in subst.clk_outs_zipped %}
	    ana_clkgate ana_clkgate_{{clk.name}}(.en({{clk_en.name}}), .gated({{clk.name}}), .clk({{subst.str_cfg.clk_m_ports[0].name}}));
    {% endfor %}
`else
	logic dbg_hub_clk, locked;

	clk_wiz_0 clk_wiz_0_i(
    {% for line in subst.clk_wiz_ifc.text.splitlines() %}
        {{line}},
    {% endfor %}
        .reset(1'b0),
		.locked(locked)
	);
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule
`default_nettype wire
'''

def main():
    print(ModuleClkManager(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()