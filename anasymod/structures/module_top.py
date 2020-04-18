from anasymod.generators.gen_api import SVAPI, ModuleInst
from anasymod.templates.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.sim_ctrl.datatypes import DigitalSignal
from anasymod.util import back2fwd

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

        # Set decimation bits, and decimation threshold, and time signal width for template substitution
        self.dec_bits = target.prj_cfg.cfg.dec_bits
        self.dec_thr = target.str_cfg.dec_thr_ctrl.name

        ctrl_ios = (scfg.analog_ctrl_inputs + scfg.analog_ctrl_outputs +
                    scfg.digital_ctrl_inputs + scfg.digital_ctrl_outputs)

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

        if scfg.use_default_oscillator:
            # instantiate API
            self.def_osc_api = SVAPI()

            # generate clock and reset signals
            emu_cke = digsig('emu_cke')
            self.def_osc_api.gen_signal(emu_cke)

            # instantiate the default oscillator
            def_osc_inst = ModuleInst(
                api=self.def_osc_api,
                name='osc_model_anasymod',
                inst_name='def_osc_i'
            )
            def_osc_inst.add_output(digsig('cke'), connection=emu_cke)
            def_osc_inst.generate_instantiation()
        else:
            self.def_osc_api = None

        ######################################################
        # Manage time manager module
        ######################################################

        ## Instantiate all time manager signals

        if self.num_dt_reqs > 0:
            self.inst_timemanager_sigs = SVAPI()

            emu_dt = digsig('emu_dt', width=pcfg.cfg.dt_width)
            self.inst_timemanager_sigs.gen_signal(emu_dt)

            dt_req_sigs = []
            for derived_clk in scfg.clk_derived:
                if derived_clk.abspath_dt_req is None:
                    continue
                dt_req_sig = digsig(f'dt_req_{derived_clk.name}', width=pcfg.cfg.dt_width)
                self.inst_timemanager_sigs.gen_signal(dt_req_sig)
                dt_req_sigs.append(dt_req_sig)

            ## Instantiate time manager module
            self.time_manager_inst_ifc = SVAPI()
            time_manager_inst = ModuleInst(api=self.time_manager_inst_ifc, name='gen_time_manager')
            time_manager_inst.add_input(scfg.emu_clk, connection=scfg.emu_clk)
            time_manager_inst.add_input(scfg.reset_ctrl, connection=scfg.reset_ctrl)
            time_manager_inst.add_output(scfg.time_probe, scfg.time_probe)
            time_manager_inst.add_output(emu_dt, emu_dt)
            for dt_req_sig in dt_req_sigs:
                time_manager_inst.add_input(dt_req_sig, connection=dt_req_sig)

            time_manager_inst.generate_instantiation()
        else:
            self.inst_timemanager_sigs = None
            self.time_manager_inst_ifc = None

        ######################################################
        # Control module
        ######################################################

        self.ctrl_anasymod_inst_ifc = SVAPI()

        ctrl_anasymod_inst = ModuleInst(
            api=self.ctrl_anasymod_inst_ifc,
            name='ctrl_anasymod',
            inst_name='ctrl_anasymod_i'
        )

        ctrl_anasymod_inst.add_input(scfg.emu_ctrl_mode, connection=scfg.emu_ctrl_mode)
        ctrl_anasymod_inst.add_input(scfg.emu_ctrl_data, connection=scfg.emu_ctrl_data)
        ctrl_anasymod_inst.add_input(scfg.time_probe, connection=scfg.time_probe)
        ctrl_anasymod_inst.add_input(scfg.dec_thr_ctrl, connection=scfg.dec_thr_ctrl)
        ctrl_anasymod_inst.add_output(scfg.dec_cmp, connection=scfg.dec_cmp)

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
    initial begin
        $dumpfile("{{subst.result_path_raw}}");
        
        // Signals to be dumped as well for debug purposes
        {{subst.dump_debug_signals.text}}
        
    end
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule

`default_nettype wire
'''

def main():
    print(ModuleTop(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()
