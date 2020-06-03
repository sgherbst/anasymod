from anasymod.templates.templ import JinjaTempl
from anasymod.generators.gen_api import SVAPI, ModuleInst
from anasymod.sim_ctrl.datatypes import DigitalSignal
from anasymod.structures.structure_config import StructureConfig
from anasymod.templates.zynq_gpio import TemplZynqGPIO

class ModuleUARTSimCtrl(JinjaTempl):
    def __init__(self, scfg: StructureConfig):
        super().__init__(trim_blocks=True, lstrip_blocks=True)

        ctrl_inputs = scfg.analog_ctrl_inputs + scfg.digital_ctrl_inputs
        ctrl_outputs = scfg.analog_ctrl_outputs + scfg.digital_ctrl_outputs

        #####################################################
        # Define module ios
        #####################################################
        self.module_ifc = SVAPI()
        self.zynq_gpio = TemplZynqGPIO()

        module = ModuleInst(api=self.module_ifc, name="sim_ctrl_gen")
        module.add_inputs(ctrl_outputs)
        module.add_outputs(ctrl_inputs)
        module.add_input(scfg.emu_clk)
        module.add_inouts(TemplZynqGPIO.EXT_IOS)
        module.generate_header()

        ctrl_inputs = scfg.analog_ctrl_inputs + scfg.digital_ctrl_inputs
        ctrl_outputs = scfg.analog_ctrl_outputs + scfg.digital_ctrl_outputs

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
        # FPGA sim control section
        #####################################################

        # instantiation of register map module

        self.reg_map_inst = SVAPI()

        reg_map = ModuleInst(api=self.reg_map_inst, name="reg_map")

        reg_map.add_input(io_obj=DigitalSignal(name='clk', width=1, abspath=None),
                          connection=DigitalSignal(name='emu_clk', width=1, abspath=None))

        reg_map.add_input(io_obj=self.zynq_gpio.o_ctrl, connection=self.zynq_gpio.o_ctrl)
        reg_map.add_output(io_obj=self.zynq_gpio.o_data, connection=self.zynq_gpio.o_data)
        reg_map.add_input(io_obj=self.zynq_gpio.i_ctrl, connection=self.zynq_gpio.i_ctrl)
        reg_map.add_input(io_obj=self.zynq_gpio.i_data, connection=self.zynq_gpio.i_data)

        reg_map.add_outputs(io_objs=ctrl_inputs, connections=ctrl_inputs)
        reg_map.add_inputs(io_objs=ctrl_outputs, connections=ctrl_outputs)

        reg_map.generate_instantiation()

        # instantiation of bd

        self.bd_inst = SVAPI()

        bd = ModuleInst(api=self.bd_inst, name=self.zynq_gpio.design_name)

        bd.add_output(io_obj=self.zynq_gpio.o_ctrl, connection=self.zynq_gpio.o_ctrl)
        bd.add_input(io_obj=self.zynq_gpio.o_data, connection=self.zynq_gpio.o_data)
        bd.add_output(io_obj=self.zynq_gpio.i_ctrl, connection=self.zynq_gpio.i_ctrl)
        bd.add_output(io_obj=self.zynq_gpio.i_data, connection=self.zynq_gpio.i_data)

        bd.add_inouts(io_objs=TemplZynqGPIO.EXT_IOS, connections=TemplZynqGPIO.EXT_IOS)

        bd.generate_instantiation()

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
    // Signal declaration
    logic [31:0] o_ctrl;
    logic [31:0] o_data;
    logic [31:0] i_ctrl;
    logic [31:0] i_data;

    // Instantiation of register map
    {{subst.reg_map_inst.text}}

    // Instantiation of processing system
    {{subst.bd_inst.text}}
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule

`default_nettype wire
'''