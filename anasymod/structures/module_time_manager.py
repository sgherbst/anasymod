from anasymod.templates.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.generators.gen_api import SVAPI, ModuleInst
from anasymod.structures.structure_config import StructureConfig
from anasymod.sim_ctrl.datatypes import DigitalSignal

class ModuleTimeManager(JinjaTempl):
    def __init__(self, scfg: StructureConfig, pcfg: EmuConfig):
        super().__init__(trim_blocks=True, lstrip_blocks=True)

        self.num_dt_reqs = scfg.num_dt_reqs
        self.dt_value = pcfg.cfg.dt

        #####################################################
        # Create module interface
        #####################################################
        self.module_ifc = SVAPI()

        module = ModuleInst(api=self.module_ifc, name="gen_time_manager")
        module.add_input(scfg.emu_clk)
        module.add_input(scfg.reset_ctrl)
        module.add_output(scfg.time_probe)

        module.add_output(DigitalSignal(name=f'emu_dt', abspath='', width=pcfg.cfg.dt_width, signed=False))

        # determine all of the timestep request signal names
        dt_req_sig_names = []

        # add inputs for external timestep requests
        for derived_clk in scfg.clk_derived:
            if derived_clk.abspath_dt_req is not None:
                module.add_input(
                    DigitalSignal(
                        name=f'dt_req_{derived_clk.name}', abspath='',
                        width=pcfg.cfg.dt_width, signed=False
                    )
                )
                dt_req_sig_names.append(derived_clk.name)

        module.generate_header()

        # generate a bit of code to take the minimum of the timestep requests
        self.codegen = SVAPI()
        self.codegen.indent()

        # add a default timestep request if none are specified
        if scfg.num_dt_reqs == 0:
            # name and value for default timestep request
            dt_def_req_name = 'dt_def_req'
            dt_def_req = int(round(pcfg.cfg.dt / pcfg.cfg.dt_scale))
            # add signal and assign value
            self.codegen.writeln(f'// Using a fixed timestep {pcfg.cfg.dt} with scale factor {pcfg.cfg.dt_scale}')
            self.codegen.writeln(f'logic [((`DT_WIDTH)-1):0] {dt_def_req_name};')
            self.codegen.writeln(f'assign {dt_def_req_name} = {dt_def_req};')
            # append signal to list of timestep requests
            dt_req_sig_names.append(dt_def_req_name)

        # take minimum of the timestep requests
        if len(dt_req_sig_names) == 0:
            raise Exception('There should always be at least one timestep request.')
        else:
            prev_min = None
            for k, curr_sig in enumerate(dt_req_sig_names):
                if k == 0:
                    prev_min = curr_sig
                else:
                    # create a signal to hold temporary min result
                    curr_min = f'__dt_req_min_{k-1}'
                    self.codegen.writeln(f'logic [((`DT_WIDTH)-1):0] {curr_min};')
                    # take the minimum of the previous minimum and the current signal
                    curr_min_val = self.vlog_min(curr_sig, prev_min)
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

`include "msdsl.sv"

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