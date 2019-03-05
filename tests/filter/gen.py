import os.path
from argparse import ArgumentParser

from msdsl.model import MixedSignalModel
from msdsl.generator.verilog import VerilogGenerator
from msdsl.expr.signals import AnalogInput, AnalogOutput
from msdsl.eqn.deriv import Deriv

from anasymod.files import get_full_path

def main(tau=1e-6):
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    parser.add_argument('--dt', type=float)
    args = parser.parse_args()

    # create the model
    model = MixedSignalModel('filter', AnalogInput('v_in'), AnalogOutput('v_out'), dt=args.dt)
    model.add_eqn_sys(eqns=[Deriv(model.v_out) == (model.v_in - model.v_out) / tau])

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), f'{model.module_name}.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_to_file(VerilogGenerator(), filename)

if __name__ == '__main__':
    main()