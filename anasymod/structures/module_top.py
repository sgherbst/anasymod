from anasymod.generators.gen_api import SVAPI, ModuleInst
from anasymod.templates.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.sim_ctrl.datatypes import DigitalSignal
from anasymod.structures.structure_config import StructureConfig
from anasymod.util import back2fwd

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
        dt_req_cnt = 0
        gated_clks_cnt = 0
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
                dt_req_cnt += 1
            if clk.abspath_gated_clk is not None:
                self.derived_clk_assigns.writeln(f'assign clk_val_{clk.name} = {clk.abspath_gated_clk_req};')
                self.derived_clk_assigns.writeln(f'assign {clk.abspath_gated_clk} = clk_{clk.name};')
                gated_clks_cnt += 1

        self.num_dt_reqs = dt_req_cnt
        self.num_gated_clks = gated_clks_cnt

        #####################################################
        # Manage Ctrl Module
        #####################################################

        # Set decimation bits, and decimation threshold, and time signal width for template substitution
        self.dec_bits = target.prj_cfg.cfg.dec_bits
        self.dec_thr = target.str_cfg.dec_thr_ctrl.name

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
        for ctrl_input in scfg.digital_ctrl_inputs + scfg.analog_ctrl_inputs:
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

        gated_clk_sig_names = []

        ## Instantiate all emulation clk signals
        self.inst_emu_clk_sigs = SVAPI()

        for derived_clk in scfg.clk_derived:
            if derived_clk.abspath_gated_clk is not None:
                gated_clk_sig_names.append(derived_clk.name)

        for gated_clk_sig_name in gated_clk_sig_names:
            self.inst_emu_clk_sigs.gen_signal(DigitalSignal(name=f'clk_val_{gated_clk_sig_name}', width=1, abspath=''))
            self.inst_emu_clk_sigs.gen_signal(DigitalSignal(name=f'clk_{gated_clk_sig_name}', width=1, abspath=''))

        ## Instantiate gen emulation clk module
        self.emu_clks_inst_ifc = SVAPI()

        emu_clks_inst = ModuleInst(api=self.emu_clks_inst_ifc, name="gen_emu_clks")
        emu_clks_inst.add_input(scfg.emu_clk_2x, connection=scfg.emu_clk_2x)
        emu_clks_inst.add_output(scfg.emu_clk, connection=scfg.emu_clk)

        for gated_clk_sig_name in gated_clk_sig_names:
            clk_val = DigitalSignal(name=f'clk_val_{gated_clk_sig_name}', width=1, abspath='')
            clk = DigitalSignal(name=f'clk_{gated_clk_sig_name}', width=1, abspath='')
            emu_clks_inst.add_input(clk_val, connection=clk_val)
            emu_clks_inst.add_output(clk, connection=clk)

        emu_clks_inst.generate_instantiation()

        ######################################################
        # Manage time manager Module
        ######################################################

        dt_req_sig_names = []

        ## Instantiate all time manager signals
        self.inst_timemanager_sigs = SVAPI()

        if scfg.num_dt_reqs > 0:
            self.inst_timemanager_sigs.gen_signal(DigitalSignal(name=f'emu_dt', abspath='', width=pcfg.cfg.dt_width, signed=True))
            for derived_clk in scfg.clk_derived:
                if derived_clk.abspath_dt_req is not None:
                    dt_req_sig_names.append(derived_clk.name)

        for dt_req_sig_name in dt_req_sig_names:
            self.inst_timemanager_sigs.gen_signal(DigitalSignal(name=f'dt_req_{dt_req_sig_name}', abspath='', width=pcfg.cfg.dt_width, signed=True))

        ## Instantiate time manager module
        self.time_manager_inst_ifc = SVAPI()
        time_manager_inst = ModuleInst(api=self.time_manager_inst_ifc, name='gen_time_manager')
        time_manager_inst.add_input(scfg.emu_clk, connection=scfg.emu_clk)
        time_manager_inst.add_input(scfg.reset_ctrl, connection=scfg.reset_ctrl)
        time_manager_inst.add_output(scfg.time_probe, scfg.time_probe)
        if scfg.num_dt_reqs > 0:
            # wire up the emu_dt signal if needed
            # TODO: cleanup
            emu_dt = DigitalSignal(name='emu_dt', abspath='', width=pcfg.cfg.dt_width, signed=True)
            time_manager_inst.add_output(emu_dt, emu_dt)
        for dt_req_sig_name in dt_req_sig_names:
            dt_req_sig = DigitalSignal(name=f'dt_req_{dt_req_sig_name}', abspath='', width=pcfg.cfg.dt_width, signed=True)
            time_manager_inst.add_input(dt_req_sig, connection=dt_req_sig)

        time_manager_inst.generate_instantiation()

        #####################################################
        # Instantiate testbench
        #####################################################
        self.tb_inst_ifc = SVAPI()
        tb_inst = ModuleInst(api=self.tb_inst_ifc, name='tb')
        tb_inst.add_inputs(scfg.clk_independent, connections=scfg.clk_independent)
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
{{subst.inst_timemanager_sigs.text}}

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

// Time manager
{{subst.time_manager_inst_ifc.text}}

// calculate decimation ctrl signal for trace port
logic [{{subst.dec_bits|int-1}}:0] emu_dec_cnt, emu_dec_nxt;
assign emu_dec_cmp = (emu_dec_cnt == {{subst.dec_thr}}) ? 1'b1 : 0;
assign emu_dec_nxt = (emu_dec_cmp == 1'b1) ? 'd0 : (emu_dec_cnt + 'd1);
mem_digital #(
    .init('d0),
    .width({{subst.dec_bits|int}})
) mem_digital_emu_dec_cnt_i (
    .in(emu_dec_nxt),
    .out(emu_dec_cnt),
    .clk(`CLK_MSDSL),
    .rst(`RST_MSDSL),
    .cke(1'b1)
);

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
    // stop simulation after some time
    initial begin
        #((`TSTOP_MSDSL)*1s);
        $finish;
    end

    // dump waveforms to a specified VCD file
    initial begin
        $dumpfile("{{subst.result_path_raw}}");
    end
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule

`default_nettype wire
'''

def main():
    print(ModuleTop(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()
