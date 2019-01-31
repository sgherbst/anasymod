from anasymod.blocks.generic_ip import TemplGenericIp

class TemplClkWiz(TemplGenericIp):
    def __init__(self, ip_dir, input_freq, output_freqs=None):
        # set defaults
        if output_freqs is None:
            output_freqs = []

        props = {}
        props['CONFIG.PRIM_IN_FREQ'] = str(input_freq*1e-6)
        for k, freq in enumerate(output_freqs):
            props[f'CONFIG.CLKOUT{k+1}_USED'] = 'true'
            props[f'CONFIG.CLKOUT{k+1}_REQUESTED_OUT_FREQ'] = str(freq*1e-6)

        super().__init__('clk_wiz', ip_dir=ip_dir, props=props)

def main():
    print(TemplClkWiz('ip_dir', 125e6, [25e6, 300e6]).render())

if __name__ == "__main__":
    main()
