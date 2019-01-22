from jinja2 import FileSystemLoader, Environment, Template
from os.path import dirname, join, exists, isfile
from os import makedirs
from argparse import ArgumentParser

from emuflow.files import get_full_path
from emuflow.util import call_python

class Template_gen():
    """
    tbd
    """
    def __init__(self, project_root, template_dir, template_name):
        self.tool_root = dirname(dirname(__file__))
        self.project_root = project_root

        self.subst_dict = {}
        self.subst_dict['part'] = r"xc7z020clg400-1"

        self.template_name = template_name
        self.ip_core_template_dir = join(self.tool_root, r"templates", template_dir)
        self.ip_core_template_path = join(self.ip_core_template_dir, template_name)
        self.file_loader = FileSystemLoader(self.ip_core_template_dir)
        self.env = Environment(loader=self.file_loader)

class Ip_cores_gen(Template_gen):
    """
    tbd
    """
    def __init__(self, project_root, template_dir, template_name, ip_name, build_dir):
        Template_gen.__init__(self, project_root, template_dir, template_name)

        self.subst_dict['ip_name'] = ip_name

        if build_dir in [None]:
            self.build_dir = r"{0}/{1}/{2}".format(self.project_root, r"build", r"ips")
            #self.build_dir = join(self.project_root, r"build", r"ips", self.subst_dict['ip_name'])
        else:
            self.build_dir = build_dir
        self.templ_build_dir = join(self.project_root, r"build", r"ip_gen_scripts")

        self.subst_dict['build_dir'] = self.build_dir #r"{0}/{1}".format(self.build_dir, self.subst_dict['ip_name'] + r".xci")
        #self.subst_dict['build_path'] = join(self.build_dir, self.subst_dict['ip_name'] + r".xci")
        self.subst_dict['ip_gen_prj_name'] = r"ip_gen_prj"
        self.subst_dict['ip_gen_prj_dir'] = r"{0}/{1}/{2}".format(self.project_root, r"build", self.subst_dict['ip_gen_prj_name'])
        #self.subst_dict['ip_gen_prj_dir'] = join(self.project_root, r"build", self.subst_dict['ip_gen_prj_name'])


    def _generate(self, template_name, subst_dict):
        template = self.env.get_template(template_name)
        output = template.render(subst=subst_dict)
        #print(output)

        if not exists(self.templ_build_dir):
            makedirs(self.templ_build_dir)
        with open(join(self.templ_build_dir, r"gen_" + self.subst_dict['ip_name'] + r".tcl"), "w") as fh:
            fh.write(output)

class Clk_wiz_gen(Ip_cores_gen):
    """
    tbd
    """
    def __init__(self, project_root, template_dir=r"ip_cores", template_name=r"templ_clk_gen.txt", ip_name=r"clk_wiz", build_dir=None):
        Ip_cores_gen.__init__(self, project_root, template_dir, template_name, ip_name, build_dir)

        # IP Core specific properties
        self.subst_dict['prop'] = {}
        #self.subst_dict['prop']['PRIM_IN_FREQ'] = r"125.000"
        #self.subst_dict['prop']['CLKOUT1_USED'] = r"true"
        #self.subst_dict['prop']['CLKOUT1_REQUESTED_OUT_FREQ'] = r"20.000"
        #self.subst_dict['prop']['CLKOUT1_DRIVES'] = r"tbd"
        #self.subst_dict['prop']['CLKOUT2_USED'] = r"false"
        #self.subst_dict['prop']['CLKOUT2_REQUESTED_OUT_FREQ'] = r"0.000"
        #self.subst_dict['prop']['CLKOUT2_DRIVES'] = r"tbd"
        #self.subst_dict['prop']['CLKOUT3_USED'] = r"false"
        #self.subst_dict['prop']['CLKOUT3_REQUESTED_OUT_FREQ'] = r"0.000"
        #self.subst_dict['prop']['CLKOUT3_DRIVES'] = r"BUFGCE"
        #self.subst_dict['prop']['CLKIN1_JITTER_PS'] = r"80.0"
        #self.subst_dict['prop']['MMCM_DIVCLK_DIVIDE'] = r"1"
        #self.subst_dict['prop']['MMCM_CLKFBOUT_MULT_F'] = r"8.000"
        #self.subst_dict['prop']['MMCM_CLKOUT0_DIVIDE_F'] = r"50.000"
        #self.subst_dict['prop']['MMCM_CLKOUT1_DIVIDE'] = r"10"
        #self.subst_dict['prop']['MMCM_CLKOUT2_DIVIDE'] = r"50"
        #self.subst_dict['prop']['NUM_OUT_CLKS'] = r"3"
        #self.subst_dict['prop']['CLKOUT1_JITTER'] = r"172.798"
        #self.subst_dict['prop']['CLKOUT1_PHASE_ERROR'] = r"96.948"
        #self.subst_dict['prop']['CLKOUT2_JITTER'] = r"124.615"
        #self.subst_dict['prop']['CLKOUT2_PHASE_ERROR'] = r"96.948"
        #self.subst_dict['prop']['CLKOUT3_JITTER'] = r"172.798"
        #self.subst_dict['prop']['CLKOUT3_PHASE_ERROR'] = r"96.948"

    def generate(self):
        self._generate(subst_dict=self.subst_dict, template_name=self.template_name)

