import os.path
import numpy as np
from argparse import ArgumentParser

from msdsl.model import MixedSignalModel
from msdsl.verilog import VerilogGenerator
from msdsl.expr import AnalogInput, AnalogOutput, AnalogSignal

from anasymod.files import get_full_path
from anasymod.util import DictObject

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    args = parser.parse_args()

    # load config options
    config_file_path = os.path.join(os.path.dirname(get_full_path(__file__)), 'config.json')
    cfg = DictObject.load_json(config_file_path)

    # create the model
    model = MixedSignalModel('rlc', AnalogInput('v_in'), AnalogOutput('v_out'), dt=cfg.dt)
    model.add_signal(AnalogSignal('i_ind', 100))

    # define model dynamics
    A = np.array([[-cfg.res/cfg.ind, -1/cfg.ind], [1/cfg.cap, 0]], dtype=float)
    B = np.array([[1/cfg.ind], [0]], dtype=float)
    model.add_lds((A, B, 0, 0), inputs=[model.v_in], states=[model.i_ind, model.v_out])

    # define probes
    model.add_probe(model.i_ind)

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), f'{model.name}.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_model(VerilogGenerator(filename))

if __name__ == '__main__':
    main()