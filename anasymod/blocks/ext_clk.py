from anasymod.templ import JinjaTempl

class TemplExtClk(JinjaTempl):
    def __init__(self, ext_clk_pin='H16', ext_clk_io_std='LVCMOS33', ext_clk_name='ext_clk', ext_clk_freq=125e6):
        super().__init__()
        self.ext_clk_pin = ext_clk_pin
        self.ext_clk_io_std = ext_clk_io_std
        self.ext_clk_name = ext_clk_name

        period_ns = 1e9/ext_clk_freq
        self.ext_clk_full_period_ns = str(period_ns)
        self.ext_clk_half_period_ns = str(0.5*period_ns)

    TEMPLATE_TEXT = '''
# start auto-generated code for external clock

set_property -dict {PACKAGE_PIN {{subst.ext_clk_pin}} IOSTANDARD {{subst.ext_clk_io_std}}} [get_ports {{subst.ext_clk_name}}]
create_clock -period {{subst.ext_clk_full_period_ns}} -name {{subst.ext_clk_name}} -waveform {0.0 {{subst.ext_clk_half_period_ns}}} -add [get_ports {{subst.ext_clk_name}}]

# end auto-generated code for external clock
'''

def main():
    print(TemplExtClk().render())

if __name__ == "__main__":
    main()