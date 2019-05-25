import os.path
from argparse import ArgumentParser

from msdsl.model import MixedSignalModel
from msdsl.generator.verilog import VerilogGenerator
from msdsl.expr.signals import AnalogSignal

from anasymod.files import get_full_path

def main(tau=1e-6):
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    parser.add_argument('--dt', type=float)
    args = parser.parse_args()

    # create the model
    m = MixedSignalModel('filter', dt=args.dt)

    m.add_analog_input('v_in')
    m.add_analog_output('v_out')

    c = m.make_circuit()
    gnd = c.make_ground()

    c.voltage('net_v_in', gnd, m.v_in)
    c.diode('net_v_in', 'net_v_x')
    c.resistor('net_v_x', 'net_v_out', 1e3)
    c.capacitor('net_v_out', gnd, 1e-9, voltage_range=1.5)

    c.add_eqns(
        m.v_out == AnalogSignal('net_v_out')
    )

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), f'{m.module_name}.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    m.compile_to_file(VerilogGenerator(), filename)

if __name__ == '__main__':
    main()