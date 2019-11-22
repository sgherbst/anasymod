from anasymod.generators.gen_api import SVAPI, ModuleInst
from anasymod.templates.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.sim_ctrl.ctrlifc_datatypes import DigitalSignal, ProbeSignal, DigitalCtrlInput, DigitalCtrlOutput


class ModuleTop(JinjaTempl):
    """
    This is the generator for top.sv.
    """
    def __init__(self, target):
        super().__init__(trim_blocks=True, lstrip_blocks=True)
        scfg = target.str_cfg
        """ :type: StructureConfig """

        #####################################################
        # Add plugin specific includes
        #####################################################

        self.plugin_includes = SVAPI()
        for plugin in target.plugins:
            for include_statement in plugin.include_statements:
                self.plugin_includes.writeln(f'{include_statement}')

        #####################################################
        # Create module interface
        #####################################################
        self.module_ifc = SVAPI()

        module = ModuleInst(api=self.module_ifc, name='top')
        module.add_inputs(scfg.clk_i)
        module.generate_header()

        #####################################################
        # Instantiate clk management Module
        #####################################################

        # Add clk in signals for simulation case
        self.clk_in_sim_sigs = SVAPI()

        for clk_i in scfg.clk_i:
            self.clk_in_sim_sigs.gen_signal(io_obj=clk_i)

        # Add dbg clk signals
        self.dbg_clk_sigs = SVAPI()

        for clk_d in scfg.clk_d:
            self.dbg_clk_sigs.gen_signal(io_obj=clk_d)

        # Instantiation of clk_gen wrapper
        self.clk_gen_ifc = SVAPI()
        clk_gen = ModuleInst(api=self.clk_gen_ifc, name='clk_gen')

        for clk in scfg.clk_i + scfg.clk_m + scfg.clk_d:
            clk_gen.add_input(clk, connection=clk)
        clk_gen.generate_instantiation()

        #####################################################
        # Instantiate Ctrl Module
        #####################################################

        custom_ctrl_ios = scfg.analog_ctrl_inputs + scfg.analog_ctrl_outputs + scfg.digital_ctrl_inputs + \
                          scfg.digital_ctrl_outputs

        ctrl_ios = custom_ctrl_ios + [scfg.dec_thr_ctrl] + [scfg.reset_ctrl]

        ## Instantiate all ctrl signals
        self.inst_itl_ctlsigs = SVAPI()
        for ctrl_io in ctrl_ios:
            self.inst_itl_ctlsigs.gen_signal(io_obj=ctrl_io)

        ## Instantiate ctrl module
        self.sim_ctrl_inst_ifc = SVAPI()
        sim_ctrl_inst = ModuleInst(api=self.sim_ctrl_inst_ifc, name='sim_ctrl_gen')
        sim_ctrl_inst.add_inputs(scfg.analog_ctrl_outputs + scfg.digital_ctrl_outputs,
                                 connections=scfg.analog_ctrl_outputs + scfg.digital_ctrl_outputs)
        sim_ctrl_inst.add_outputs(scfg.analog_ctrl_inputs + scfg.digital_ctrl_inputs + [scfg.dec_thr_ctrl] +
                                  [scfg.reset_ctrl], connections=scfg.analog_ctrl_inputs + scfg.digital_ctrl_inputs +
                                                                 [scfg.dec_thr_ctrl] + [scfg.reset_ctrl])
        # add master clk to ctrl module
        sim_ctrl_inst.add_input(DigitalSignal(name='emu_clk', width=1, abspath=None), connection=DigitalSignal(name='emu_clk', width=1, abspath=None))
        sim_ctrl_inst.generate_instantiation()

        ## Assign custom ctrl signals via abs paths into design
        self.assign_custom_ctlsigs = SVAPI()
        for ctrl_io in custom_ctrl_ios:
            self.assign_custom_ctlsigs.assign_to(io_obj=ctrl_io, exp=ctrl_io.abs_path)

        #####################################################
        # Instantiate trace port Module
        ######################################################
        # ToDo: This needs cleanup once probe class is conveniently implemented

        ## Instantiate all probe signals
        self.inst_probesigs = SVAPI()
        for signal in scfg.probes:
            sig = DigitalSignal(name=signal.name, abspath=signal.abspath, width=signal.width)
            self.inst_probesigs.gen_signal(sig)

        ## Instantiate traceport module
        self.trap_inst_ifc = SVAPI()
        trap_inst = ModuleInst(api=self.trap_inst_ifc, name='trace_port_gen')
        for signal in scfg.probes:
            inst_sig = DigitalSignal(name=signal.name, abspath=signal.abspath, width=signal.width)
            trap_inst.add_input(inst_sig, connection=inst_sig)

        #Add master clk to traceport module
        trap_inst.add_input(scfg.emu_clk, connection=scfg.emu_clk)
        trap_inst.generate_instantiation()

        ## Assign probe signals via abs paths into design
        self.assign_probesigs = SVAPI()
        for signal in scfg.probes:
            sig = DigitalCtrlOutput(name=signal.name, abspath=signal.abspath, width=signal.width)
            self.assign_probesigs.assign_to(io_obj=sig, exp=sig.abs_path)

        #####################################################
        # Instantiate emu clk manager Module
        #####################################################

        # Number of output clocks
        self.num_o_clks = len(scfg.clk_o)

        # Absolute path assignments for clk_o tuples
        self.clk_out_assigns = SVAPI()
        for k, clk in enumerate(scfg.clk_o):
            self.clk_out_assigns.writeln(f'// emulated clock {k}')
            self.clk_out_assigns.writeln(f'assign clk_vals[{k}] = {clk}.__emu_clk_val;')
            self.clk_out_assigns.writeln(f'assign {clk}.__emu_clk_i = clks[{k}];')
            self.clk_out_assigns.writeln(f'assign {clk}.__emu_rst = emu_rst;')
            self.clk_out_assigns.writeln(f'assign {clk}.__emu_clk = emu_clk;')

        #####################################################
        # Instantiate emu clk manager Module
        #####################################################

        self.num_dt_reqs = len(scfg.dt_reqs)

        # Absolute path assignments for dt_reqs
        self.dt_req_assigns = SVAPI()
        for k, dt_req in enumerate(scfg.dt_reqs):
            self.dt_req_assigns.writeln(f'assign {dt_req}.__emu_dt = emu_dt;')
            self.dt_req_assigns.writeln(f'assign dt_req[{k}] = {dt_req}.__emu_dt_req;')

        #####################################################
        # Instantiate testbench
        #####################################################
        self.tb_inst_ifc = SVAPI()
        tb_inst = ModuleInst(api=self.tb_inst_ifc, name='tb')
        tb_inst.generate_instantiation()

    TEMPLATE_TEXT = '''
`timescale 1ns/1ps

{{subst.plugin_includes.text}}

`default_nettype none

`ifndef SIMULATION_MODE_MSDSL
{{subst.module_ifc.text}}
`else
module top(
);
`endif // `ifndef SIMULATION_MODE_MSDSL

// Declaration of control signals
{{subst.inst_itl_ctlsigs.text}}

// Declaration of probe signals
{{subst.inst_probesigs.text}}

// create ext_clk signal when running in simulation mode
`ifdef SIMULATION_MODE_MSDSL
    logic ext_clk;
    {% for line in subst.clk_in_sim_sigs.text.splitlines() %}
        {{line}}
    {% endfor %}
`endif // `ifdef SIMULATION_MODE_MSDSL

// debug clk declaration
{{subst.dbg_clk_sigs.text}}

// emulation clock declarations
logic emu_clk, emu_clk_2x;

// declarations for time manager
localparam integer n_dt = {{subst.num_dt_reqs}};
logic signed [((`DT_WIDTH)-1):0] dt_req [n_dt];
logic signed [((`DT_WIDTH)-1):0] emu_dt;
logic signed [((`TIME_WIDTH)-1):0] emu_time;

// declarations for emu clock generator
localparam integer n_clks = {{subst.num_o_clks}};
logic clk_vals [n_clks];
logic clks [n_clks];

// instantiate testbench
{{subst.tb_inst_ifc.text}}

// Instantiation of control wrapper
{{subst.sim_ctrl_inst_ifc.text}}

// Instantiation of traceport wrapper
{{subst.trap_inst_ifc.text}}

// Clock generator
{{subst.clk_gen_ifc.text}}

// Emu Clk generator
gen_emu_clks  #(.n(n_clks)) gen_emu_clks_i (
    .emu_clk_2x(emu_clk_2x),
    .emu_clk(emu_clk),
    .clk_vals(clk_vals),
    .clks(clks)
);

// Time manager
time_manager  #(
    .n(n_dt),
    .width(`DT_WIDTH),
    .time_width(`TIME_WIDTH)
) time_manager_i (
    .dt_req(dt_req),
    .emu_dt(emu_dt),
    .emu_clk(emu_clk),
    .emu_rst(emu_rst),
    .emu_time(emu_time)
);

// Assignment for output clks
{{subst.clk_out_assigns.text}}

//Assignment for requested time steps
{{subst.dt_req_assigns.text}}

// Assignment of custom control signals via absolute paths to design signals
{{subst.assign_custom_ctlsigs.text}}

// Assignment of probe signals via absolute paths to design signals
{{subst.assign_probesigs.text}}

// make probes needed for emulation control
//`MAKE_EMU_CTRL_PROBES;

// simulation control
`ifdef SIMULATION_MODE_MSDSL
    // stop simulation after some time
    initial begin
        #((`TSTOP_MSDSL)*1s);
        $finish;
    end

    // dump waveforms to a specified VCD file
    `define ADD_QUOTES_TO_MACRO(macro) `"macro`"
    initial begin
        $dumpfile(`ADD_QUOTES_TO_MACRO(`VCD_FILE_MSDSL));
    end
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule

`default_nettype wire
'''

def main():
    print(ModuleTop(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()