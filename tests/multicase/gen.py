import os.path
import json
from argparse import ArgumentParser

from msdsl.model import MixedSignalModel
from msdsl.verilog import VerilogGenerator
from msdsl.expr import AnalogInput, DigitalInput, AnalogOutput, Deriv, Case

from anasymod.files import get_full_path

def main(tau=1e-6):
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    args = parser.parse_args()

    # load config options
    config_file_path = os.path.join(os.path.dirname(get_full_path(__file__)), 'config.json')
    config = json.load(open(config_file_path, 'r'))

    # create the model
    model = MixedSignalModel('filter', DigitalInput('ctrl'), AnalogInput('v_in'), AnalogOutput('v_out'),
                             dt=config['dt'])

    # define dynamics
    model.add_eqn_sys([
        Deriv(model.v_out) == Case([0, 1/tau], [model.ctrl])*model.v_in - model.v_out/tau
    ], states=[model.v_out], inputs=[model.v_in], sel_bits=[model.ctrl])

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), 'filter.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_model(VerilogGenerator(filename))

if __name__ == '__main__':
    main()