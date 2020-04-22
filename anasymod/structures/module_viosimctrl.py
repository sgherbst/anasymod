from anasymod.templates.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.generators.gen_api import SVAPI, ModuleInst
from anasymod.structures.structure_config import StructureConfig
from anasymod.sim_ctrl.datatypes import DigitalCtrlInput, DigitalCtrlOutput, DigitalSignal, AnalogCtrlInput, AnalogCtrlOutput

class ModuleVIOSimCtrl(JinjaTempl):
    def __init__(self, scfg: StructureConfig):
        super().__init__(trim_blocks=True, lstrip_blocks=True)

        ctrl_inputs = scfg.analog_ctrl_inputs + scfg.digital_ctrl_inputs
        ctrl_outputs = scfg.analog_ctrl_outputs + scfg.digital_ctrl_outputs

        #####################################################
        # Define module ios
        #####################################################
        self.module_ifc = SVAPI()

        module = ModuleInst(api=self.module_ifc, name="sim_ctrl_gen")
        module.add_inputs(ctrl_outputs)
        module.add_outputs(ctrl_inputs)
        module.add_input(scfg.emu_clk)

        module.generate_header()

        #####################################################
        # PC sim control section
        #####################################################

        ## Custom control IOs for pc sim control module
        self.pc_sim_crtl_ifc = SVAPI()

        # Only generate instantiation if there is any custom ctrl signal available
        ctrl_signals = ctrl_outputs + ctrl_inputs
        custom_ctrl_signals = []
        for ctrl_signal in ctrl_signals:
            if not ctrl_signal.name in scfg.special_ctrl_ios:
                custom_ctrl_signals.append(ctrl_signal)

        if len(custom_ctrl_signals) != 0:
            sim_ctrl_module = ModuleInst(api=self.pc_sim_crtl_ifc, name="sim_ctrl")
            for ctrl_output in ctrl_outputs:
                if ctrl_output.name not in scfg.special_ctrl_ios:
                    sim_ctrl_module.add_input(ctrl_output, connection=ctrl_output)
            for ctrl_input in ctrl_inputs:
                if ctrl_input.name not in scfg.special_ctrl_ios:
                    sim_ctrl_module.add_output(ctrl_input, connection=ctrl_input)

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

        for k, output in enumerate(ctrl_inputs):
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

    TEMPLATE_TEXT = '''\
`timescale 1ns/1ps

`include "svreal.sv"

`default_nettype none
{{subst.module_ifc.text}}

`ifdef SIMULATION_MODE_MSDSL
    // reset sequence
    logic emu_rst_state = 1'b1;    
    assign emu_rst = emu_rst_state;
    initial begin
        @(posedge emu_clk);
        #((0.1/(`EMU_CLK_FREQ))*1s);
        emu_rst_state = 1'b0;
    end

    // decimation threshold
    `ifndef DEC_THR_VAL_MSDSL
        `define DEC_THR_VAL_MSDSL 0
    `endif // `ifdef DEC_THR_VAL_MSDSL
    assign emu_dec_thr = `DEC_THR_VAL_MSDSL;

    // stall / run / sleep controls
    logic [((`TIME_WIDTH)-1):0] emu_ctrl_data_state;
    logic [3:0] emu_ctrl_mode_state;
    assign emu_ctrl_data = emu_ctrl_data_state;
    assign emu_ctrl_mode = emu_ctrl_mode_state;

    // module for custom vio handling
    // NOTE: sim_ctrl module must be written and added to the project manually!!!
{{subst.pc_sim_crtl_ifc.text}}
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