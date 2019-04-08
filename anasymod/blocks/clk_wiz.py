from anasymod.blocks.generic_ip import TemplGenericIp

class TemplClkWiz(TemplGenericIp):
    def __init__(self, ip_dir, input_freq, clk_wiz_outputs=None, clk_wiz_diff_input=False):
        # set defaults
        if clk_wiz_outputs is None:
            clk_wiz_outputs = []

        props = {}

        # request differential clock input if needed
        if clk_wiz_diff_input:
            props['CONFIG.PRIM_SOURCE'] = 'Differential_clock_capable_pin'

        # set the input clock frequency
        props['CONFIG.PRIM_IN_FREQ'] = str(input_freq*1e-6)

        # specify the number of output clocks
        props['CONFIG.NUM_OUT_CLKS'] = str(len(clk_wiz_outputs))

        for k, (freq, gated) in enumerate(clk_wiz_outputs):
            # note that clock numbers start from 1, not 0
            clk_num = k+1

            # declare that this clock output is being used
            props[f'CONFIG.CLKOUT{clk_num}_USED'] = 'true'

            # state the desired output frequency of this clock
            props[f'CONFIG.CLKOUT{clk_num}_REQUESTED_OUT_FREQ'] = str(freq*1e-6)

            # if the clock is gated, we indicate this by changing the output driver to BUFGCE
            # another option is BUFHCE, although that may not be quite as flexible...
            if gated:
                props[f'CONFIG.CLKOUT{clk_num}_DRIVES'] = 'BUFGCE'

        super().__init__('clk_wiz', ip_dir=ip_dir, props=props)

def main():
    clk_wiz_outputs = []
    clk_wiz_outputs += [(25e6, False)]
    clk_wiz_outputs += [(100e6, False)]
    clk_wiz_outputs += [(25e6, True)]
    clk_wiz_outputs += [(25e6, True)]
    print(TemplClkWiz('ip_dir', 125e6, clk_wiz_outputs).render())

if __name__ == "__main__":
    main()
