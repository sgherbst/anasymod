from anasymod.generators.gen_api import SVAPI, ModuleInst
from anasymod.templates.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.sim_ctrl.datatypes import DigitalSignal
from anasymod.structures.structure_config import StructureConfig
from anasymod.util import back2fwd
from anasymod.enums import FPGASimCtrl
from anasymod.templates.zynq_gpio import TemplZynqGPIO

def digsig(name, width=1, signed=False):
    # convenience function to return a digital signal
    return DigitalSignal(
        name=f'{name}',
        width=width,
        signed=signed,
        abspath=''
    )

class ModuleTop(JinjaTempl):
    """
    This is the generator for top.sv.
    """
    def __init__(self, target):
        super().__init__(trim_blocks=True, lstrip_blocks=True)
        scfg = target.str_cfg
        """ :type: StructureConfig """

        pcfg = target.prj_cfg
        """ :type: EmuConfig """

        self.result_path_raw = back2fwd(target.result_path_raw)

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
        if ((target.cfg.fpga_sim_ctrl is not None) and
                (target.cfg.fpga_sim_ctrl == FPGASimCtrl.UART_ZYNQ) and
                (not pcfg.board.is_ultrascale)):
            module.add_inouts(TemplZynqGPIO.EXT_IOS)
        module.generate_header()

        #####################################################
        # Manage clks
        #####################################################

        # Add clk in signals for simulation case
        self.clk_in_sim_sigs = SVAPI()

        for clk_i in scfg.clk_i:
            self.clk_in_sim_sigs.gen_signal(io_obj=clk_i)

        # Add dbg clk signals
        self.dbg_clk_sigs = SVAPI()
        self.dbg_clk_sigs.gen_signal(io_obj=scfg.dbg_clk)

        # Instantiation of clk_gen wrapper
        self.clk_gen_ifc = SVAPI()
        clk_gen = ModuleInst(api=self.clk_gen_ifc, name='clk_gen')
        clk_gen.add_inputs(scfg.clk_i, connections=scfg.clk_i)
        clk_gen.add_output(scfg.emu_clk_2x, connection=scfg.emu_clk_2x)
        clk_gen.add_output(scfg.dbg_clk, connection=scfg.dbg_clk)
        clk_gen.add_outputs(scfg.clk_independent, connections=scfg.clk_independent)
        clk_gen.generate_instantiation()

        # Absolute path assignments for derived clks
        self.derived_clk_assigns = SVAPI()
        for k, clk in enumerate(scfg.clk_derived):
            self.derived_clk_assigns.writeln(f'// derived clock: {clk.name}')
            if clk.abspath_emu_dt is not None:
                self.derived_clk_assigns.writeln(f'assign {clk.abspath_emu_dt} = emu_dt;')
            if clk.abspath_emu_clk is not None:
                self.derived_clk_assigns.writeln(f'assign {clk.abspath_emu_clk} = emu_clk;')
            if clk.abspath_emu_rst is not None:
                self.derived_clk_assigns.writeln(f'assign {clk.abspath_emu_rst} = emu_rst;')
            if clk.abspath_dt_req is not None:
                self.derived_clk_assigns.writeln(f'assign dt_req_{clk.name} = {clk.abspath_dt_req};')
            if clk.abspath_gated_clk is not None:
                self.derived_clk_assigns.writeln(f'assign clk_val_{clk.name} = {clk.abspath_gated_clk_req};')
                self.derived_clk_assigns.writeln(f'assign {clk.abspath_gated_clk} = clk_{clk.name};')

        self.num_dt_reqs = scfg.num_dt_reqs
        self.num_gated_clks = scfg.num_gated_clks

        #####################################################
        # Manage Ctrl Module
        #####################################################

        # provide information if default oscillator was used for template evaluation
        self.use_default_oscillator = scfg.use_default_oscillator

        ctrl_ios = scfg.analog_ctrl_inputs + scfg.analog_ctrl_outputs + scfg.digital_ctrl_inputs + \
                          scfg.digital_ctrl_outputs

        ## Instantiate all ctrl signals
        self.inst_itl_ctlsigs = SVAPI()
        for ctrl_io in ctrl_ios:
            self.inst_itl_ctlsigs.gen_signal(io_obj=ctrl_io)

        ## Instantiate ctrl module
        self.sim_ctrl_inst_ifc = SVAPI()
        sim_ctrl_inst = ModuleInst(api=self.sim_ctrl_inst_ifc, name='sim_ctrl_gen')
        sim_ctrl_inst.add_inputs(
            scfg.analog_ctrl_outputs + scfg.digital_ctrl_outputs,
            connections=scfg.analog_ctrl_outputs + scfg.digital_ctrl_outputs
        )
        sim_ctrl_inst.add_outputs(
            scfg.analog_ctrl_inputs + scfg.digital_ctrl_inputs,
            connections=scfg.analog_ctrl_inputs + scfg.digital_ctrl_inputs
        )

        ## Wire through Zynq connections if needed
        if ((target.cfg.fpga_sim_ctrl is not None) and
                (target.cfg.fpga_sim_ctrl == FPGASimCtrl.UART_ZYNQ) and
                (not pcfg.board.is_ultrascale)):
            sim_ctrl_inst.add_inouts(TemplZynqGPIO.EXT_IOS,
                                     connections=TemplZynqGPIO.EXT_IOS)

        # add master clk to ctrl module
        emu_clk_sig = DigitalSignal(name='emu_clk', width=1, abspath=None)
        sim_ctrl_inst.add_input(emu_clk_sig, emu_clk_sig)
        sim_ctrl_inst.generate_instantiation()

        ## Assign custom ctrl signals via abs paths into design
        self.assign_custom_ctlsigs = SVAPI()
        for ctrl_input in scfg.digital_ctrl_inputs + scfg.analog_ctrl_inputs:
            if ctrl_input.abs_path is not None:
                self.assign_custom_ctlsigs.assign_to(io_obj=ctrl_input.abs_path, exp=ctrl_input.name)

        for ctrl_output in scfg.digital_ctrl_outputs + scfg.analog_ctrl_outputs:
            self.assign_custom_ctlsigs.assign_to(io_obj=ctrl_output.name, exp=ctrl_output.abs_path)

        ######################################################
        # Manage trace port Module
        ######################################################

        probes = scfg.digital_probes + scfg.analog_probes + [scfg.time_probe] + [scfg.dec_cmp]

        ## Instantiate all probe signals
        self.inst_probesigs = SVAPI()
        for probe in probes:
            self.inst_probesigs.gen_signal(probe)

        ## Instantiate traceport module
        self.num_probes = len(probes)
        self.trap_inst_ifc = SVAPI()
        trap_inst = ModuleInst(api=self.trap_inst_ifc, name='trace_port_gen')
        trap_inst.add_inputs(probes, connections=probes)
        trap_inst.add_input(scfg.emu_clk, connection=scfg.emu_clk)
        trap_inst.generate_instantiation()

        ## Assign probe signals via abs paths into design except for time probe
        self.assign_probesigs = SVAPI()
        for probe in scfg.digital_probes + scfg.analog_probes:
            self.assign_probesigs.assign_to(io_obj=probe, exp=probe.abs_path)

        ######################################################
        # Manage emulation clks Module
        ######################################################

        ## Instantiate all emulation clk signals
        self.inst_emu_clk_sigs = SVAPI()

        clk_io_pairs = []
        for derived_clk in scfg.clk_derived:
            if derived_clk.abspath_gated_clk is None:
                continue
            clk_val = digsig(f'clk_val_{derived_clk.name}')
            clk = digsig(f'clk_{derived_clk.name}')
            self.inst_emu_clk_sigs.gen_signal(clk_val)
            self.inst_emu_clk_sigs.gen_signal(clk)
            clk_io_pairs.append((clk_val, clk))

        # add default oscillator signals, in case default oscillator was used
        if self.use_default_oscillator:
            clk_val = digsig(f'clk_val_default_osc')
            clk = digsig(f'clk_default_osc')
            self.inst_emu_clk_sigs.gen_signal(clk_val)
            self.inst_emu_clk_sigs.gen_signal(clk)
            clk_io_pairs.append((clk_val, clk))

        ## Instantiate gen emulation clk module
        self.emu_clks_inst_ifc = SVAPI()

        emu_clks_inst = ModuleInst(api=self.emu_clks_inst_ifc, name="gen_emu_clks")
        emu_clks_inst.add_input(scfg.emu_clk_2x, connection=scfg.emu_clk_2x)
        emu_clks_inst.add_output(scfg.emu_clk, connection=scfg.emu_clk)

        for clk_val, clk in clk_io_pairs:
            emu_clks_inst.add_input(clk_val, connection=clk_val)
            emu_clks_inst.add_output(clk, connection=clk)

        emu_clks_inst.generate_instantiation()

        ######################################################
        # Manage default oscillator module
        ######################################################

        emu_dt = digsig('emu_dt', width=pcfg.cfg.dt_width)
        dt_req_default_osc = DigitalSignal(name=f'dt_req_default_osc', abspath='', width=pcfg.cfg.dt_width, signed=False)

        if scfg.use_default_oscillator:
            # instantiate API
            self.def_osc_api = SVAPI()

            # generate clock and reset signals

            # instantiate the default oscillator
            def_osc_inst = ModuleInst(
                api=self.def_osc_api,
                name='osc_model_anasymod',
                inst_name='def_osc_i'
            )

            emu_dt_req = digsig('emu_dt_req', width=pcfg.cfg.dt_width)

            def_osc_inst.add_output(scfg.emu_clk, connection=scfg.emu_clk)
            def_osc_inst.add_output(scfg.reset_ctrl, connection=scfg.reset_ctrl)
            def_osc_inst.add_output(emu_dt, connection=emu_dt)
            def_osc_inst.add_output(emu_dt_req, connection=dt_req_default_osc)
            def_osc_inst.add_output(digsig('cke'), connection=digsig('clk_val_default_osc'))
            def_osc_inst.generate_instantiation()
        else:
            self.def_osc_api = None

        ######################################################
        # Manage time manager Module
        ######################################################

        ## Instantiate all time manager signals
        self.inst_timemanager_sigs = SVAPI()

        self.inst_timemanager_sigs.gen_signal(emu_dt)

        dt_reqs = []
        for derived_clk in scfg.clk_derived:
            if derived_clk.abspath_dt_req is None:
                continue
            dt_req_sig = digsig(f'dt_req_{derived_clk.name}', width=pcfg.cfg.dt_width)
            self.inst_timemanager_sigs.gen_signal(dt_req_sig)
            dt_reqs.append(dt_req_sig)

        # add input for anasymod control dt request signal
        dt_req_stall = DigitalSignal(name=f'dt_req_stall', abspath='', width=pcfg.cfg.dt_width, signed=False)
        dt_reqs.append(dt_req_stall)

        # add input for dt request signal, in case a default oscillator is used
        if scfg.use_default_oscillator:
            dt_reqs.append(dt_req_default_osc)

        ## Instantiate time manager module
        self.time_manager_inst_ifc = SVAPI()
        time_manager_inst = ModuleInst(api=self.time_manager_inst_ifc, name='gen_time_manager')
        time_manager_inst.add_input(scfg.emu_clk, connection=scfg.emu_clk)
        time_manager_inst.add_input(scfg.reset_ctrl, connection=scfg.reset_ctrl)
        time_manager_inst.add_output(scfg.time_probe, scfg.time_probe)
        time_manager_inst.add_output(emu_dt, emu_dt)
        for dt_req_sig in dt_reqs:
            time_manager_inst.add_input(dt_req_sig, connection=dt_req_sig)

        time_manager_inst.generate_instantiation()

        ######################################################
        # Control module
        ######################################################

        self.ctrl_anasymod_inst_ifc = SVAPI()

        ctrl_anasymod_inst = ModuleInst(
            api=self.ctrl_anasymod_inst_ifc,
            name='ctrl_anasymod',
            inst_name='ctrl_anasymod_i'
        )

        ctrl_anasymod_inst.add_input(scfg.emu_ctrl_data, connection=scfg.emu_ctrl_data)
        ctrl_anasymod_inst.add_input(scfg.emu_ctrl_mode, connection=scfg.emu_ctrl_mode)
        ctrl_anasymod_inst.add_input(scfg.time_probe, connection=scfg.time_probe)
        ctrl_anasymod_inst.add_input(scfg.dec_thr_ctrl, connection=scfg.dec_thr_ctrl)
        ctrl_anasymod_inst.add_input(scfg.emu_clk, connection=scfg.emu_clk)
        ctrl_anasymod_inst.add_input(scfg.reset_ctrl, connection=scfg.reset_ctrl)
        ctrl_anasymod_inst.add_output(scfg.dec_cmp, connection=scfg.dec_cmp)
        ctrl_anasymod_inst.add_output(dt_req_stall, connection=dt_req_stall)

        ctrl_anasymod_inst.generate_instantiation()

        # indicate whether TSTOP_MSDSL should be used
        self.use_tstop = target.cfg.tstop is not None

        #####################################################
        # Instantiate testbench
        #####################################################
        self.tb_inst_ifc = SVAPI()
        tb_inst = ModuleInst(api=self.tb_inst_ifc, name='tb')
        tb_inst.add_inputs(scfg.clk_independent, connections=scfg.clk_independent)
        tb_inst.generate_instantiation()

        #####################################################
        # CPU debug mode
        #####################################################
        self.dump_debug_signals = SVAPI()
        if pcfg.cfg.cpu_debug_mode:
            dbg_mods_list = pcfg.cfg.cpu_debug_hierarchies
            if isinstance(dbg_mods_list, list):
                for dbg_module in dbg_mods_list:
                    if isinstance(dbg_module, list):
                        self.dump_debug_signals.writeln(f'$dumpvars({dbg_module[0]}, {dbg_module[1]});')
                    elif isinstance(dbg_module, int) and len(dbg_mods_list) == 2: # only one single debug module was provided
                        self.dump_debug_signals.writeln(f'$dumpvars({dbg_mods_list[0]}, {dbg_mods_list[1]});')
                        break
                    else:
                        raise Exception(f'ERROR: unexpected format for cpu_debug_hierarchies attribute of '
                                        f'project_config: {dbg_mods_list}, expecting a list including <depth>, '
                                        f'<path_to_module> or a lists of such a list.')
            elif not dbg_mods_list:
                self.dump_debug_signals.writeln(f'$dumpvars(0, top.tb_i);')
            else:
                raise Exception(f'ERROR: unexpected format for cpu_debug_hierarchies attribute of '
                                f'project_config: {dbg_mods_list}, expecting tuple, list or None')

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
(* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] dt_req_stall;
{% if subst.use_default_oscillator %}
(* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] dt_req_default_osc;
{% endif %}

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

