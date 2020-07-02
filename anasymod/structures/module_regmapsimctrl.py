from copy import deepcopy
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

        o_ctrl = DigitalSignal(name='o_ctrl', width=32, abspath=None)
        module.add_input(io_obj=o_ctrl)
        o_data = DigitalSignal(name='o_data', width=32, abspath=None)
        module.add_output(io_obj=o_data)
        i_ctrl = DigitalSignal(name='i_ctrl', width=32, abspath=None)
        module.add_input(io_obj=i_ctrl)
        i_data = DigitalSignal(name='i_data', width=32, abspath=None)
        module.add_input(io_obj=i_data)

        # Add I/Os to Design (probes and Conrol Parameters)
        module.add_outputs(io_objs=crtl_inputs, connections=crtl_inputs)
        module.add_inputs(io_objs=ctrl_outputs, connections=ctrl_outputs)

        module.generate_header()

        #####################################################
        # Initialize Default Values for ControlInfrastructure Parameters
        #####################################################

        self.init_ctrlios = SVAPI()

        for parameter in crtl_inputs:
            default_signal = deepcopy(parameter)
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
            if probe.o_addr is not None:
                self.probes_combomux_cases.writeln(f"'d{probe.o_addr}: o_data_reg = {probe.name};")

        #####################################################
        # Combo mux for Probes section
        #####################################################

        # instantiation of register map module
        self.params_regmap = SVAPI()

        for param in crtl_inputs:
            # create a reg signal
            reg_signal = deepcopy(param)
            reg_signal.name = f'{param.name}_reg'
            self.params_regmap.gen_signal(reg_signal)

            # assign to the reg signal
            self.params_regmap.writeln(f'assign {param.name} = {param.name}_reg;')

            # update the reg signal
            self.params_regmap.writeln(f'''\
always @(posedge clk) begin
    if (i_rst == 'b1) begin
        {param.name}_reg <= {param.name}_def; // use VIO defaults
    end else if ((i_valid == 1'b1) && (i_addr == 'd{param.i_addr})) begin
        {param.name}_reg <= i_data;
    end else begin
        {param.name}_reg <= {param.name}_reg;
    end
end''')

    TEMPLATE_TEXT = '''
`timescale 1ns/1ps

`default_nettype none

{{subst.module_ifc.text}}

    // break out signals in o_ctrl    
    logic [7:0] o_addr;
    assign o_addr = o_ctrl[7:0];
    
    // break out signals in i_ctrl
    logic i_rst;
    assign i_rst = i_ctrl[31];
    
    logic i_valid;
    assign i_valid = i_ctrl[30];
    
    logic [7:0] i_addr;
    assign i_addr = i_ctrl[7:0];
    
    // Initial values for parameters
    {{subst.init_ctrlios.text}}

	// combo mux for reading outputs from design
	logic [31:0] o_data_reg;
	assign o_data = o_data_reg;
	always @* begin
		case (o_addr)
{{subst.probes_combomux_cases.text}}
		    default: o_data_reg = 0;
		endcase
	end

	// register map for writing to the inputs of the design
	{{subst.params_regmap.text}}

endmodule
`default_nettype wire
'''