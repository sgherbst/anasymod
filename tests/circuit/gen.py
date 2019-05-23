import os.path
from argparse import ArgumentParser

from msdsl.expr.svreal import RangeOf
from msdsl.expr.signals import AnalogSignal

from msdsl.model import MixedSignalModel
from msdsl.generator.verilog import VerilogGenerator

from anasymod.files import get_full_path

class Filter(MixedSignalModel):
    def __init__(self, name='filter', res=1e3, cap=1e-9, dt=0.1e-6):
        # call the super constructor
        super().__init__(name, dt=dt)

        # define I/O
        self.add_analog_input('v_in')
        self.add_analog_output('v_out')

        c = self.make_circuit()
        gnd = c.make_ground()

        c.capacitor('net_v_out', gnd, cap, voltage_range=RangeOf(self.v_out))
        c.resistor('net_v_in', 'net_v_out', res)
        c.voltage('net_v_in', gnd, self.v_in)

        c.add_eqns(
            AnalogSignal('net_v_out') == self.v_out
        )

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