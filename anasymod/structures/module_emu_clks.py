from anasymod.templates.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.generators.gen_api import SVAPI, ModuleInst
from anasymod.structures.structure_config import StructureConfig
from anasymod.sim_ctrl.datatypes import DigitalSignal


class ModuleEmuClks(JinjaTempl):
    def __init__(self, scfg: StructureConfig, pcfg: EmuConfig):
        super().__init__(trim_blocks=True, lstrip_blocks=True)

        gated_clk_sig_names = []

        #####################################################
        # Create module interface
        #####################################################
        self.module_ifc = SVAPI()

        module = ModuleInst(api=self.module_ifc, name="gen_emu_clks")
        module.add_input(scfg.emu_clk_2x)
        module.add_output(scfg.emu_clk)

        for derived_clk in scfg.clk_derived:
            if derived_clk.abspath_gated_clk is not None:
                gated_clk_sig_names.append(derived_clk.name)

        for gated_clk_sig_name in gated_clk_sig_names:
            module.add_input(DigitalSignal(name=f'clk_val_{gated_clk_sig_name}', width=1, abspath=''))
            module.add_output(DigitalSignal(name=f'clk_{gated_clk_sig_name}', width=1, abspath=''))

        module.generate_header()

        #####################################################
        # Generate other clks
        #####################################################
        self.generated_clks = SVAPI()

        if gated_clk_sig_names:
            for gated_clk_sig_name in gated_clk_sig_names:
                self.generated_clks.gen_signal(DigitalSignal(name=f'clk_unbuf_{gated_clk_sig_name}', width=1, abspath=''))
            self.generated_clks.writeln(f'always @(posedge emu_clk_2x) begin')
            self.generated_clks.indent()
            self.generated_clks.writeln(r"if (emu_clk_unbuf == 1'b0) begin")
            self.generated_clks.indent()
            for gated_clk_sig_name in gated_clk_sig_names:
                self.generated_clks.writeln(f'clk_unbuf_{gated_clk_sig_name} <= clk_val_{gated_clk_sig_name};')
            self.generated_clks.dedent()
            self.generated_clks.writeln(f'end else begin')
            self.generated_clks.indent()
            for gated_clk_sig_name in gated_clk_sig_names:
                self.generated_clks.writeln(f'clk_unbuf_{gated_clk_sig_name} <= clk_unbuf_{gated_clk_sig_name};')
            self.generated_clks.dedent()
            self.generated_clks.writeln(f'end')
            self.generated_clks.dedent()
            self.generated_clks.writeln(f'end')
            self.generated_clks.writeln(f'')
            self.generated_clks.writeln(f'`ifndef SIMULATION_MODE_MSDSL')
            self.generated_clks.indent()
            for k, gated_clk_sig_name in enumerate(gated_clk_sig_names):
                self.generated_clks.writeln(f'BUFG buf_{k} (.I(clk_unbuf_{gated_clk_sig_name}), .O(clk_{gated_clk_sig_name}));')
            self.generated_clks.dedent()
            self.generated_clks.writeln(f'`else')
            self.generated_clks.indent()
            for gated_clk_sig_name in gated_clk_sig_names:
                self.generated_clks.writeln(f'assign clk_{gated_clk_sig_name} = clk_unbuf_{gated_clk_sig_name};')
            self.generated_clks.dedent()
            self.generated_clks.writeln(f'`endif')

    TEMPLATE_TEXT = '''
`timescale 1ns/1ps

`default_nettype none

{{subst.module_ifc.text}}

// generate emu_clk
logic emu_clk_unbuf = 0;
always @(posedge emu_clk_2x) begin
    emu_clk_unbuf <= ~emu_clk_unbuf;
end
`ifndef SIMULATION_MODE_MSDSL
    BUFG buf_emu_clk (.I(emu_clk_unbuf), .O(emu_clk));
`else
    assign emu_clk = emu_clk_unbuf;
`endif

// generate other clocks
{{subst.generated_clks.text}}
endmodule
 
`default_nettype wire
'''

def main():
    print(ModuleEmuClks(scfg=StructureConfig(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()
