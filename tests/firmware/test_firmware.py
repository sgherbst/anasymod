import os
import pytest
import subprocess
import shutil
import serial
from pathlib import Path

root = Path(__file__).resolve().parent

from ..common import run_simulation, run_emulation, DEFAULT_SIMULATOR

def test_1(simulator_name=DEFAULT_SIMULATOR):
    # run simulation
    run_simulation(root=root, simulator_name=simulator_name)

@pytest.mark.skipif(
    'FPGA_SERVER' not in os.environ,
    reason='The FPGA_SERVER environment variable must be set to run this test.'
)
def test_2(gen_bitstream=True):
    # build bitstream
    run_emulation(root=root, gen_bitstream=gen_bitstream, emulate=False)

@pytest.mark.skipif(
    'FPGA_SERVER' not in os.environ,
    reason='The FPGA_SERVER environment variable must be set to run this test.'
)
def test_3(top_name='top'):
    # export hardware
    sdk_path = root / 'build' / 'fpga' / 'prj' / 'prj.sw'
    sdk_path.mkdir(exist_ok=True, parents=True)

    sysdef_path = root / 'build' / 'fpga' / 'prj' / 'prj.runs' / 'impl_1' / f'{top_name}.sysdef'
    hdf_path = sdk_path / f'{top_name}.hdf'

    shutil.copy(str(sysdef_path), str(hdf_path))

@pytest.mark.skipif(
    'FPGA_SERVER' not in os.environ,
    reason='The FPGA_SERVER environment variable must be set to run this test.'
)
def test_4():
    # build ELF
    tcl_path = root / 'build' / 'tcl'
    tcl_path.mkdir(exist_ok=True, parents=True)

    with open(tcl_path / 'sdk.tcl', 'w') as f:
        f.write(sdk_script())

    subprocess.run(['xsct', tcl_path / 'sdk.tcl'])

@pytest.mark.skipif(
    'FPGA_SERVER' not in os.environ,
    reason='The FPGA_SERVER environment variable must be set to run this test.'
)
def test_5():
    # download program
    tcl_path = root / 'build' / 'tcl'
    tcl_path.mkdir(exist_ok=True, parents=True)

    with open(tcl_path / 'program.tcl', 'w') as f:
        f.write(program_script())

    subprocess.run(['xsct', tcl_path / 'program.tcl'])

@pytest.mark.skipif(
    'FPGA_SERVER' not in os.environ,
    reason='The FPGA_SERVER environment variable must be set to run this test.'
)
def test_6():
    # run UART test
    ser = serial.Serial(
        port='/dev/ttyUSB0',
        baudrate=115200
    )

    # simple test
    ser.write(f'HELLO\n'.encode('utf-8'))
    out = ser.readline().decode('utf-8').strip()
    print(f'Got output: "{out}"')
    if out != 'Hello World!':
        raise Exception('Output mismatch.')

    # detailed test
    def run_test(a, b, mode, expct):
        # write inputs
        ser.write(f'SET_A {a}\n'.encode('utf-8'))
        ser.write(f'SET_B {b}\n'.encode('utf-8'))
        ser.write(f'SET_MODE {mode}\n'.encode('utf-8'))

        # get output
        ser.write('GET_C\n'.encode('utf-8'))
        out = ser.readline().decode('utf-8').strip()
        c = int(out)

        print(f'a={a}, b={b}, mode={mode} -> c={c} (expct={expct})')

        if c != expct:
            raise Exception('Output mismatch.')

    # try out different operating modes
    run_test(12, 34, 0, 46)
    run_test(45, 10, 1, 35)
    run_test(10, 44, 2, 34)
    run_test(3, 7, 3, 21)
    run_test(9, 1, 4, 4)
    run_test(9, 1, 5, 18)
    run_test(2, 32, 6, 8)
    run_test(3, 3, 7, 24)
    run_test(56, 78, 8, 42)

    # quit the program
    print('Quitting the program...')
    ser.write('EXIT\n'.encode('utf-8'))

def sdk_script(proc_name='ps7_cortexa9_0', hw_name='hw', top_name='top', sw_name='sw'):
    sdk_path = root / 'build' / 'fpga' / 'prj' / 'prj.sw'
    firmware_dir = root / 'firmware'

    return f'''\
# set the work directory
setws "{sdk_path}"

# create the hardware configuration
createhw \\
    -name {hw_name} \\
    -hwspec "{sdk_path / top_name}.hdf"

# create the software configuration
createapp \\
    -name {sw_name} \\
    -hwproject {hw_name} \\
    -proc {proc_name} \\
    -app "Empty Application"

# import sources
importsources \\
    -name {sw_name} \\
    -path {firmware_dir}

# build application
projects -build
'''

def program_script(cpu_filter='"ARM*#0"', hw_name='hw', top_name='top', sw_name='sw'):
    sdk_path = root / 'build' / 'fpga' / 'prj' / 'prj.sw'

    return f'''\
# References:
# 1. https://www.xilinx.com/html_docs/xilinx2018_1/SDK_Doc/xsct/use_cases/xsdb_standalone_app_debug.html
# 2. https://github.com/Digilent/Arty-Z7-20-linux_bd/blob/master/sdk/.sdk/launch_scripts/xilinx_c-c%2B%2B_application_(system_debugger)/system_debugger_using_debug_video.elf_on_local.tcl
    
# connect to the HW server
puts "Connecting to the HW server..."
connect

# select the CPU (there are two on the Pynq)
puts "Selecting the CPU..."
targets -set -filter {{name =~ {cpu_filter}}}

# reset the system
puts "Resetting the system..."
rst

# program the FPGA
puts "Programming the FPGA..."
fpga "{sdk_path / hw_name / top_name}.bit"

# make the debugger aware of the memory map
# TODO: is this needed?
puts "Setting up the debugger..."
loadhw "{sdk_path / top_name}.hdf"

# initialize the processor
puts "Initializing the processor..."
source "{sdk_path / hw_name / 'ps7_init'}.tcl"
ps7_init
ps7_post_config

# download the program
puts "Downloading the program..."
dow "{sdk_path / sw_name / 'Debug' / sw_name}.elf"

# run program
puts "Starting the program..."
con

# print message for debugging purposes
puts "Program started."'''