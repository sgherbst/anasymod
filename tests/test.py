import os
import os.path
import json

from argparse import ArgumentParser

from anasymod.config import MsEmuConfig
from anasymod.sim.vivado import VivadoSimulator
from anasymod.sim.icarus import IcarusSimulator
from anasymod.build import VivadoBuild
from anasymod.files import get_full_path, mkdir_p, rm_rf, get_from_module, which
from anasymod.util import call
from anasymod.wave import ConvertWaveform

def main():
    # parse command line arguments
    parser = ArgumentParser()

    parser.add_argument('-i', '--input', type=str, default=get_from_module('anasymod', 'tests', 'filter'))
    parser.add_argument('--simulator_name', type=str, default='icarus')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--float', action='store_true')
    parser.add_argument('--models', action='store_true')
    parser.add_argument('--sim', action='store_true')
    parser.add_argument('--view', action='store_true')
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--run_FPGA', action='store_true')
    parser.add_argument('--view_FPGA', action='store_true')

    args = parser.parse_args()

    # expand path of input and output directories
    args.input = get_full_path(args.input)

    # load configuration data
    cfg = MsEmuConfig()
    test_config = json.load(open(os.path.join(args.input, 'config.json'), 'r'))

    # test-level structure
    model_dir = os.path.join(cfg.build_dir, 'models')
    cfg.verilog_sources.append(os.path.join(model_dir, '*.sv'))
    cfg.verilog_sources.append(os.path.join(args.input, 'tb.sv'))

    # configure timing options
    cfg.set_dt(test_config['dt'])
    cfg.set_tstop(test_config['tstop'])

    # configure waveform viewing
    cfg.setup_vcd()
    cfg.setup_ila()

    # real number options
    if args.float:
        cfg.sim_only_verilog_defines.append('FLOAT_REAL')
    if args.debug:
        cfg.sim_only_verilog_defines.append('DEBUG_REAL')

    # make models if desired
    if args.models:
        # make model directory, removing the old one if necessary
        rm_rf(model_dir)
        mkdir_p(model_dir)

        # run generator script
        gen_script = os.path.join(args.input, 'gen.py')
        call([which('python'), gen_script, '-o', model_dir])

    # generate bitstream if desired
    if args.build:
        build = VivadoBuild(cfg)
        build.build()

    # run FPGA if desired
    if args.run_FPGA:
        if r"build" not in locals():
            build = VivadoBuild(cfg)
        build.run_FPGA()

    # run simulation if desired
    if args.sim:
        # pick simulator
        sim_cls = {
            'icarus': IcarusSimulator,
            'vivado': VivadoSimulator
        }[args.simulator_name]

        # run simulation
        sim = sim_cls(cfg)
        sim.simulate()

    # view results if desired
    if args.view:
        # build command
        cmd = [cfg.gtkwave_config.gtkwave, cfg.vcd_abs_path]

        # add waveform file if it exists
        gtkw_file = os.path.join(args.input, 'view.gtkw')
        if os.path.isfile(gtkw_file):
            cmd.append(gtkw_file)

        # run command
        call(cmd)

    if args.view_FPGA:
        # build command
        test = ConvertWaveform(cfg=cfg)
        cmd = [cfg.gtkwave_config.gtkwave, cfg.vcd_path]

        # run command
        print(cmd)
        call(cmd)

if __name__ == '__main__':
    main()