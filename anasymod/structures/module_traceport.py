from anasymod.templates.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.generators.gen_api import SVAPI, ModuleInst
from anasymod.structures.structure_config import StructureConfig
from anasymod.sim_ctrl.datatypes import DigitalSignal

class ModuleTracePort(JinjaTempl):
    def __init__(self, scfg: StructureConfig):
        super().__init__(trim_blocks=True, lstrip_blocks=True)
        probes = scfg.digital_probes + scfg.analog_probes + [scfg.time_probe] + [scfg.dec_cmp]

        #####################################################
        # Define module ios
        #####################################################

        self.module_ifc = SVAPI()
        module = ModuleInst(api=self.module_ifc, name="trace_port_gen")
        # Add probe signals
        module.add_inputs(probes)

        # Add master clk
        module.add_input(scfg.emu_clk)

        module.generate_header()

        #####################################################
        # FPGA sim control section - Instantiate vio wizard
        #####################################################

        self.ila_wiz_inst = SVAPI()
        ila_wiz = ModuleInst(api=self.ila_wiz_inst, name="ila_0")

        # Add probe signals
        for k, signal in enumerate(probes):
            ila_wiz.add_input(DigitalSignal(name=f'probe{k}', abspath=None, width=signal.width), connection=signal)

        # Add master clk
        ila_wiz.add_input(DigitalSignal(name='clk', abspath=None, width=1), connection=scfg.emu_clk)

        ila_wiz.generate_instantiation()

    TEMPLATE_TEXT = '''
`timescale 1ns/1ps

`default_nettype none
{{subst.module_ifc.text}}

`ifdef SIMULATION_MODE_MSDSL
    //Will be added later
`else
	// ILA instantiation
{{subst.ila_wiz_inst.text}}
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule
`default_nettype wire
'''

def main():
    print(ModuleTracePort(scfg=StructureConfig(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()