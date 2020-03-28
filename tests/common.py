import os
from argparse import ArgumentParser

from anasymod.analysis import Analysis

DEFAULT_SIMULATOR = 'icarus' if 'FPGA_SERVER' not in os.environ else 'vivado'

def run_simulation(root, simulator_name):
    # create analysis object
    ana = Analysis(input=root,
                   simulator_name=simulator_name)

    # generate functional models
    ana.msdsl.models()

    # setup project's filesets
    ana.setup_filesets()

    # run the simulation
    ana.simulate()

    # declare success
    print('Success!')

def run_emulation(root, gen_bitstream, emu_ctrl_fun=None):
    # create analysis object
    ana = Analysis(input=root)

    # generate functional models
    ana.msdsl.models()
    ana.setup_filesets()
    ana.set_target(target_name='fpga')  # set the active target to 'fpga'

    # generate the bitstream if desired
    if gen_bitstream:
        ana.build()  # generate bitstream for project

    # run the specific emulation sequence if desired
    if emu_ctrl_fun is not None:
        ctrl = ana.launch(debug=True)  # start interactive control
        emu_ctrl_fun(ctrl)

    # declare success
    print('Success!')

class CommonArgParser(ArgumentParser):
    def __init__(self, sim_fun, emu_fun, *args, **kwargs):
        # call the super constructor
        super().__init__(*args, **kwargs)

        # parse command-line arguments
        self.add_argument('--sim', action='store_true')
        self.add_argument('--emulate', action='store_true')
        self.add_argument('--gen_bitstream', action='store_true')
        self.add_argument('--simulator_name', type=str, default=DEFAULT_SIMULATOR)
        args = self.parse_args()

        # run actions as requested
        if args.sim:
            print('Running simulation...')
            sim_fun(simulator_name=args.simulator_name)
        if args.emulate:
            print('Running emulation...')
            emu_fun(gen_bitstream=args.gen_bitstream)