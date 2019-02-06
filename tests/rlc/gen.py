import os.path
from argparse import ArgumentParser

from msdsl.model import MixedSignalModel
from msdsl.verilog import VerilogGenerator
from msdsl.expr import AnalogInput, AnalogOutput, AnalogSignal, Deriv

from anasymod.files import get_full_path
from anasymod.util import json2obj

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    args = parser.parse_args()

    # load config options
    config_file_path = os.path.join(os.path.dirname(get_full_path(__file__)), 'config.json')
    cfg = json2obj(open(config_file_path, 'r').read())

    # create the model
    model = MixedSignalModel('rlc', AnalogInput('v_in'), AnalogOutput('v_out'), dt=cfg.dt)
    model.add_signal(AnalogSignal('i_ind', 100))

    # internal variables
    v_l = AnalogSignal('v_l')
    v_r = AnalogSignal('v_r')

    # define dynamics
    eqns = [
        Deriv(model.i_ind) == v_l/cfg.ind,
        Deriv(model.v_out) == model.i_ind / cfg.cap,
        v_r == model.i_ind*cfg.res,
        model.v_in == model.v_out + v_l + v_r
    ]
    model.add_eqn_sys(eqns=eqns, states=[model.i_ind, model.v_out], inputs=[model.v_in], internals=[v_l, v_r])

    # define probes
    model.add_probe(model.i_ind)

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), f'{model.name}.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_model(VerilogGenerator(filename))

if __name__ == '__main__':
    main()