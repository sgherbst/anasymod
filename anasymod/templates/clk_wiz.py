from anasymod.templates.generic_ip import TemplGenericIp
from anasymod.targets import FPGATarget
from anasymod.base_config import BaseConfig
from anasymod.enums import ConfigSections
from anasymod.config import EmuConfig

class TemplClkWiz(TemplGenericIp):
    def __init__(self, target: FPGATarget):

        ####################################################
        # Add module ports
        ####################################################


        ####################################################
        # Generate ip core config for clk wizard
        ####################################################
        props = {}
        # Add input clks
        props['CONFIG.PRIM_IN_FREQ'] = str(target.prj_cfg.board.clk_freq * 1e-6)
        if len(target.str_cfg.clk_i) == 2:
            props['CONFIG.PRIM_SOURCE'] = 'Differential_clock_capable_pin'
        elif len(target.str_cfg.clk_i) == 1:
            props['CONFIG.PRIM_SOURCE'] = 'Single_ended_clock_capable_pin'
        else:
            raise Exception("Wrong number of master clk pins is provided")

        # Add master output clk (emu_clk)
        props[f'CONFIG.CLKOUT1_USED'] = 'true'
        # commented out the line below because the "_PORT" config option is buggy
        props['CONFIG.CLKOUT1_REQUESTED_OUT_FREQ'] = (target.prj_cfg.cfg.emu_clk_freq * 1e-6)

        # Add debug clks
        for k, port in enumerate(target.str_cfg.clk_d):
            props[f'CONFIG.CLKOUT{k+2}_USED'] = 'true'
            # commented out the line below because the "_PORT" config option is buggy
            #props[f'CONFIG.CLKOUT{k+2}_PORT'] = port.name
            props[f'CONFIG.CLKOUT{k+2}_REQUESTED_OUT_FREQ'] = (target.prj_cfg.board.dbg_hub_clk_freq * 1e-6)

        # Add additional output clks
        #if self.target.str_cfg.cfg.clk_o_num:
        #    props['CONFIG.FEEDBACK_SOURCE'] = 'FDBK_AUTO'

        #for k, port in enumerate(self.target.str_cfg.clk_o):
        #    # commented out the line below because the "_PORT" config option is buggy
        #    #props[f'CONFIG.CLKOUT{k+self.target.str_cfg.clk_d_num+2}_PORT'] = port.name
        #    props[f'CONFIG.CLKOUT{k+self.target.str_cfg.clk_d_num+2}_USED'] = 'true'
        #    props[f'CONFIG.CLKOUT{k+self.target.str_cfg.clk_d_num+2}_REQUESTED_OUT_FREQ'] = (self.target.prj_cfg.cfg.emu_clk_freq * 1e-6)
        #    props[f'CONFIG.CLKOUT{k+self.target.str_cfg.clk_d_num+2}_DRIVES'] = 'BUFGCE'

        ####################################################
        # Prepare Template substitutions
        ####################################################

        props[f'CONFIG.NUM_OUT_CLKS'] = len(target.str_cfg.clk_m + target.str_cfg.clk_d) #ToDo: This shall not be hardwired!!!

        super().__init__(ip_name='clk_wiz', ip_dir=target.ip_dir, props=props)

def main():
    print(TemplClkWiz(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()
