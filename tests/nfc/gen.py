import os.path

from argparse import ArgumentParser
from math import sqrt

from msdsl.model import MixedSignalModel
from msdsl.generator.verilog import VerilogGenerator
from msdsl.expr.signals import AnalogSignal, DigitalInput, DigitalSignal, DigitalOutput
from msdsl.eqn.deriv import Deriv
from msdsl.eqn.cases import eqn_case
from msdsl.expr.expr import LessThan, GreaterThan, ModelExpr

from anasymod.util import json2obj
from anasymod.files import get_full_path

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output',type=str)
    parser.add_argument('--dt', type=float)
    args = parser.parse_args()

    # load config options
    config_file_path = os.path.join(os.path.dirname(get_full_path(__file__)), 'config.json')
    cfg = json2obj(open(config_file_path, 'r').read())

    # calculate derived parameters
    m = cfg.coupling*sqrt(cfg.ind_tx*cfg.ind_rx)

    # create the model
    model = MixedSignalModel('nfc', DigitalInput('tx_clk'), DigitalInput('tx_send'), DigitalOutput('tx_recv'),
                             DigitalInput('rx_send'), DigitalOutput('rx_recv'), DigitalOutput('rx_clk'), dt=args.dt)

    # implement TX carrier
    model.bind_name('v_in', cfg.v_carrier*(2*model.tx_clk-1))

    # internal signals
    model.add_analog_state('i_ind_tx', 1.0)
    model.add_analog_state('i_ind_rx', 1.0)
    model.add_analog_state('v_cap_tx', 100)
    model.add_analog_state('v_cap_rx', 100)

    v_ind_rx = AnalogSignal('v_ind_rx')
    v_ind_tx = AnalogSignal('v_ind_tx')

    # determine TX and RX resistances as a function of digital state
    res_tx = eqn_case([cfg.res_tx_comm_0, cfg.res_tx_comm_1], [model.tx_send]) + cfg.res_coil_tx
    cond_load_rx = eqn_case([cfg.cond_rx_comm_0, cfg.cond_rx_comm_1], [model.rx_send])

    # implement coil dynamics
    model.add_eqn_sys([
        # coupled inductor dynamics
        v_ind_tx == cfg.ind_tx * Deriv(model.i_ind_tx) + m * Deriv(model.i_ind_rx),
        v_ind_rx == m * Deriv(model.i_ind_tx) + cfg.ind_rx * Deriv(model.i_ind_rx),
        # capacitor dynamics
        Deriv(model.v_cap_tx) == +model.i_ind_tx/cfg.cap_tx,
        Deriv(model.v_cap_rx) == (-model.i_ind_rx - cond_load_rx*model.v_cap_rx)/cfg.cap_rx,
        # KVL
        model.v_in == res_tx*model.i_ind_tx + v_ind_tx + model.v_cap_tx,
        model.v_cap_rx == cfg.res_coil_rx*model.i_ind_rx + v_ind_rx
    ])

    # implement communication
    def add_com(v_com_in_expr: ModelExpr, com_out: DigitalSignal, suffix: str, polarity: str):
        # declare state variables
        v_det = model.add_analog_state(f'v_det_{suffix}', range_=100)
        v_lpf_fast = model.add_analog_state(f'v_lpf_fast_{suffix}', range_=100)
        v_lpf_slow = model.add_analog_state(f'v_lpf_slow_{suffix}', range_=100)

        # com circuit input
        v_com_in = model.bind_name(f'v_com_in_{suffix}', v_com_in_expr)

        # detector diode on/off
        com_gt_det = model.bind_name(f'com_gt_det_{suffix}', v_com_in > v_det)

        # comparator input
        v_comp = model.bind_name(f'v_comp_{suffix}', v_lpf_fast-v_lpf_slow)

        # com output 1/0
        comp_op = {'+': GreaterThan, '-': LessThan}[polarity]
        model.set_this_cycle(com_out, comp_op(v_comp, 0))

        # detector dynamics
        model.add_eqn_sys([
            Deriv(v_det) == eqn_case([0, 1/cfg.tau_det_fast], [com_gt_det])*(v_com_in-v_det) - v_det/cfg.tau_det_slow,
            Deriv(v_lpf_fast) == (v_det - v_lpf_fast)/cfg.tau_com_fast,
            Deriv(v_lpf_slow) == (v_det - v_lpf_slow)/cfg.tau_com_slow
        ])

    # TX incoming bits
    add_com(model.v_in-model.v_cap_tx, model.tx_recv, suffix='tx', polarity='+')

    # RX incoming bits
    add_com(model.v_cap_rx, model.rx_recv, suffix='rx', polarity='-')

    # RX clock recovery
    model.set_this_cycle(model.rx_clk, model.v_cap_rx > 0)

    # probe signals of interest
    model.add_probe(model.v_in)
    model.add_probe(model.i_ind_tx)
    model.add_probe(model.i_ind_rx)
    model.add_probe(model.v_cap_tx)
    model.add_probe(model.v_cap_rx)
    model.add_probe(model.v_com_in_tx)
    model.add_probe(model.v_com_in_rx)
    model.add_probe(model.v_det_tx)
    model.add_probe(model.v_det_rx)
    model.add_probe(model.v_lpf_fast_tx)
    model.add_probe(model.v_lpf_fast_rx)
    model.add_probe(model.v_lpf_slow_tx)
    model.add_probe(model.v_lpf_slow_rx)
    model.add_probe(model.v_comp_tx)
    model.add_probe(model.v_comp_rx)
    model.add_probe(model.com_gt_det_tx)
    model.add_probe(model.com_gt_det_rx)

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), f'{model.module_name}.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_to_file(VerilogGenerator(), filename)

if __name__ == '__main__':
    main()