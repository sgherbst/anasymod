from time import sleep
from math import exp
import os

from anasymod.vivado_tcl import VivadoTCL

ANALOG_EXPONENT = -18

def float_to_fixed(x):
    return int(x * (2.0**(-ANALOG_EXPONENT)))

def fixed_to_float(x):
    return x * (2.0**(ANALOG_EXPONENT))

def test_rc(mock=False):
    # start TCL interpreter
    tcl = VivadoTCL(debug=True, mock=mock)

    # routine to pulse clock
    def pulse_clock():
        tcl.set_vio(name='$go_vio', value=0b1)
        sleep(0.1)
        tcl.set_vio(name='$go_vio', value=0b0)
        sleep(0.1)

    # program FPGA
    print('Programming FPGA.')
    tcl.source('program.tcl')

    # reset emulator
    tcl.set_vio(name='$emu_rst', value=0b1)
    sleep(0.1)
    tcl.set_vio(name='$emu_rst', value=0b0)
    sleep(0.1)

    # reset everything else
    tcl.set_vio(name='$go_vio', value=0b0)
    tcl.set_vio(name='$rst_vio', value=0b1)
    tcl.set_vio(name='$v_in_vio', value=float_to_fixed(1.0))

    # pulse the clock
    pulse_clock()
    
    # release from reset
    tcl.set_vio(name='$rst_vio', value=0b0)
    sleep(0.1)
    
    # walk through simulation values
    t_sim = 0.0
    tau = 1.0e-6
    abs_tol = 1e-3
    for _ in range(25):
        # get readings
        tcl.refresh_hw_vio('$vio_0_i')
        v_out_vio = fixed_to_float(int(tcl.get_vio('$v_out_vio')))

        # print readings
        print(f't_sim: {t_sim}, v_out_vio: {v_out_vio}')
    
        # check results
        meas_val = v_out_vio
        expt_val = 1.0 - exp(-t_sim/tau)
        assert (expt_val - abs_tol) <= meas_val <= (expt_val + abs_tol), 'Measured value is out of range.'

        # pulse clock
        pulse_clock()
    
        # update the time variable
        t_sim += 0.1e-6

if __name__ == '__main__':
    test_rc(mock=True)
