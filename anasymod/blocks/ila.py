from anasymod.templ import JinjaTempl
from anasymod.util import next_pow_2
from anasymod.probe_config import ProbeConfig

class TemplILA(JinjaTempl):
    def __init__(self, probe_cfg_path, depth=1024, inst_name='u_ila_0', ila_clk='emu_clk'):
        # set defaults

        # adjust depth if necessary
        depth = max(next_pow_2(depth), 1024)

        self.inst_name = inst_name

        self.width_ila_clk = '1'
        self.conn_ila_clk = ila_clk

        self.ila_prop = {}
        self.ila_prop['C_INPUT_PIPE_STAGES'] = '1'
        self.ila_prop['ALL_PROBE_SAME_MU_CNT'] = '1'
        self.ila_prop['C_DATA_DEPTH'] = str(depth)

        # specify all signals to be probed
        self.probe_cfg = ProbeConfig(probe_cfg_path=probe_cfg_path)
        self.probes = {}
        signals = self.probe_cfg.analog_signals + self.probe_cfg.time_signal + self.probe_cfg.reset_signal + self.probe_cfg.digital_signals
        print(f"Signals:{signals}")
        for k, (conn, width, _) in enumerate(signals):
            probe_name = f'probe{k}'
            self.probes[probe_name] = {}
            self.probes[probe_name]['conn'] = conn
            self.probes[probe_name]['width'] = str(width)

    TEMPLATE_TEXT = '''
# start auto-generated code for ILA

create_debug_core {{subst.inst_name}} ila

{% for propname, propvalue in subst.ila_prop.items() -%}
    set_property {{propname}} {{ propvalue }} [get_debug_cores {{ subst.inst_name }}]
{% endfor -%}

set_property port_width {{ subst.width_ila_clk }} [get_debug_ports {{ subst.inst_name }}/clk]
connect_debug_port {{ subst.inst_name }}/clk [get_nets [list {{ subst.conn_ila_clk }}]]

{%- set probe = probe0 -%}
{% for probename, probevalue in subst.probes.items() -%}
    {% if probename != 'probe0' %}
create_debug_port {{ subst.inst_name }} probe
    {%- endif %}
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports {{ subst.inst_name }}/{{probename}}]
set_property port_width {{probevalue.width}} [get_debug_ports {{ subst.inst_name }}/{{probename}}]
connect_debug_port {{ subst.inst_name }}/{{ probename }} [get_nets [list
    {%- if probevalue.width != '1' %}
    {%- for idx in range(probevalue.width|int) -%}
        {{ ' {' }}{{ probevalue.conn }}[{{ idx }}]{{'}'}}
    {%- endfor %}
    {%- else -%}
        {{' '}}{{ probevalue.conn }}
    {%- endif -%}
]]
{%- endfor %}

# end auto-generated code for ILA
'''

def main():
    print(TemplILA().render())

if __name__ == "__main__":
    main()