from anasymod.templates.templ import JinjaTempl
from anasymod.targets import FPGATarget

class TemplDbgHub(JinjaTempl):
    def __init__(self, target: FPGATarget):
        super().__init__()
        self.dbg_hub_prop = {}
        self.dbg_hub_prop['C_ENABLE_CLK_DIVIDER'] = 'false'
        self.dbg_hub_prop['C_USER_SCAN_CHAIN'] = '1'
        self.dbg_hub_prop['C_CLK_INPUT_FREQ_HZ'] = str(int(target.prj_cfg.board.dbg_hub_clk_freq))
        self.conn_dbg_clk = f'clk_gen_i/clk_wiz_0_i/clk_out2'
        #ToDo: In case multiple dbg hubs are necessary, managing signal names needs to be adapted and several
        # instantiations are necessary

    TEMPLATE_TEXT = '''
# start auto-generated code for debug hub
{%- for propname, propvalue in subst.dbg_hub_prop.items() %}
set_property {{propname}} {{ propvalue }} [get_debug_cores dbg_hub]
{%- endfor %}
connect_debug_port dbg_hub/clk [get_pins {{ subst.conn_dbg_clk }}]

# end auto-generated code for debug hub
'''

def main():
    print(TemplDbgHub().render())

if __name__ == "__main__":
    main()