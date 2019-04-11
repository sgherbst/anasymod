from anasymod.blocks.generic_ip import TemplGenericIp
from anasymod.targets import FPGATarget
from anasymod.base_config import BaseConfig
from anasymod.enums import ConfigSections
from anasymod.config import EmuConfig

class TemplClkWiz(TemplGenericIp):
    def __init__(self, target: FPGATarget):

        self.target = target

        ####################################################
        # Initialize config
        ####################################################
        self.cfg = Config(target=self.target)

        # Update config options by reading from config file
        self.cfg.update_config()

        ####################################################
        # Add module ports
        ####################################################


        ####################################################
        # Generate ip core config for clk wizard
        ####################################################
        props = {}
        # Add input clks
        props['CONFIG.PRIM_IN_FREQ'] = str(self.target.prj_cfg.board.clk_freq * 1e-6)
        props['CONFIG.PRIM_SOURCE'] = self.cfg.input_source

        # Add master output clk (emu_clk)
        props[f'CONFIG.CLKOUT1_USED'] = 'true'
        #props[f'CONFIG.CLKOUT1_PORT'] = self.target.str_cfg.clk_m_names[0]
        props['CONFIG.CLKOUT1_REQUESTED_OUT_FREQ'] = (self.target.prj_cfg.cfg.emu_clk_freq * 1e-6)

        # Add debug clks
        for k, port in enumerate(self.target.str_cfg.clk_d_ports):
            props[f'CONFIG.CLKOUT{k+2}_USED'] = 'true'
            #props[f'CONFIG.CLKOUT{k+2}_PORT'] = port.name
            props[f'CONFIG.CLKOUT{k+2}_REQUESTED_OUT_FREQ'] = (self.target.prj_cfg.board.dbg_hub_clk_freq * 1e-6)

        # Add additional output clks
        if self.target.str_cfg.cfg.clk_o_num:
            props['CONFIG.FEEDBACK_SOURCE'] = 'FDBK_AUTO'

        for k, port in enumerate(self.target.str_cfg.clk_o_ports):
            #props[f'CONFIG.CLKOUT{k+self.target.str_cfg.clk_d_num+2}_PORT'] = port.name
            props[f'CONFIG.CLKOUT{k+self.target.str_cfg.clk_d_num+2}_USED'] = 'true'
            props[f'CONFIG.CLKOUT{k+self.target.str_cfg.clk_d_num+2}_REQUESTED_OUT_FREQ'] = (self.target.prj_cfg.cfg.emu_clk_freq * 1e-6)
            props[f'CONFIG.CLKOUT{k+self.target.str_cfg.clk_d_num+2}_DRIVES'] = 'BUFGCE'

        ####################################################
        # Prepare Template substitutions
        ####################################################

        props[f'CONFIG.NUM_OUT_CLKS'] = '2'

        super().__init__(ip_name='clk_wiz', target=self.target, props=props)

class Config(BaseConfig):
    """
    Container to store all config attributes.
    """

    def __init__(self, target: FPGATarget):
        super().__init__(cfg_file=target.prj_cfg.cfg_file, section=ConfigSections.CLK)

        # add some default enums
        #single_ended = 'Single_ended_clock_capable_pin'
        #differential = 'Differential_clock_capable_pin'

        self.input_source = 'Single_ended_clock_capable_pin'

def main():
    print(TemplClkWiz(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()
