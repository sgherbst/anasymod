from anasymod.anasymod.templ import JinjaTempl
from anasymod.anasymod.structures.signal import Signal

class ModuleClkManager(JinjaTempl):
    def __init__(self):
        super().__init__(trim_blocks=True, lstrip_blocks=True)

        self.child_module =

        self.signals = {}
        self.signals['ext_clk'] = [Signal(name='ext_clk_p'), Signal(name='ext_clk_n')]
        self.signals['emu_clk'] = Signal(name='emu_clk')

        self.ios = []
        self.ios += [signal.input() for signal in self.signals['ext_clk']]
        self.ios += [self.signals['emu_clk'].output()]

    TEMPLATE_TEXT = '''   
`timescale 1ns/1ps

`default_nettype none
module clk_gen(
	//input wire logic ext_clk,
	//output wire logic emu_clk
{% for io in subst.ios %}
    {{io}}{{ "," if not loop.last }}
{% endfor %}
);

'''
'''
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
`else
	logic dbg_hub_clk, locked;
	//clk_wiz_0 clk_wiz_0_i(
	//	// input clock
	//	.clk_in1(ext_clk),
	//	// output clocks
	//	.clk_out1(emu_clk),
	//	.clk_out2(dbg_hub_clk),
	//	// other signals
	//	.reset(1'b0),
	//	.locked(locked)
	//);
	{{subst.module_clkwiz}}
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule
`default_nettype wire
    '''