from anasymod.templ import JinjaTempl
from anasymod.gen_api import SVAPI, ModuleInst
from anasymod.targets import Target
from anasymod.sim_ctrl.ctrlifc_datatypes import DigitalCtrlInput, DigitalCtrlOutput, DigitalSignal, AnalogSignal, AnalogCtrlInput, AnalogCtrlOutput

class ModuleRegMapSimCtrl(JinjaTempl):
    def __init__(self, target: Target):
        super().__init__(trim_blocks=True, lstrip_blocks=True)
        scfg = target.str_cfg



        #custom_ctrl_ios = scfg.analog_ctrl_inputs + scfg.analog_ctrl_outputs + scfg.digital_ctrl_inputs + \
        #                  scfg.digital_ctrl_outputs

        #ctrl_ios = custom_ctrl_ios + scfg.dec_thr_ctrl + scfg.reset_ctrl

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
        # Initialize Default Values for Control Parameters
        #####################################################

        self.init_ctrlios = SVAPI()

        for parameter in crtl_inputs:
            default_signal = parameter
            default_signal.name = str(default_signal.name) + '_def'
            self.init_ctrlios._gen_signal(io_obj=default_signal)
            self.init_ctrlios.assign_to(io_obj=default_signal, exp=default_signal.init_value)

        #####################################################
        # Combo mux for Probes section
        #####################################################

        # instantiation of register map module
        self.probes_combomux_cases = SVAPI()

        for probe in crtl_inputs:
            if isinstance(probe, (DigitalSignal, DigitalCtrlInput, DigitalCtrlOutput)):
                self.probes_combomux_cases.println(f"'d{int(probe.i_addr, i_addr.width)}: o_data = {probe.name};")
            elif isinstance(probe, (AnalogSignal, AnalogCtrlOutput,AnalogCtrlInput)):
                self.probes_combomux_cases.println(f"'d{int(probe.i_addr, i_addr.width)}: begin")
                self.probes_combomux_cases.println(f"`FORCE_REAL({probe.name}, o_data);")
                self.probes_combomux_cases.println(f"end")

            #'d0: o_data = a;
            #'d1: o_data = b;
            #// ...
            #default: o_data = a;

        #####################################################
        # Combo mux for Probes section
        #####################################################

        # instantiation of register map module
        self.params_regmap_conditions = SVAPI()



    TEMPLATE_TEXT = '''
`timescale 1ns/1ps

`default_nettype none

{{subst.module_ifc.text}}

    // Initial values for parameters
    {{subst.init_ctrlios}}  
    wire o_data_def;
    assign o_data_def = 0;

	// combo mux for reading outputs from design
	always @* begin
		case (o_addr)
		    {{subst.probes_combomux_cases}}
		    default: o_data = o_data_def;
		endcase
	end

	// register map for writing to the inputs of the design
	{{subst.params_regmap_conditions}}
	always @(posedge clk) begin	
		if (rst == 'b1) begin
			c <= c_def; // use VIO defaults
		end else if (i_addr == 'd0) begin 
			c <= i_data;
		end else begin
			c <= c;
		end
	end 

	always @(posedge clk) begin
		if (rst == 'b1) begin
			d <= d_def; // use VIO defaults
		end else if (i_addr == 'd1) begin 
			d <= i_data;
		end else begin
			d <= d;
		end
	end 

endmodule

HIER ALTES

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
    sim_ctrl sim_ctrl_i (
    {% for line in subst.pc_sim_crtl_ifc.text.splitlines() %}
        {{line}}{{ "," if not loop.last }}
    {% endfor %}
    )
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
    print(ModuleVIOManager(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()