from os.path import dirname, join, exists, isfile
from os import makedirs
from argparse import ArgumentParser

from ip_core_gen.ip_core_gen import Clk_wiz_gen, Vio_gen

def main():
    # parse command line arguments
    parser = ArgumentParser()

    parser.add_argument('-r', '--root', type=str, default=None)
    parser.add_argument('-o', '--output', type=str, default=None)
    parser.add_argument('--debug', action='store_true')

    args = parser.parse_args()

    # Specify templates to be generated

    clk_0 = Clk_wiz_gen(project_root=args.root, ip_name=r"clk_wiz_0", )
    clk_0.subst_dict['prop']['PRIMITIVE'] = r"PLL"
    clk_0.subst_dict['prop']['PRIM_IN_FREQ'] = r"125.000"
    clk_0.subst_dict['prop']['CLKOUT1_USED'] = r"true"
    clk_0.subst_dict['prop']['CLKOUT1_REQUESTED_OUT_FREQ'] = r"50.000"
    clk_0.subst_dict['prop']['NUM_OUT_CLKS'] = r"1"


    vio_0 = Vio_gen(project_root=args.root, ip_name=r"vio_0")
    vio_0.subst_dict['prop']['C_PROBE_OUT0_INIT_VAL'] = r"0x1"
    vio_0.subst_dict['prop']['C_PROBE_OUT0_WIDTH'] = r"1"
    vio_0.subst_dict['prop']['C_NUM_PROBE_OUT'] = r"1"
    vio_0.subst_dict['prop']['C_NUM_PROBE_IN'] = r"0"

    ###############
    # template generation
    ###############

    clk_0.generate()
    vio_0.generate()

if __name__ == "__main__":
    main()