import os.path
from argparse import ArgumentParser

from msdsl import MixedSignalModel, VerilogGenerator, DigitalInput, DigitalOutput
from anasymod import get_full_path

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    parser.add_argument('--dt', type=float, default=0.1e-6)
    args = parser.parse_args()

    # create the model
    m = MixedSignalModel('inertial', DigitalInput('in_'), DigitalOutput('out'), dt=args.dt)
    m.set_this_cycle(m.out, m.inertial_delay(m.in_, tr=42e-6, tf=0e-6))

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), f'{m.module_name}.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    m.compile_to_file(VerilogGenerator(), filename)

if __name__ == '__main__':
    main()