class Vio_gen(Ip_cores_gen):
    """
    tbd
    """
    def __init__(self, project_root, template_dir=r"ip_cores", template_name=r"templ_vio.txt", ip_name=r"vio", build_dir=None):
        Ip_cores_gen.__init__(self, project_root, template_dir, template_name, ip_name, build_dir)

        # IP Core specific properties
        self.subst_dict['prop'] = {}
        #self.subst_dict['prop']['C_PROBE_OUT0_INIT_VAL'] = r"0x1"
        #self.subst_dict['prop']['C_PROBE_OUT2_WIDTH'] = r"24"
        #self.subst_dict['prop']['C_PROBE_OUT1_WIDTH'] = r"32"
        #self.subst_dict['prop']['C_NUM_PROBE_OUT'] = r"3"
        #self.subst_dict['prop']['C_EN_PROBE_IN_ACTIVITY'] = r"0"
        #self.subst_dict['prop']['C_NUM_PROBE_IN'] = r"0"

    def generate(self):
        self._generate(subst_dict=self.subst_dict, template_name=self.template_name)

class ILA_gen(Template_gen):
    """
        self.subst_dict['probes'] = {}
        self.subst_dict['probes']['probe0'] = {}
        self.subst_dict['probes']['probe0']['conn'] = r"flyback_i/i_mag"
        self.subst_dict['probes']['probe0']['width'] = r"25"

        self.subst_dict['probes']['probe1'] = {}
        self.subst_dict['probes']['probe1']['conn'] = r"flyback_i/v_cs"
        self.subst_dict['probes']['probe1']['width'] = r"25"
    """
    def __init__(self, project_root, inst_name, constr_name, template_dir=r"const_append", template_name=r"templ_ila_append.txt", ip_name=r"ila"):
        Template_gen.__init__(self, project_root, template_dir, template_name)

        self.constr_name = constr_name
        self.source_path = join(self.project_root, r"source", r"constraints", self.constr_name)

        self.build_path = join(self.project_root, r"build", r"constraints", self.constr_name)



        # IP Core specific properties
        self.subst_dict['ip_name'] = ip_name
        self.subst_dict['inst_name'] = inst_name

        self.subst_dict['ila_prop'] = {}
        self.subst_dict['ila_prop']['ALL_PROBE_SAME_MU'] = r"true"
        self.subst_dict['ila_prop']['ALL_PROBE_SAME_MU_CNT'] = r"1"
        self.subst_dict['ila_prop']['C_ADV_TRIGGER'] = r"false"
        self.subst_dict['ila_prop']['C_DATA_DEPTH'] = r"16384"
        self.subst_dict['ila_prop']['C_EN_STRG_QUAL'] = r"false"
        self.subst_dict['ila_prop']['C_INPUT_PIPE_STAGES'] = r"0"
        self.subst_dict['ila_prop']['C_TRIGIN_EN'] = r"false"
        self.subst_dict['ila_prop']['C_TRIGOUT_EN'] = r"false"

        self.subst_dict['dbg_hub_prop'] = {}
        self.subst_dict['dbg_hub_prop']['C_CLK_INPUT_FREQ_HZ'] = r"300000000"
        self.subst_dict['dbg_hub_prop']['C_ENABLE_CLK_DIVIDER'] = r"false"
        self.subst_dict['dbg_hub_prop']['C_USER_SCAN_CHAIN'] = r"1"

        self.subst_dict['probes'] = {}
        #self.subst_dict['probes']['probe0'] = {}
        #self.subst_dict['probes']['probe0']['conn'] = r"flyback_i/i_mag"
        #self.subst_dict['probes']['probe0']['width'] = r"25"

        #self.subst_dict['probes']['probe1'] = {}
        #self.subst_dict['probes']['probe1']['conn'] = r"flyback_i/v_cs"
        #self.subst_dict['probes']['probe1']['width'] = r"25"

        #self.subst_dict['probes']['probe2'] = {}
        #self.subst_dict['probes']['probe2']['conn'] = r"flyback_i/v_in"
        #self.subst_dict['probes']['probe2']['width'] = r"25"

        #self.subst_dict['probes']['probe3'] = {}
        #self.subst_dict['probes']['probe3']['conn'] = r"flyback_i/v_out"
        #self.subst_dict['probes']['probe3']['width'] = r"25"

        #self.subst_dict['probes']['probe4'] = {}
        #self.subst_dict['probes']['probe4']['conn'] = r"flyback_i/v_vcc"
        #self.subst_dict['probes']['probe4']['width'] = r"25"

        #self.subst_dict['probes']['probe5'] = {}
        #self.subst_dict['probes']['probe5']['conn'] = r"flyback_i/v_vs"
        #self.subst_dict['probes']['probe5']['width'] = r"25"

        #self.subst_dict['probes']['probe6'] = {}
        #self.subst_dict['probes']['probe6']['conn'] = r"flyback_i/v_zcd"
        #self.subst_dict['probes']['probe6']['width'] = r"25"

        #self.subst_dict['probes']['probe7'] = {}
        #self.subst_dict['probes']['probe7']['conn'] = r"flyback_i/gate"
        #self.subst_dict['probes']['probe7']['width'] = r"1"

        #self.subst_dict['probes']['probe8'] = {}
        #self.subst_dict['probes']['probe8']['conn'] = r"ila_samp_en"
        #self.subst_dict['probes']['probe8']['width'] = r"1"

        #self.subst_dict['probes']['probe9'] = {}
        #self.subst_dict['probes']['probe9']['conn'] = r"ila_trigger"
        #self.subst_dict['probes']['probe9']['width'] = r"1"

        #self.subst_dict['probes']['probe10'] = {}
        #self.subst_dict['probes']['probe10']['conn'] = r"flyback_i/rst"
        #self.subst_dict['probes']['probe10']['width'] = r"1"

        self.subst_dict['conn_dbg_clk'] = r"dbg_clk"
        self.subst_dict['width_ila_clk'] = r"1"
        self.subst_dict['conn_ila_clk'] = r"clkgen_i/clk_wiz_0_i/inst/clk_out3"


    def generate(self):
        template = self.env.get_template(self.template_name)
        output = template.render(subst=self.subst_dict)
        print(output)
        with open(self.source_path, 'r') as fh:
            content = fh.read()

        with open(self.build_path, 'w') as fh:
            fh.write(content)
            fh.write(output)

def main():
    # parse command line arguments
    parser = ArgumentParser()

    parser.add_argument('-i', '--input', type=str, default=None)
    parser.add_argument('-o', '--output', type=str, default=None)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--float', action='store_true')

    args = parser.parse_args()

    # expand path of input directory
    args.input = get_full_path(args.input)

    ###############
    # template generation
    ###############

    if isfile(args.input):
        call_python([args.input, '-o', args.output])

if __name__ == "__main__":
    main()


#test
#prj_root = r"C:\Inicio_dev\fpga_framework\test_project"

#gen_clk = Clk_wiz_gen(project_root = prj_root)
#gen_clk.generate()

#gen_vio = Vio_gen(project_root = prj_root)
#gen_vio.generate()

#gen_ila_append = ILA_gen(project_root = prj_root, inst_name=r"u_ila_0", constr_name=r"orig_constr.xdc")
#gen_ila_append.generate()