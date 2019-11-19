from anasymod.templates.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.generators.gen_api import SVAPI, ModuleInst
from anasymod.structures.structure_config import StructureConfig
from anasymod.sim_ctrl.ctrlifc_datatypes import DigitalSignal


class ModuleClkManager(JinjaTempl):
    """
    This is the generator for clk_gen.sv wrapper.
    """
    def __init__(self, scfg: StructureConfig):
        super().__init__(trim_blocks=True, lstrip_blocks=True)

        #####################################################
        # Create module interface
        #####################################################
        self.module_ifc = SVAPI()

        module = ModuleInst(api=self.module_ifc, name="clk_gen")
        module.add_inputs(scfg.clk_i)
        module.add_outputs(scfg.clk_d)
        module.add_outputs(scfg.clk_m)
        module.generate_header()

        #####################################################
        # Instantiate clk wizard
        #####################################################
        self.clk_wiz_inst = SVAPI()

        clk_wiz = ModuleInst(api=self.clk_wiz_inst, name='clk_wiz_0')
        clk_wiz.add_inputs(scfg.clk_i, connections=scfg.clk_i)

        # handled by emu clk generator
        for k, port in enumerate(scfg.clk_m + scfg.clk_d):
            clk_wiz.add_output(DigitalSignal(abspath=None, width=1, name=f'clk_out{k + 1}'), connection=port)

        clk_wiz.add_input(DigitalSignal(abspath=None, width=1, name='reset'), connection=r"1'b0")
        clk_wiz.add_output(DigitalSignal(abspath=None, width=1, name='locked'), DigitalSignal(abspath=None, width=1, name='locked'))

        clk_wiz.generate_instantiation()

    TEMPLATE_TEXT = '''
`timescale 1ns/1ps

`default_nettype none
{{subst.module_ifc.text}}

`ifdef SIMULATION_MODE_MSDSL
	// emulator clock sequence
	logic emu_clk_state = 1'b0;
	initial begin
		// since the reset signal is initially "1", this delay+posedge will
		// cause the MSDSL templates to be reset
	    #((0.5*`DT_MSDSL)*1s);
	    emu_clk_state = 1'b1;

	    // clock runs forever
	    forever begin
	        #((0.5*`DT_MSDSL)*1s);
	        emu_clk_state = ~emu_clk_state;
	    end
	end
	
	// output assignment
	assign emu_clk_2x = emu_clk_state;
	
`else
	logic locked;

    {{subst.clk_wiz_inst.text}}

`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule
`default_nettype wire
'''

def main():
    print(ModuleClkManager(scfg=StructureConfig(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()