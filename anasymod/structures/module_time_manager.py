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

        dt_req_sig_names = []
        if scfg.num_dt_reqs > 0:
            module.add_output(DigitalSignal(name=f'emu_dt', abspath='', width=pcfg.cfg.dt_width, signed=True))
            for derived_clk in scfg.clk_derived:
                if derived_clk.abspath_dt_req is not None:
                    dt_req_sig_names.append(derived_clk.name)

        for dt_req_sig_name in dt_req_sig_names:
            module.add_input(DigitalSignal(name=f'dt_req_{dt_req_sig_name}', abspath='', width=pcfg.cfg.dt_width, signed=True))

        module.generate_header()

        #####################################################
        # Behaviour if num_dt_req > 0
        #####################################################

        if dt_req_sig_names:
            self.signal_gen = SVAPI()
            for dt_req_sig_name in dt_req_sig_names:
                self.signal_gen.gen_signal(DigitalSignal(name=f'dt_arr_{dt_req_sig_name}', abspath='', width=pcfg.cfg.dt_width, signed=True))

            self.assign_ends = SVAPI()
            self.assign_ends.indent()
            self.assign_ends.writeln(f'assign dt_arr_{dt_req_sig_names[0]} = dt_req_{dt_req_sig_names[0]};')
            self.assign_ends.writeln(f'assign emu_dt = dt_arr_{dt_req_sig_names[-1]};')

            self.assign_intermediates = SVAPI()
            for k in range(1, len(dt_req_sig_names)):
                self.assign_intermediates.writeln(f'assign dt_arr_{dt_req_sig_names[k]} = dt_req_{dt_req_sig_names[k]} < dt_arr_{dt_req_sig_names[k-1]} ? dt_req_{dt_req_sig_names[k]} : dt_arr_{dt_req_sig_names[k-1]};')

    TEMPLATE_TEXT = '''
`timescale 1ns/1ps

`include "msdsl.sv"

`default_nettype none

{{subst.module_ifc.text}}

{% if subst.num_dt_reqs == 0 %}
    `COPY_FORMAT_REAL(emu_time, emu_time_next);
    `COPY_FORMAT_REAL(emu_time, emu_dt);

    `ASSIGN_CONST_REAL({{subst.dt_value}}, emu_dt);
    `ADD_INTO_REAL(emu_time, emu_dt, emu_time_next);
    `DFF_INTO_REAL(emu_time_next, emu_time, `RST_MSDSL, `CLK_MSDSL, 1'b1, 0);
{% else %}

    logic emu_time_sig;
    
    // create array of intermediate results and assign the endpoints
    {{subst.signal_gen.text}}
{{subst.assign_ends.text}}
    
    // assign intermediate results
    {{subst.assign_intermediates.text}}
    
    // calculate emulation time
    always @(posedge emu_clk) begin
        if (emu_rst == 1'b1) begin
            emu_time_sig <= '0;
        end else begin
            emu_time_sig <= emu_time_sig + emu_dt;
        end
    end
    
    assign emu_time = emu_time_sig;
{% endif %}
endmodule

`default_nettype wire
'''

def main():
    print(ModuleTimeManager(scfg=StructureConfig(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()