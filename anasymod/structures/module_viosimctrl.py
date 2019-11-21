from anasymod.templates.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.generators.gen_api import SVAPI, ModuleInst
from anasymod.structures.structure_config import StructureConfig
from anasymod.sim_ctrl.ctrlifc_datatypes import DigitalCtrlInput, DigitalCtrlOutput, DigitalSignal, AnalogCtrlInput, AnalogCtrlOutput

class ModuleVIOSimCtrl(JinjaTempl):
    def __init__(self, scfg: StructureConfig):
        super().__init__(trim_blocks=True, lstrip_blocks=True)

        crtl_inputs = scfg.analog_ctrl_inputs + scfg.digital_ctrl_inputs
        ctrl_outputs = scfg.analog_ctrl_outputs + scfg.digital_ctrl_outputs

        #####################################################
        # Define module ios
        #####################################################
        self.module_ifc = SVAPI()

        module = ModuleInst(api=self.module_ifc, name="sim_ctrl_gen")
        module.add_inputs(ctrl_outputs)
        module.add_outputs(crtl_inputs + [scfg.dec_thr_ctrl] + [scfg.reset_ctrl])
        module.add_input(scfg.emu_clk)

        module.generate_header()

        #####################################################
        # PC sim control section
        #####################################################

        # Custom control IOs for pc sim control module
        self.pc_sim_crtl_ifc = SVAPI()

        sim_ctrl_module = ModuleInst(api=self.pc_sim_crtl_ifc, name="sim_ctrl")
        sim_ctrl_module.add_inputs(ctrl_outputs, connections=ctrl_outputs)
        sim_ctrl_module.add_outputs(crtl_inputs, connections=crtl_inputs)

        sim_ctrl_module.generate_instantiation()

        # set number of clk cycles for initial reset
        self.rst_clkcycles = scfg.cfg.rst_clkcycles

        #####################################################
        # FPGA sim control section - Instantiate vio wizard
        #####################################################

        self.vio_wiz_inst = SVAPI()
        vio_wiz = ModuleInst(api=self.vio_wiz_inst, name="vio_0")

        for k, input in enumerate(ctrl_outputs):
            if isinstance(input, AnalogCtrlOutput):
                width = '`LONG_WIDTH_REAL'
            elif isinstance(input, DigitalCtrlOutput):
                width = input.width
            else:
                raise Exception(f"Provided signal type:{type(input)} is not supported!")

            vio_i = DigitalSignal(name=f'probe_in{k}', width=width, abspath=None)
            vio_wiz.add_input(io_obj=vio_i, connection=input)

        for k, output in enumerate([scfg.reset_ctrl] + [scfg.dec_thr_ctrl] + crtl_inputs):
            if isinstance(output, AnalogCtrlInput):
                width = '`LONG_WIDTH_REAL'
            elif isinstance(output, DigitalCtrlInput):
                width = output.width
            else:
                raise Exception(f"Provided signal type:{type(output)} is not supported!")

            vio_o = DigitalSignal(name=f'probe_out{k}', width=width, abspath=None)
            vio_wiz.add_output(io_obj=vio_o, connection=output)

        vio_wiz.add_input(io_obj=DigitalSignal(name='clk', width=1, abspath=None), connection=scfg.emu_clk)
        vio_wiz.generate_instantiation()

    TEMPLATE_TEXT = '''
`timescale 1ns/1ps

`default_nettype none
{{subst.module_ifc.text}}

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

    {% if subst.pc_sim_crtl_ifc.text is not none %} 
    //module for custom vio handling
    //NOTE: sim_ctrl module must be written and added to the project manually!!!
{{subst.pc_sim_crtl_ifc.text}}
    {% endif %}
`else
	// VIO instantiation
{{subst.vio_wiz_inst.text}}
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule
`default_nettype wire
'''

def main():
    print(ModuleVIOSimCtrl(scfg=StructureConfig(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()