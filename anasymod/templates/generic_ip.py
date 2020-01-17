import os.path

from anasymod.templates.templ import JinjaTempl
from anasymod.util import back2fwd


class TemplGenericIp(JinjaTempl):
    def __init__(self, ip_name, ip_module_name=None, props=None, ip_dir=None):
        super().__init__()
        # set defaults
        if props is None:
            props = {}

        if ip_module_name is None:
            ip_module_name = ip_name + '_0'

        self.ip_name = ip_name
        self.ip_module_name = ip_module_name
        self.ip_xci_path = back2fwd(os.path.join(ip_dir, ip_module_name, f'{ip_module_name}.xci'))

        self.props = props

    TEMPLATE_TEXT = '''
# start auto-generated code for {{subst.ip_name}}

create_ip -name {{subst.ip_name}} -vendor xilinx.com -library ip -module_name {{subst.ip_module_name}}

set_property -dict [list \\
{%- for propname, propvalue in subst.props.items() %}
    {{propname}} {{'{'}}{{ propvalue }}{{'}'}} \\
{%- endfor %}
] [get_ips {{subst.ip_module_name}}]

generate_target instantiation_template [get_files "{{subst.ip_xci_path}}"]

# end auto-generated code for {{subst.ip_name}}

'''

def main():
    print(TemplGenericIp(ip_name='ip_name', ip_module_name='ip_module_name', ip_dir='ip_dir').render())

if __name__ == "__main__":
    main()