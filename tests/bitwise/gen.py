import os.path
from argparse import ArgumentParser

from msdsl.model import MixedSignalModel
from msdsl.verilog import VerilogGenerator
from msdsl.expr import DigitalOutput, DigitalInput

from anasymod.util import json2obj
from anasymod.files import get_full_path

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    args = parser.parse_args()

    # load config options
    config_file_path = os.path.join(os.path.dirname(get_full_path(__file__)), 'config.json')
    cfg = json2obj(open(config_file_path, 'r').read())

    # create the model
    model = MixedSignalModel('bitwise', DigitalInput('a'), DigitalInput('b'), DigitalOutput('a_and_b'),
                             DigitalOutput('a_or_b'), DigitalOutput('a_xor_b'), DigitalOutput('a_inv'),
                             DigitalOutput('b_inv'), dt=cfg.dt)
    model.set_this_cycle(model.a_and_b, model.a & model.b)
    model.set_this_cycle(model.a_or_b, model.a | model.b)
    model.set_this_cycle(model.a_xor_b, model.a ^ model.b)
    model.set_this_cycle(model.a_inv, ~model.a)
    model.set_this_cycle(model.b_inv, ~model.b)

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), 'bitwise.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_model(VerilogGenerator(filename))

if __name__ == '__main__':
    main()