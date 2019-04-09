import os.path
from argparse import ArgumentParser

from msdsl.model import MixedSignalModel
from msdsl.generator.verilog import VerilogGenerator
from msdsl.expr.signals import AnalogInput, AnalogOutput
from msdsl.eqn.deriv import Deriv

from anasymod.files import get_full_path

class Filter(MixedSignalModel):
    def __init__(self, name='filter', tau=1e-6, dt=0.1e-6):
        # call the super constructor
        super().__init__(name, dt=dt)

        # define IOs
        self.add_analog_input('v_in')
        self.add_analog_output('v_out')

        # define dynamics
        self.add_eqn_sys([
            Deriv(self.v_out) == (self.v_in - self.v_out) / tau
        ])

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    parser.add_argument('--dt', type=float)
    args = parser.parse_args()

    # create the model
    model = Filter(dt=args.dt)

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), f'{model.module_name}.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_to_file(VerilogGenerator(), filename)

if __name__ == '__main__':
    main()
