import os.path
from argparse import ArgumentParser

from msdsl import MixedSignalModel, VerilogGenerator, AnalogInput, AnalogOutput
from anasymod import get_full_path

def main(num=(1e12,), den=(1, 8e5, 1e12,)):
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    parser.add_argument('--dt', type=float)
    args = parser.parse_args()

    # create the model
    model = MixedSignalModel('filter', AnalogInput('v_in'), AnalogOutput('v_out'), dt=args.dt)
    model.set_tf(input_=model.v_in, output=model.v_out, tf=(num, den))

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), f'{model.module_name}.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_to_file(VerilogGenerator(), filename)

if __name__ == '__main__':
    main()