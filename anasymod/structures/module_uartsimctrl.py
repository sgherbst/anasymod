from anasymod.templates.templ import JinjaTempl
from anasymod.generators.gen_api import SVAPI, ModuleInst
from anasymod.sim_ctrl.datatypes import DigitalCtrlInput, DigitalSignal
from anasymod.structures.structure_config import StructureConfig

class ModuleUARTSimCtrl(JinjaTempl):
    def __init__(self, scfg: StructureConfig):
        super().__init__(trim_blocks=True, lstrip_blocks=True)

        custom_ctrl_ios = scfg.analog_ctrl_inputs + scfg.analog_ctrl_outputs + scfg.digital_ctrl_inputs + \
                          scfg.digital_ctrl_outputs

        crtl_inputs = scfg.analog_ctrl_inputs + scfg.digital_ctrl_inputs
        ctrl_outputs = scfg.analog_ctrl_outputs + scfg.digital_ctrl_outputs

        #####################################################
        # Define module ios
        #####################################################
        self.module_ifc = SVAPI()

        module = ModuleInst(api=self.module_ifc, name="sim_ctrl_gen")
        module.add_inputs(ctrl_outputs)
        module.add_outputs(crtl_inputs + [scfg.dec_thr_ctrl] + [scfg.reset_ctrl])
        #ToDo: after revamp of clk in structure config, adding the master clk can be cleaned up as well
        module.add_input(DigitalCtrlInput(name=scfg.clk_independent[0].name, width=1, abspath=None))

        module.generate_header()
        #ToDo: currently clk will be treated as inputs to this wrapper, might be driven from PS at one point

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
        # FPGA sim control section
        #####################################################

        # instantiation of register map module
        self.reg_map_inst = SVAPI()

        reg_map = ModuleInst(api=self.reg_map_inst, name="reg_map")

        reg_map.add_input(io_obj=DigitalSignal(name='clk', width=1, abspath=None), connection=DigitalSignal(name='emu_clk', width=1, abspath=None))

        rst = DigitalSignal(name='rst', width=1, abspath=None)
        reg_map.add_input(io_obj=rst, connection=scfg.reset_ctrl)

        i_addr = DigitalSignal(name='i_addr', width=8, abspath=None)
        reg_map.add_input(io_obj=i_addr, connection=i_addr)
        i_data = DigitalSignal(name='i_data', width=32, abspath=None)
        reg_map.add_input(io_obj=i_data, connection=i_data)
        o_addr = DigitalSignal(name='o_addr', width=8, abspath=None)
        reg_map.add_input(io_obj=o_addr, connection=o_addr)
        o_data = DigitalSignal(name='o_data', width=32, abspath=None)
        reg_map.add_output(io_obj=o_data, connection=o_data)

        reg_map.add_outputs(io_objs=crtl_inputs, connections=crtl_inputs)
        reg_map.add_inputs(io_objs=ctrl_outputs, connections=ctrl_outputs)

        reg_map.generate_instantiation()

        # instantiation of bd
        self.bd_inst = SVAPI()

        bd = ModuleInst(api=self.bd_inst, name="design_1_wrapper")

        i_addr_tri_o = DigitalSignal(name='i_addr_tri_o', width=8, abspath=None)
        i_data_tri_o = DigitalSignal(name='i_data_tri_o', width=8, abspath=None)
        o_addr_tri_o = DigitalSignal(name='o_addr_tri_o', width=8, abspath=None)
        o_data_tri_i = DigitalSignal(name='o_data_tri_i', width=8, abspath=None)
        ps_clk = DigitalSignal(name='ps_clk', width=8, abspath=None)
        reset_tri_o = DigitalSignal(name='reset_tri_o', width=8, abspath=None)


        bd.add_output(io_obj=i_addr_tri_o, connection=i_addr)
        bd.add_output(io_obj=i_data_tri_o, connection=i_data)
        bd.add_output(io_obj=o_addr_tri_o, connection=o_addr)
        bd.add_input(io_obj=o_data_tri_i, connection=o_data)
        bd.add_input(io_obj=ps_clk, connection=clk)
        # ToDo: Check direction of this clk
        bd.add_output(io_obj=reset_tri_o, connection=rst)

        bd.generate_instantiation()

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
    // Instantiation of register map
    {{subst.reg_map_inst.text}}

    // Instantiation of processing system
{{subst.bd_inst.text}}
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule
`default_nettype wire
'''

def main():
    from anasymod.config import EmuConfig
    #print(ModuleRegMapSimCtrl(scfg=StructureConfig(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())
    print(ModuleUARTSimCtrl(scfg=StructureConfig(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()