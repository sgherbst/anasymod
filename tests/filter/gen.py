import os.path
import json
from argparse import ArgumentParser

from msdsl.model import MixedSignalModel
from msdsl.verilog import VerilogGenerator
from msdsl.expr import AnalogInput, AnalogOutput, Deriv

from anasymod.util import json2obj
from anasymod.files import get_full_path

def main(tau=1e-6):
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    args = parser.parse_args()

    # load config options
    config_file_path = os.path.join(os.path.dirname(get_full_path(__file__)), 'config.json')
    cfg = json2obj(open(config_file_path, 'r').read())

    # create the model
    model = MixedSignalModel('filter', AnalogInput('v_in'), AnalogOutput('v_out'), dt=cfg.dt)
    model.add_eqn_sys(eqns=[Deriv(model.v_out) == (model.v_in - model.v_out) / tau], inputs=[model.v_in],
                      states=[model.v_out])

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), 'filter.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_model(VerilogGenerator(filename))

if __name__ == '__main__':
    main()