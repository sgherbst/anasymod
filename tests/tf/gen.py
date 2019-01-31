import os.path
import json
from argparse import ArgumentParser

from msdsl.model import MixedSignalModel
from msdsl.verilog import VerilogGenerator
from msdsl.expr import AnalogInput, AnalogOutput

from anasymod.files import get_full_path

def main(num=(1e12,), den=(1, 8e5, 1e12,)):
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    args = parser.parse_args()

    # load config options
    config_file_path = os.path.join(os.path.dirname(get_full_path(__file__)), 'config.json')
    config = json.load(open(config_file_path, 'r'))

    # create the model
    model = MixedSignalModel('filter', AnalogInput('v_in'), AnalogOutput('v_out'), dt=config['dt'])
    model.set_tf(model.v_out, model.v_in, (num, den))

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), 'filter.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_model(VerilogGenerator(filename))

if __name__ == '__main__':
    main()