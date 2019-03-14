from anasymod.templ import JinjaTempl
from anasymod.structures.signal_base import SignalBase
from anasymod.structures.port_base import PortIN, PortOUT
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

        self.clk_wiz = TemplClkWiz(target=target, num_out_clks=self.num_out_clks)
        self.clk_wiz_ports = self.clk_wiz.ports

        # Add signals for input clk
        if isinstance(self.target.prj_cfg.board.clk_pin, list):
            if len(self.target.prj_cfg.board.clk_pin) == 2:
                clk_in_ports = ['clk_in1_p', 'clk_in1_n']
                ext_clk_name = [f"{ext_clk_name}_p", f"{ext_clk_name}_n"]
            elif len(self.target.prj_cfg.board.clk_pin) == 1:
                clk_in_ports = ['clk_in1']
                ext_clk_name = [ext_clk_name]
            else:
                raise ValueError(
                    f"Wrong number of pins provided for boards parameter 'clk_pin', expecting 1 or 2, provided:{len(self.target.prj_cfg.board.cfg['clk_pin'])}")
        else:
            raise ValueError(
                f"Wrong type for boards parameter 'clk_pin', expecting list, provided:{type(self.target.prj_cfg.board.cfg['clk_pin'])}")



        self.signals = {
            'emu_clk' : SignalBase(name=emu_clk_name),
            'dbg_clk' : SignalBase(name=dbg_clk_name)
        }

        self.clk_wiz_ports['clk_out1'].connect(self.signals['emu_clk'])
        self.clk_wiz_ports['clk_out2'].connect(self.signals['dbg_clk'])

        for signal_name, port_name in zip(ext_clk_name, clk_in_ports):
            self.signals[signal_name] = SignalBase(name=signal_name)
            self.clk_wiz_ports[port_name].connect(self.signals[signal_name])

        for k in range(num_out_clks-1):
            self.signals[f"out_clk{k+3}"] = SignalBase(name=f"{clk_out_name}{k+3}")
            self.clk_wiz_ports[f"clk_out{k+3}"].connect(self.signals[f"out_clk{k+3}"])

            self.signals[f"out_clk{k+3}_en"] = SignalBase(name=f"{clk_out_name}{k+3}_en")
            self.clk_wiz_ports[f"clk_out{k+3}_ce"].connect(self.signals[f"out_clk{k+3}_en"])

        ####################################################
        # Add module ports
        ####################################################
        self.ports = {}
        """ type : {PortBase}"""

        self.gen_ports()
        # Combine additional out clks with appropriate enable signals
        self.clk_outs_zipped = zip(self.ports['output_clks'], self.ports['output_clks_en'])

    def gen_ports(self):
        # Add ports for input clk
        if isinstance(self.target.prj_cfg.board.cfg['clk_pin'], list):
            if len(self.target.prj_cfg.board.cfg['clk_pin'])==2:
                clk_in_ports = [f"{self.ext_clk_name}_p", f"{self.ext_clk_name}_n"]
            elif len(self.target.prj_cfg.board.cfg['clk_pin'])==1:
                clk_in_ports = [self.ext_clk_name]
            else:
                raise ValueError(f"Wrong number of pins provided for boards parameter 'clk_pin', expecting 1 or 2, provided:{len(self.target.prj_cfg.board.cfg['clk_pin'])}")
        else:
            raise ValueError(f"Wrong type for boards parameter 'clk_pin', expecting list, provided:{type(self.target.prj_cfg.board.cfg['clk_pin'])}")

        self.ports['input_clks'] = []
        for port in clk_in_ports:
            self.ports['input_clks'].append(PortIN(name=port))

        # Add port for main clk
        self.ports['main_clk'] = [PortOUT(name=self.emu_clk_name)]

        # Add ports for additional output clks
        self.ports['output_clks'] = []
        for k in range(1, self.num_out_clks):
            self.ports[f'output_clks'].append(PortOUT(name=f'clk_out{k+2}'))

        # Add ports for additional output clks
        self.ports['output_clks_en'] = []
        for k in range(1, self.num_out_clks):
            self.ports[f'output_clks_en'].append(PortIN(name=f'clk_out{k+2}_en'))

    TEMPLATE_TEXT = '''
`timescale 1ns/1ps

`default_nettype none
module clk_gen(
{% for _, v in subst.ports.items() %}
    {% for port in v %}
        {{port.render_mod_port()}}{{ "," if not loop.last }}
    {% endfor %}
{% endfor %}
);

`ifdef SIMULATION_MODE_MSDSL
	// emulator clock sequence
	logic emu_clk_state = 1'b0;
	initial begin
		// since the reset signal is initially "1", this delay+posedge will
		// cause the MSDSL blocks to be reset
	    #((0.5*`DT_MSDSL)*1s);
	    emu_clk_state = 1'b1;

	    // clock runs forever
	    forever begin
	        #((0.5*`DT_MSDSL)*1s);
	        emu_clk_state = ~emu_clk_state;
	    end
	end
	
	// output assignment
	assign emu_clk = emu_clk_state;
	
	{% for clk, clk_en in subst.clk_outs_zipped %}
	    ana_clkgate ana_clkgate_{{clk.name}}(.en({{clk_en.name}}), .gated({{clk.name}}), .clk({{subst.ports['main_clk'][0].name}}));
    {% endfor %}
`else
	logic dbg_hub_clk, locked;

	clk_wiz_0 clk_wiz_0_i(
	{% for k, v in subst.clk_wiz_ports.items() %}
        .{{v.render_inst_port()}}({{v.connection}}),
    {% endfor %}
        .reset(1'b0),
		.locked(locked)
	);
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule
`default_nettype wire
'''

def main():
    print(ModuleClkManager(cfg=EmuConfig(root='test', cfg_file=''), target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()