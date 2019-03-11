from anasymod.blocks.generic_ip import TemplGenericIp
from anasymod.anasymod.targets import FPGATarget
from anasymod.anasymod.config import EmuConfig

class TemplClkWiz(TemplGenericIp):
    def __init__(self, cfg: EmuConfig, target: FPGATarget, num_out_clks=1):
        # set defaults
        if output_freqs is None:
            output_freqs = []

        # Initialize config
        self.cfg = {}
        self.cfg['input_freq'] = cfg.board['clk_freq']
        self.cfg['output_freq'] = target.cfg['emu_clk_freq']
        self.cfg['dbg_hub_clk_freq'] = cfg.board['dbg_hub_clk_freq']
        self.cfg['num_out_clks'] = num_out_clks

        hier weiter: code unten entsprechend anpassen, clk für emu clk not gated, clk für debug not gated, weitere clks gated
        !! außerdem propagation bzgl. anzahl der clks weiter nach oben propagieren; allgemeiner container nötig der beschreibt wieviele zusätzliche clks benötigt werden zB durch bestehendes dig design, MRTL ...
        props = {}
        props['CONFIG.PRIM_IN_FREQ'] = str(input_freq*1e-6)
        for k, freq in enumerate(output_freqs):
            props[f'CONFIG.CLKOUT{k+1}_USED'] = 'true'
            props[f'CONFIG.CLKOUT{k+1}_REQUESTED_OUT_FREQ'] = str(freq*1e-6)

        super().__init__('clk_wiz', ip_dir=ip_dir, props=props)

def main():
    pass

if __name__ == "__main__":
    main()
