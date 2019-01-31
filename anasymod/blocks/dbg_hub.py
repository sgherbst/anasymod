from anasymod.templ import JinjaTempl

class TemplDbgHub(JinjaTempl):
    def __init__(self, dbg_hub_clk_freq=300e6):
        self.dbg_hub_prop = {}
        self.dbg_hub_prop['C_ENABLE_CLK_DIVIDER'] = 'false'
        self.dbg_hub_prop['C_USER_SCAN_CHAIN'] = '1'
        self.dbg_hub_prop['C_CLK_INPUT_FREQ_HZ'] = str(int(dbg_hub_clk_freq))
        self.conn_dbg_clk = 'clk_wiz_0_i/clk_out2'

    TEMPLATE_TEXT = '''
# start auto-generated code for debug hub
{%- for propname, propvalue in subst.dbg_hub_prop.items() %}
set_property {{propname}} {{ propvalue }} [get_debug_cores dbg_hub]
{%- endfor %}
connect_debug_port dbg_hub/clk [get_nets {{ subst.conn_dbg_clk }}]

# end auto-generated code for debug hub
'''

def main():
    print(TemplDbgHub().render())

if __name__ == "__main__":
    main()