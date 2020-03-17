from pathlib import Path
from argparse import ArgumentParser
from msdsl import (MixedSignalModel, VerilogGenerator, Deriv)

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str, default='build')
    parser.add_argument('--dt', type=float, default=0.1e-6)
    parser.add_argument('--tau', type=float, default=1.0e-6)
    args = parser.parse_args()

    # create the model
    m = MixedSignalModel('model', dt=args.dt)
    m.add_analog_input('v_in')
    m.add_analog_output('v_out')
    m.add_digital_input('clk')
    m.add_digital_input('rst')
    m.add_eqn_sys([Deriv(m.v_out) == (m.v_in - m.v_out)/args.tau],
                  clk=m.clk, rst=m.rst)

    # determine the output filename
    filename = Path(args.output).resolve() / f'{m.module_name}.sv'
    print(f'Model will be written to: {filename}')

    # generate the model
    m.compile_to_file(VerilogGenerator(), filename)

if __name__ == '__main__':
    main()
