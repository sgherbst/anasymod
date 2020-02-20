from anasymod.templates.templ import JinjaTempl
from anasymod.targets import FPGATarget
from anasymod.config import EmuConfig

class TemplExtClk(JinjaTempl):
    def __init__(self, target: FPGATarget):
        super().__init__(trim_blocks=True, lstrip_blocks=True)
        self.target = target

        self.ports = self.target.str_cfg.clk_i

        self.ext_clk_pin = self.target.prj_cfg.board.clk_pin
        self.ext_clk_io_std = self.target.prj_cfg.board.clk_io

        period_ns = 1e9 / self.target.prj_cfg.board.clk_freq
        self.ext_clk_full_period_ns = str(period_ns)
        self.ext_clk_half_period_ns = str(0.5*period_ns)

        self.zipped = zip(self.ext_clk_pin, [port.name for port in self.ports])

    TEMPLATE_TEXT = '''
# start auto-generated code for external clock

{% for boardport, designport in subst.zipped -%}
    set_property -dict {PACKAGE_PIN {{boardport}} IOSTANDARD {{subst.ext_clk_io_std}}} [get_ports {{designport}}]
{% endfor %}

create_clock -period {{subst.ext_clk_full_period_ns}} -name {{subst.ports[0].name}} -waveform {0.0 {{subst.ext_clk_half_period_ns}}} -add [get_ports {{subst.ports[0].name}}]
'''

def main():
    print(TemplExtClk(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()