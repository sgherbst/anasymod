import os.path
from argparse import ArgumentParser

from msdsl import MixedSignalModel, VerilogGenerator, DigitalOutput, DigitalInput

from anasymod.files import get_full_path

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    parser.add_argument('--dt', type=float)
    args = parser.parse_args()

    # create the model
    model = MixedSignalModel('bitwise', DigitalInput('a'), DigitalInput('b'), DigitalOutput('a_and_b'),
                             DigitalOutput('a_or_b'), DigitalOutput('a_xor_b'), DigitalOutput('a_inv'),
                             DigitalOutput('b_inv'), dt=args.dt)
    model.set_this_cycle(model.a_and_b, model.a & model.b)
    model.set_this_cycle(model.a_or_b, model.a | model.b)
    model.set_this_cycle(model.a_xor_b, model.a ^ model.b)
    model.set_this_cycle(model.a_inv, ~model.a)
    model.set_this_cycle(model.b_inv, ~model.b)

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), f'{model.module_name}.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_to_file(VerilogGenerator(), filename)

if __name__ == '__main__':
    main()