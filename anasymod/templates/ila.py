from anasymod.templates.templ import JinjaTempl
from anasymod.util import next_pow_2
from anasymod.targets import FPGATarget

class TemplILA(JinjaTempl):
    def __init__(self, target: FPGATarget, depth=4096):
        super().__init__()
        # set defaults

        # Sanity checking for ILA depth
        assert next_pow_2(depth) == depth, 'The ILA depth must be a power of 2.'
        assert depth >= 1024, 'The ILA depth must be at least 1024.'

        self.inst_name = target.prj_cfg.vivado_config.ila_inst_name

        self.width_ila_clk = '1'
        self.conn_ila_clk = target.str_cfg.clk_m[0].name

        self.ila_prop = {}

        # set the number samples per signal
        self.ila_prop['C_DATA_DEPTH'] = str(depth)

        # add a pipelined input to reduce burden on timing closure
        self.ila_prop['C_INPUT_PIPE_STAGES'] = '1'

        # enable capture control
        self.ila_prop['C_EN_STRG_QUAL'] = 'true'

        # two comparators per probe are recommended when using capture control (per UG908, p 40)
        self.ila_prop['ALL_PROBE_SAME_MU_CNT'] = '2'

        # specify all signals to be probed
        self.probes = {}
        signals = target.str_cfg.probes
        print(f"Signals: {[f'{signal.name}' for signal in signals]}")
        for k, (_, abspath, width, _) in enumerate(signals):
            probe_name = f'probe{k}'
            self.probes[probe_name] = {}
            self.probes[probe_name]['conn'] = abspath
            self.probes[probe_name]['width'] = str(width)

    TEMPLATE_TEXT = '''
{% if subst.probes %}  
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
{% endif %}  
'''

def main():
    print(TemplILA().render())

if __name__ == "__main__":
    main()