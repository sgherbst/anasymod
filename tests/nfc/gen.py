import os.path

from argparse import ArgumentParser
from math import sqrt

from msdsl.model import MixedSignalModel
from msdsl.verilog import VerilogGenerator
from msdsl.expr import (AnalogSignal, Deriv, DigitalInput, Case, DigitalSignal, DigitalOutput, AnalogArray,
                        DigitalArray, ModelExpr, LessThan, GreaterThan)


from anasymod.util import json2obj
from anasymod.files import get_full_path

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', default='.', type=str)
    args = parser.parse_args()

    # load config options
    config_file_path = os.path.join(os.path.dirname(get_full_path(__file__)), 'config.json')
    cfg = json2obj(open(config_file_path, 'r').read())

    # calculate derived parameters
    m = cfg.coupling*sqrt(cfg.ind_tx*cfg.ind_rx)

    # create the model
    model = MixedSignalModel('nfc', DigitalInput('tx_clk'), DigitalInput('tx_send'), DigitalOutput('tx_recv'),
                             DigitalInput('rx_send'), DigitalOutput('rx_recv'), DigitalOutput('rx_clk'), dt=cfg.dt)

    # implement TX carrier
    model.add_signal(AnalogSignal('v_in', 10))
    model.set_this_cycle(model.v_in, AnalogArray([-cfg.v_carrier, +cfg.v_carrier], model.tx_clk))

    # internal signals
    model.add_signal(AnalogSignal('i_ind_tx', 1.0))
    model.add_signal(AnalogSignal('i_ind_rx', 1.0))
    model.add_signal(AnalogSignal('v_cap_tx', 100))
    model.add_signal(AnalogSignal('v_cap_rx', 100))

    v_ind_rx = AnalogSignal('v_ind_rx')
    v_ind_tx = AnalogSignal('v_ind_tx')

    # determine TX and RX resistances as a function of digital state
    res_tx = Case([cfg.res_tx_comm_0, cfg.res_tx_comm_1], sel_bits=[model.tx_send]) + cfg.res_coil_tx
    cond_load_rx = Case([cfg.cond_rx_comm_0, cfg.cond_rx_comm_1], sel_bits=[model.rx_send])

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
    ],
        internals=[v_ind_rx, v_ind_tx],
        inputs=[model.v_in],
        states=[model.i_ind_tx, model.i_ind_rx, model.v_cap_tx, model.v_cap_rx],
        sel_bits=[model.rx_send, model.tx_send]
    )

    # implement communication
    def add_com(v_com_in_expr: ModelExpr, com_out: DigitalSignal, suffix: str, polarity: str):
        # declare signals
        v_com_in = AnalogSignal(f'v_com_in_{suffix}', range=100)
        v_det = AnalogSignal(f'v_det_{suffix}', range=100)
        v_lpf_fast = AnalogSignal(f'v_lpf_fast_{suffix}', range=100)
        v_lpf_slow = AnalogSignal(f'v_lpf_slow_{suffix}', range=100)
        v_comp = AnalogSignal(f'v_comp_{suffix}', range=100)
        com_gt_det = DigitalSignal(f'com_gt_det_{suffix}')

        # add signals to model
        model.add_signal(v_com_in)
        model.add_signal(v_det)
        model.add_signal(v_lpf_fast)
        model.add_signal(v_lpf_slow)
        model.add_signal(v_comp)
        model.add_signal(com_gt_det)

        # com circuit input
        model.set_this_cycle(v_com_in, v_com_in_expr)

        # detector diode on/off
        model.set_this_cycle(com_gt_det, v_com_in > v_det)

        # comparator input
        model.set_this_cycle(v_comp, v_lpf_fast-v_lpf_slow)

        # com output 1/0
        comp_op = {'+': GreaterThan, '-': LessThan}[polarity]
        model.set_this_cycle(com_out, comp_op(v_comp, 0))

        # detector dynamics
        model.add_eqn_sys([
            Deriv(v_det) == Case([0, 1/cfg.tau_det_fast], [com_gt_det])*(v_com_in-v_det) - v_det/cfg.tau_det_slow,
            Deriv(v_lpf_fast) == (v_det - v_lpf_fast)/cfg.tau_com_fast,
            Deriv(v_lpf_slow) == (v_det - v_lpf_slow)/cfg.tau_com_slow
        ], inputs=[v_com_in], states=[v_det, v_lpf_fast, v_lpf_slow], sel_bits=[com_gt_det])

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
    if args.output is not None:
        filename = os.path.join(get_full_path(args.output), 'nfc.sv')
        print('Model will be written to: ' + filename)
    else:
        filename = None

    # generate the model
    model.compile_model(VerilogGenerator(filename))

if __name__ == '__main__':
    main()