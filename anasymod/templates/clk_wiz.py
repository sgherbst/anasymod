from anasymod.templates.generic_ip import TemplGenericIp
from anasymod.targets import FPGATarget
from anasymod.config import EmuConfig

class TemplClkWiz(TemplGenericIp):
    def __init__(self, target: FPGATarget):
        # defaults
        scfg = target.str_cfg
        pcfg = target.prj_cfg

        ####################################################
        # Generate ip core config for clk wizard
        ####################################################
        props = {}
        # Add input clks
        props['CONFIG.PRIM_IN_FREQ'] = str(pcfg.board.clk_freq * 1e-6)
        if len(scfg.clk_i) == 2:
            props['CONFIG.PRIM_SOURCE'] = 'Differential_clock_capable_pin'
        elif len(scfg.clk_i) == 1:
            props['CONFIG.PRIM_SOURCE'] = 'Single_ended_clock_capable_pin'
        else:
            raise Exception("Wrong number of master clk pins is provided")

        # Add emu_clk_2x
        props[f'CONFIG.CLKOUT1_USED'] = 'true'
        props['CONFIG.CLKOUT1_REQUESTED_OUT_FREQ'] = (scfg.emu_clk_2x.freq * 1e-6)

        # Add dbg_clk
        props[f'CONFIG.CLKOUT2_USED'] = 'true'
        props[f'CONFIG.CLKOUT2_REQUESTED_OUT_FREQ'] = (scfg.dbg_clk.freq * 1e-6)

        # Add additional independent clks
        for k, clk in enumerate(scfg.clk_independent):
            props[f'CONFIG.CLKOUT{k + 3}_USED'] = 'true'
            props[f'CONFIG.CLKOUT{k + 3}_REQUESTED_OUT_FREQ'] = (clk.freq * 1e-6)

        ####################################################
        # Prepare Template substitutions
        ####################################################

        props[f'CONFIG.NUM_OUT_CLKS'] = len(scfg.clk_independent) + 2

        super().__init__(ip_name='clk_wiz', ip_dir=target.ip_dir, props=props)

def main():
    print(TemplClkWiz(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()
