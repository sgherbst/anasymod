from anasymod.templates.templ import JinjaTempl
from anasymod.generators.gen_api import SVAPI, ModuleInst
from anasymod.sim_ctrl.datatypes import DigitalSignal


class ModuleRegMapSimCtrl(JinjaTempl):
    def __init__(self, scfg):
        super().__init__(trim_blocks=True, lstrip_blocks=True)

        crtl_inputs = scfg.analog_ctrl_inputs + scfg.digital_ctrl_inputs
        ctrl_outputs = scfg.analog_ctrl_outputs + scfg.digital_ctrl_outputs

        #####################################################
        # Define module ios
        #####################################################
        self.module_ifc = SVAPI()
        module = ModuleInst(api=self.module_ifc, name="reg_map")

        # Add clock
        clk = DigitalSignal(name='clk', width=1, abspath=None)
        module.add_input(io_obj=clk)

        # Add reset
        rst = DigitalSignal(name='rst', width=1, abspath=None)
        module.add_input(io_obj=rst)

        # Add I/Os to CPU subsystem
        i_addr = DigitalSignal(name='i_addr', width=8, abspath=None)
        module.add_input(io_obj=i_addr)
        i_data = DigitalSignal(name='i_data', width=32, abspath=None)
        module.add_input(io_obj=i_data)
        o_addr = DigitalSignal(name='o_addr', width=8, abspath=None)
        module.add_input(io_obj=o_addr)
        o_data = DigitalSignal(name='o_data', width=32, abspath=None)
        module.add_output(io_obj=o_data)

        # Add I/Os to Design (probes and Conrol Parameters)
        module.add_outputs(io_objs=crtl_inputs, connections=crtl_inputs)
        module.add_inputs(io_objs=ctrl_outputs, connections=ctrl_outputs)

        module.generate_header()
        #ToDo: currently clk will be treated as inputs to this wrapper, might be driven from PS at one point

        #####################################################
        # Initialize Default Values for ControlInfrastructure Parameters
        #####################################################

        self.init_ctrlios = SVAPI()

        for parameter in crtl_inputs:
            default_signal = parameter
            default_signal.name = str(default_signal.name) + '_def'
            self.init_ctrlios.gen_signal(io_obj=default_signal)
            self.init_ctrlios.assign_to(io_obj=default_signal, exp=default_signal.init_value)

        #####################################################
        # Combo mux for Probes section
        #####################################################

        # instantiation of register map module
        self.probes_combomux_cases = SVAPI()

        self.probes_combomux_cases.indent(quantity=3)
        for probe in ctrl_outputs:
            self.probes_combomux_cases.writeln(f"'d{probe.o_addr}: o_data = {probe.name};")

        #####################################################
        # Combo mux for Probes section
        #####################################################

        # instantiation of register map module
        self.params_regmap = SVAPI()

        for param in crtl_inputs:
            self.params_regmap.writeln(f"always @(posedge clk) begin")
            self.params_regmap.writeln(f"    if (rst == 'b1) begin")
            self.params_regmap.writeln(f"        {param.name} <= {param.name}_def; // use VIO defaults")
            self.params_regmap.writeln(f"    end else if (i_addr == 'd{param.i_addr}) begin ")
            self.params_regmap.writeln(f"        {param.name} <= i_data;")
            self.params_regmap.writeln(f"    end else begin")
            self.params_regmap.writeln(f"        {param.name} <= {param.name};")
            self.params_regmap.writeln(f"    end")
            self.params_regmap.writeln(f"end")
            self.params_regmap.writeln(f"")

    TEMPLATE_TEXT = '''
`timescale 1ns/1ps

`default_nettype none

{{subst.module_ifc.text}}

    // Initial values for parameters
    {{subst.init_ctrlios.text}}  
    wire o_data_def;
    assign o_data_def = 0;

	// combo mux for reading outputs from design
	always @* begin
		case (o_addr)
{{subst.probes_combomux_cases.text}}
		    default: o_data = o_data_def;
		endcase
	end

	// register map for writing to the inputs of the design
	{{subst.params_regmap.text}}

endmodule
`default_nettype wire
'''

def main():
    from anasymod.structures.structure_config import StructureConfig
    from anasymod.config import EmuConfig
    print(ModuleRegMapSimCtrl(scfg=StructureConfig(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()