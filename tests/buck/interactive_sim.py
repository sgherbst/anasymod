import os

from anasymod.analysis import Analysis
from argparse import ArgumentParser

root = os.path.dirname(__file__)

def parse():
    parser = ArgumentParser()
    parser.add_argument('--gen_bitstream', action='store_true')
    return parser.parse_args()

def main():
    args = parse()
    ana = Analysis(input=root)                              # create analysis object to host prototyping project

    ana.gen_sources()                                      # generate functional models
    ana.set_target(target_name='fpga')                      # set the active target to 'fpga'

    if args.gen_bitstream:
        ana.build()                                         # generate bitstream for project

    ctrl_handle = ana.launch(debug=True)                    # start interactive control
    ctrl_handle.set_reset(1)                                # reset simulation
    ctrl_handle.setup_trace_unit(trigger_name='time',
                                 trigger_operator='gt',
                                 trigger_value=5.5,
                                 sample_decimation=800,
                                 sample_count=16384
                                 )           # config & arm trace unit
    ctrl_handle.set_reset(0)                                # start simulation
    ctrl_handle.wait_on_and_dump_trace()                    # wait till trace buffer is full and dump to result file
    ana.view()                                              # view waveform

if __name__ == "__main__":
    main()