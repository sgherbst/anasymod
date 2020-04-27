from math import exp
from pathlib import Path
from argparse import ArgumentParser
from msdsl import MixedSignalModel, VerilogGenerator

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str, default='build')
    parser.add_argument('--dt', type=float, default=0.1e-6)
    parser.add_argument('--tau', type=float, default=1.0e-6)
    a = parser.parse_args()

    # create the model
    m = MixedSignalModel('model', dt=a.dt)
    m.add_analog_input('v_in')
    m.add_analog_output('v_out')

    # apply dynamics
    # TODO: clean up with update to MSDSL
    class ce:
        name = '`CKE_MSDSL'
    m.set_next_cycle(m.v_out, m.v_out*exp(-a.dt/a.tau) + m.v_in*(1-exp(-a.dt/a.tau)), ce=ce)

    # determine the output filename
    filename = Path(a.output).resolve() / f'{m.module_name}.sv'
    print(f'Model will be written to: {filename}')

    # generate the model
    m.compile_to_file(VerilogGenerator(), filename)

if __name__ == '__main__':
    main()
