import os

from anasymod.analysis import Analysis
from argparse import ArgumentParser
from time import sleep

root = os.path.dirname(__file__)

def parse():
    parser = ArgumentParser()
    parser.add_argument('--gen_bitstream', action='store_true')
    return parser.parse_args()

def main():
    result_file = r'./results/dummy.vcd'

    args = parse()
    ana = Analysis(input=root)                              # create analysis object to host prototyping project

    ana.set_target(target_name='fpga')                      # set the active target to 'fpga'

    if args.gen_bitstream:
        ana.gen_sources()                                   # generate functional models
        ana.build()                                         # generate bitstream for project

    ctrl_handle = ana.launch(debug=True)                    # start interactive control
    ctrl_handle.set_reset(1)                                # reset simulation
    ctrl_handle.setup_trace_unit(trigger_name='time',
                                 trigger_operator='gt',
                                 trigger_value=1e-9,
                                 sample_decimation=0,
                                 )           # config & arm trace unit

    #ctrl_handle.set_param('emu_ctrl_data', 10000000)
    #ctrl_handle.set_param('emu_ctrl_mode', 3)

    ctrl_handle.set_param('emu_ctrl_mode', 1)
    ctrl_handle.set_reset(0)                                # start simulation
    #sleep(0.1)
    time = ctrl_handle.get_emu_time()
    print(f'Paused at:{time}')
    ctrl_handle.sleep_emu(1e-6)
    #sleep(0.1)
    time = ctrl_handle.get_emu_time()
    print(f'Paused at:{time}')
    ctrl_handle.sleep_emu(1e-6)
    #sleep(0.1)
    time = ctrl_handle.get_emu_time()
    print(f'Paused at:{time}')
    ctrl_handle.sleep_emu(1e-6)
    #sleep(0.1)
    time = ctrl_handle.get_emu_time()
    print(f'Paused at:{time}')
    ctrl_handle.sleep_emu(1e-6)
    #sleep(0.1)
    time = ctrl_handle.get_emu_time()
    print(f'Paused at:{time}')

    ctrl_handle.wait_on_and_dump_trace(result_file=result_file)                    # wait till trace buffer is full and dump to result file
    ana.view(result_file=result_file)                                              # view waveform

if __name__ == "__main__":
    main()