{% if subst.inst_timemanager_sigs is not none %}
// declarations for time manager
{{subst.inst_timemanager_sigs.text}}
{% endif %}

// declarations for emu clock generator
{{subst.inst_emu_clk_sigs.text}}

// instantiate testbench
{{subst.tb_inst_ifc.text}}

// Instantiation of control wrapper
{{subst.sim_ctrl_inst_ifc.text}}

{% if subst.num_probes !=0 %}
// Instantiation of traceport wrapper
{{subst.trap_inst_ifc.text}}
{% endif %}

// Clock generator
{{subst.clk_gen_ifc.text}}

// Emulation Clks Generator
{{subst.emu_clks_inst_ifc.text}}

{% if subst.def_osc_api is not none %}
// Default oscillator
{{subst.def_osc_api.text}}
{% endif %}

{% if subst.time_manager_inst_ifc.text is not none %}
// Time manager
{{subst.time_manager_inst_ifc.text}}
{% endif %}

// control signals
{{subst.ctrl_anasymod_inst_ifc.text}}

// Assignment for derived clks
{{subst.derived_clk_assigns.text}}

// Assignment of custom control signals via absolute paths to design signals
{{subst.assign_custom_ctlsigs.text}}

{% if subst.num_probes !=0 %}
// Assignment of probe signals via absolute paths to design signals
{{subst.assign_probesigs.text}}
{% endif %}

// simulation control
`ifdef SIMULATION_MODE_MSDSL
    {% if subst.use_tstop %}
    // stop simulation after a predefined amount of emulation time
    localparam longint tstop_uint = (`TSTOP_MSDSL) / (`DT_SCALE);
    always @(emu_time) begin
        if (emu_time >= tstop_uint) begin
            $display("Ending simulation at emu_time=%e", emu_time*(`DT_SCALE));
            $finish;
        end
    end
    {% endif %}
    // dump waveforms to a specified VCD file
    `define ADD_QUOTES_TO_MACRO(macro) `"macro`"
    initial begin
        $dumpfile(`ADD_QUOTES_TO_MACRO({{subst.result_path_raw}}));
        
        // Signals to be dumped as well for debug purposes
        {{subst.dump_debug_signals.text}}
        
    end
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule

`default_nettype wire
'''

def main():
    pass

if __name__ == "__main__":
    main()
