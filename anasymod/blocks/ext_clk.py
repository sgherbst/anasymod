from anasymod.templ import JinjaTempl
from anasymod.config import EmuConfig

class TemplExtClk(JinjaTempl):
    def __init__(self, cfg: EmuConfig, ext_clk_name='ext_clk'):
        super().__init__(trim_blocks=True, lstrip_blocks=True)

        self.ext_clk_pin = cfg.board.cfg['clk_pin']
        self.ext_clk_io_std = cfg.board.cfg['clk_io']

        #add _p _n suffix in case of two input clks
        if len(self.ext_clk_pin) == 2:
            self.ext_clk_name = [ext_clk_name + '_p', ext_clk_name + '_n']
        elif len(self.ext_clk_pin) == 1:
            self.ext_clk_name = [ext_clk_name]
        else:
            raise ValueError(f"Definition of 'clk_pin' in FPGA board setup is wrong, provide either one or two arguments in list, not:{cfg.board.cfg['clk_pin']}")

        period_ns = 1e9/cfg.board.cfg.clk_freq
        self.ext_clk_full_period_ns = str(period_ns)
        self.ext_clk_half_period_ns = str(0.5*period_ns)

        self.zipped = zip(self.ext_clk_pin, self.ext_clk_name)

    TEMPLATE_TEXT = '''
# start auto-generated code for external clock

{% for boardpin, designpin in subst.zipped -%}
    set_property -dict {PACKAGE_PIN {{boardpin}} IOSTANDARD {{subst.ext_clk_io_std}}} [get_ports {{designpin}}]
{% endfor %}

create_clock -period {{subst.ext_clk_full_period_ns}} -name {{subst.ext_clk_name[0]}} -waveform {0.0 {{subst.ext_clk_half_period_ns}}} -add [get_ports {{subst.ext_clk_name[0]}}]
'''

def main():
    print(TemplExtClk(cfg=EmuConfig(root='test', cfg_file=None)).render())

if __name__ == "__main__":
    main()