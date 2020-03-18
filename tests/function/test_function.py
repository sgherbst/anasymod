import os
import numpy as np
from argparse import ArgumentParser
from time import sleep

from anasymod.analysis import Analysis

root = os.path.dirname(__file__)

def myfunc(x):
    # clip input
    x = np.clip(x, -np.pi, +np.pi)
    # apply function
    return np.sin(x)

def test_func_sim(simulator_name='vivado'):
    # create analysis object
    ana = Analysis(input=root,
                   simulator_name=simulator_name)
    # generate functional models
    ana.msdsl.models()
    # setup project's filesets
    ana.setup_filesets()
    # run the simulation
    ana.simulate()

def test_func_emu(gen_bitstream=True):
    # create analysis object
    ana = Analysis(input=root)
    # generate functional models
    ana.msdsl.models()
    ana.setup_filesets()
    ana.set_target(target_name='fpga')      # set the active target to 'fpga'

    if gen_bitstream:
        ana.build()                         # generate bitstream for project

    ctrl = ana.launch(debug=True)           # start interactive control

    # reset emulator
    ctrl.set_reset(1)
    sleep(0.1)
    ctrl.set_reset(0)
    sleep(0.1)

    # reset everything else
    ctrl.set_param(name='in_', value=0.0)

    # save the outputs
    inpts = np.random.uniform(-1.2*np.pi, +1.2*np.pi, 100)
    apprx = np.zeros(shape=inpts.shape, dtype=float)
    for k, in_ in enumerate(inpts):
        ctrl.set_param(name='in_', value=in_)
        sleep(1e-3)
        ctrl.refresh_param('vio_0_i')
        apprx[k] = ctrl.get_param('out')

    # compute the exact response to inputs
    exact = myfunc(inpts)

    # check the result
    err = np.linalg.norm(exact-apprx)
    assert err <= 0.001

if __name__ == "__main__":
    # parse command-line arguments
    parser = ArgumentParser()
    parser.add_argument('--sim', action='store_true')
    parser.add_argument('--emulate', action='store_true')
    parser.add_argument('--gen_bitstream', action='store_true')
    parser.add_argument('--simulator_name', type=str, default=None)
    args = parser.parse_args()

    # run actions as requested
    if args.sim:
        print('Running simulation...')
        test_func_sim(simulator_name=args.simulator_name)
    if args.emulate:
        print('Running emulation...')
        test_func_emu(gen_bitstream=args.gen_bitstream)
