from anasymod.templ import JinjaTempl

class TemplExtClk(JinjaTempl):
    def __init__(self, clk_pin_p=None, clk_pin_n=None, io_std='LVCMOS33', clk_freq=125e6):
        # create list of clock pins
        self.clk_pins = []

        if clk_pin_p is not None:
            self.clk_pins.append((clk_pin_p, 'clk_port_p'))
        else:
            raise Exception('clk_pin_p must be provided when defining an external clock.  If the clock is single-ended, just leave clk_pin_n as None.')

        if clk_pin_n is not None:
            self.clk_pins.append((clk_pin_n, 'clk_port_n'))

        # save I/O standard
        self.io_std = io_std

        # calculate timing parameters
        period_ns = 1e9/clk_freq
        self.full_period_ns = str(period_ns)
        self.half_period_ns = str(0.5*period_ns)

    TEMPLATE_TEXT = '''
# start auto-generated code for external clock

{% for pin, port in subst.clk_pins -%}
set_property -dict {PACKAGE_PIN {{pin}} IOSTANDARD {{subst.io_std}}} [get_ports {{port}}]
{% endfor %}
create_clock -period {{subst.full_period_ns}} -name ext_clk -waveform {0.0 {{subst.half_period_ns}}} -add [get_ports {{subst.clk_pins[0][1]}}]

# end auto-generated code for external clock
'''

def main():
    print(TemplExtClk(clk_pin_p='E19', clk_pin_n='E18', io_std='LVDS', clk_freq=200e6).render())

if __name__ == "__main__":
    main()