from os.path import dirname, join, exists, isfile
from os import makedirs
from argparse import ArgumentParser
from ip_core_gen.ip_core_gen import Clk_wiz_gen, Vio_gen, ILA_gen

def main():
    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-r', '--root', type=str, default=r"C:\Inicio_dev\anasymod\test_project")
    parser.add_argument('-c', '--configfile', type=str, default=r"C:\Inicio_dev\anasymod\test_project\build\test_project\probe_config.txt")
    parser.add_argument('--debug', action='store_true')

    args = parser.parse_args()

    # Read Probe Config file
    with (open(args.configfile, "r")) as cf:
        config = cf.readlines()

    cfg_dict = {}
    cfg_dict['sb'] = config[0].strip(r"SB:").strip().split()
    cfg_dict['mb'] = config[1].strip(r"MB:").strip().split()
    cfg_dict['mb_exponent'] = config[2].strip(r"MB_EXPONENT:").strip().split()
    cfg_dict['mb_width'] = config[3].strip(r"MB_WIDTH:").strip().split()


    # Specify templates to be generated
    ila_0 = ILA_gen(project_root=args.root, ip_name=r"ila_0", constr_name=r"constr.xdc", inst_name=r"u_ila_0")

    count = 0

    # Add single bit probes
    for conn in cfg_dict['sb']:
        ila_0.subst_dict['probes']['probe{0}'.format(count)] = {}
        ila_0.subst_dict['probes']['probe{0}'.format(count)]['conn'] = r"{0}".format(conn)
        ila_0.subst_dict['probes']['probe{0}'.format(count)]['width'] = r"1"
        count += 1

    # Add multi bit probes
    for conn, width in zip(cfg_dict['mb'], cfg_dict['mb_width']):
        ila_0.subst_dict['probes']['probe{0}'.format(count)] = {}
        ila_0.subst_dict['probes']['probe{0}'.format(count)]['conn'] = r"{0}".format(conn)
        ila_0.subst_dict['probes']['probe{0}'.format(count)]['width'] = r"{0}".format(width)
        count += 1

    ###############
    # template generation
    ###############

    ila_0.generate()

if __name__ == "__main__":
    main()