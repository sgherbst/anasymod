import os.path
import json
from argparse import ArgumentParser
from math import sqrt

from msdsl.model import MixedSignalModel
from msdsl.verilog import VerilogGenerator
from msdsl.expr import AnalogInput, AnalogOutput, AnalogSignal, Min

from anasymod.files import get_full_path

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', default='.', type=str)
    args = parser.parse_args()

    # load config options
    config_file_path = os.path.join(os.path.dirname(get_full_path(__file__)), 'config.json')
    config = json.load(open(config_file_path, 'r'))

    # make aliases for config options
    l_tx = config['l_tx']
    l_rx = config['l_rx']
    r_rx = config['r_rx']
    c_rx = config['c_rx']
    coupling = config['coupling']
    tau_hpf = config['tau_hpf']

    # calculate derived parameters
    m = coupling*sqrt(l_tx*l_rx)

    # create the model
    model = MixedSignalModel('nfc', AnalogInput('v_tx'), AnalogOutput('v_hpf'), dt=config['dt'])
    model.add_signal(AnalogSignal('v_cap', range=25))
    model.add_signal(AnalogSignal('i_rx', range=5))

    # model dynamics

    # i_rx
    deriv_i_rx = (1/(l_rx-(m**2)/l_tx))*model.v_cap + ((-m/l_tx)/(l_rx-(m**2)/l_tx))*model.v_tx
    next_i_rx = Min([model.i_rx + deriv_i_rx*config['dt'], 0])
    model.set_next_cycle(model.i_rx, next_i_rx)

    # v_cap
    model.set_deriv(model.v_cap, model.i_rx*(-1/c_rx) + model.v_cap*(-1/(r_rx*c_rx)))

    # add HPF
    model.set_tf(model.v_hpf, model.v_cap, ([tau_hpf, 0], [tau_hpf, 1]))

    # probe signals of interest
    model.add_probe(model.i_rx)
    model.add_probe(model.v_cap)

    # determine the output filename
    if args.output is not None:
        filename = os.path.join(get_full_path(args.output), 'nfc.sv')
        print('Model will be written to: ' + filename)
    else:
        filename = None

    # generate the model
    model.compile_model(VerilogGenerator(filename))

if __name__ == '__main__':
    main()