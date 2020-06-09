import os
import pytest
import serial
from pathlib import Path
from anasymod.analysis import Analysis

root = Path(__file__).resolve().parent

from ..common import DEFAULT_SIMULATOR

def test_1(simulator_name=DEFAULT_SIMULATOR):
    # run simulation
    ana = Analysis(input=root, simulator_name=simulator_name)
    ana.gen_sources()
    ana.simulate()

@pytest.mark.skipif(
    'FPGA_SERVER' not in os.environ,
    reason='The FPGA_SERVER environment variable must be set to run this test.'
)
def test_2():
    # build bitstream
    ana = Analysis(input=root)
    ana.set_target(target_name='fpga')  # set the active target to 'fpga'
    ana.build()

@pytest.mark.skipif(
    'FPGA_SERVER' not in os.environ,
    reason='The FPGA_SERVER environment variable must be set to run this test.'
)
def test_3():
    # build ELF
    ana = Analysis(input=root)
    ana.set_target(target_name='fpga')  # set the active target to 'fpga'
    ana.build_firmware()

@pytest.mark.skipif(
    'FPGA_SERVER' not in os.environ,
    reason='The FPGA_SERVER environment variable must be set to run this test.'
)
def test_4():
    # download program
    ana = Analysis(input=root)
    ana.set_target(target_name='fpga')  # set the active target to 'fpga'
    ana.program_firmware()

@pytest.mark.skipif(
    'FPGA_SERVER' not in os.environ,
    reason='The FPGA_SERVER environment variable must be set to run this test.'
)
def test_5():
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
