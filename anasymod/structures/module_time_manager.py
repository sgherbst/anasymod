from anasymod.templates.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.generators.gen_api import SVAPI, ModuleInst
from anasymod.structures.structure_config import StructureConfig
from anasymod.sim_ctrl.datatypes import DigitalSignal


class ModuleTimeManager(JinjaTempl):
    def __init__(self, scfg: StructureConfig, pcfg: EmuConfig, plugin_includes: list):
        super().__init__(trim_blocks=True, lstrip_blocks=True)

        self.num_dt_reqs = scfg.num_dt_reqs
        self.dt_value = pcfg.cfg.dt

        #####################################################
        # Add plugin specific includes
        #####################################################

        self.plugin_includes = SVAPI()
        for plugin in plugin_includes:
            for include_statement in plugin.include_statements:
                self.plugin_includes.writeln(f'{include_statement}')

        #####################################################
        # Create module interface
        #####################################################
        self.module_ifc = SVAPI()

        module = ModuleInst(api=self.module_ifc, name="gen_time_manager")
        module.add_input(scfg.emu_clk)
        module.add_input(scfg.reset_ctrl)
        module.add_output(scfg.time_probe)

        module.add_output(DigitalSignal(name=f'emu_dt', abspath='', width=pcfg.cfg.dt_width, signed=False))

        # add inputs for external timestep requests
        dt_reqs = []
        for derived_clk in scfg.clk_derived:
            if derived_clk.abspath_dt_req is not None:
                dt_req = DigitalSignal(
                    name=f'dt_req_{derived_clk.name}',
                    abspath='',
                    width=pcfg.cfg.dt_width,
                    signed=False
                )
                module.add_input(dt_req)
                dt_reqs.append(dt_req)

        # add input for anasymod control dt request signal
        dt_req = DigitalSignal(name=f'dt_req_stall', abspath='', width=pcfg.cfg.dt_width, signed=False)
        module.add_input(dt_req)
        dt_reqs.append(dt_req)

        # add input for dt request signal, in case a default oscillator is used
        if scfg.use_default_oscillator:
            dt_req = DigitalSignal(name=f'dt_req_default_osc', abspath='', width=pcfg.cfg.dt_width, signed=False)
            module.add_input(dt_req)
            dt_reqs.append(dt_req)

        module.generate_header()

        # generate a bit of code to take the minimum of the timestep requests
        self.codegen = SVAPI()
        self.codegen.indent()

        # take minimum of the timestep requests
        if len(dt_reqs) == 0:
            # Convert dt value to integer considering dt_scale
            dt_as_int = int(float(pcfg.cfg.dt) / float(pcfg.cfg.dt_scale))

            # Represent as binary and expand to dt_width
            dt_as_bin = bin(dt_as_int).replace('b', '').zfill(pcfg.cfg.dt_width)

            # assign to the emulator timestep output
            self.codegen.writeln(f"assign emu_dt = {pcfg.cfg.dt_width}'b{dt_as_bin};")
        else:
            prev_min = None
            for k, curr_sig in enumerate(dt_reqs):
                if k == 0:
                    prev_min = curr_sig.name
                else:
                    # create a signal to hold temporary min result
                    curr_min = f'__dt_req_min_{k - 1}'
                    self.codegen.writeln(f'(* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] {curr_min};')
                    # take the minimum of the previous minimum and the current signal
                    curr_min_val = self.vlog_min(curr_sig.name, prev_min)
                    self.codegen.writeln(f'assign {curr_min} = {curr_min_val};')
                    # mark the current minimum as the previous minimum for the next
                    # iteration of the loop
                    prev_min = curr_min
            # assign to the emulator timestep output
            self.codegen.writeln(f'assign emu_dt = {prev_min};')

    @staticmethod
    def vlog_min(a, b):
        return f'((({a}) < ({b})) ? ({a}) : ({b}))'

    TEMPLATE_TEXT = '''\
`timescale 1ns/1ps

{{subst.plugin_includes.text}}

`default_nettype none

{{subst.module_ifc.text}}
{{subst.codegen.text}}
    // assign internal state variable to output
    logic [((`TIME_WIDTH)-1):0] emu_time_state;
    assign emu_time = emu_time_state;

    // update emulation time on each clock cycle
    always @(posedge emu_clk) begin
        if (emu_rst==1'b1) begin
            emu_time_state <= 0;
        end else begin
            emu_time_state <= emu_time_state + emu_dt;
        end
    end
endmodule

`default_nettype wire
'''


def main():
    print(ModuleTimeManager(scfg=StructureConfig(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())


if __name__ == "__main__":
    main()