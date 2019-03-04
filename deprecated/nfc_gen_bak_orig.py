import os.path

from argparse import ArgumentParser
from math import sqrt

from msdsl.model import MixedSignalModel
from msdsl.verilog import VerilogGenerator
from msdsl.expr import (AnalogSignal, Deriv, DigitalInput, Case, DigitalSignal, DigitalOutput, AnalogArray, DigitalArray)


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

    # implement main dynamics
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

    # implement peak detectors
    def add_com(v_com: AnalogSignal, v_det: AnalogSignal, v_hpf: AnalogSignal, com_gt_det: DigitalSignal, com_out: DigitalSignal):
        model.set_this_cycle(com_gt_det, v_com > v_det)
        model.add_eqn_sys([
            Deriv(v_det) == Case([0, 1/cfg.tau_det_fast], [com_gt_det])*(v_com-v_det) - v_det/cfg.tau_det_slow
        ], inputs=[v_com], states=[v_det], sel_bits=[com_gt_det])
        model.set_tf(v_hpf, v_det, ((cfg.tau_com_hpf, 0), (cfg.tau_com_hpf*cfg.tau_com_lpf, (cfg.tau_com_hpf+cfg.tau_com_lpf), 1)))
        model.set_this_cycle(com_out, v_hpf > 0)

    # TX recv communication
    model.add_signal(AnalogSignal('v_com_tx', 100))
    model.set_this_cycle(model.v_com_tx, model.v_in - model.v_cap_tx)
    model.add_signal(AnalogSignal('v_det_tx', 100))
    model.add_signal(AnalogSignal('v_hpf_tx', 100))
    model.add_signal(DigitalSignal('com_gt_det_tx'))
    add_com(model.v_com_tx, model.v_det_tx, model.v_hpf_tx, model.com_gt_det_tx, model.tx_recv)

    # RX recv communication
    model.add_signal(AnalogSignal('v_det_rx', 100))
    model.add_signal(AnalogSignal('v_hpf_rx', 100))
    model.add_signal(DigitalSignal('com_gt_det_rx'))
    model.add_signal(DigitalSignal('rx_recv_n'))
    add_com(model.v_cap_rx, model.v_det_rx, model.v_hpf_rx, model.com_gt_det_rx, model.rx_recv_n)

    # invert the RX recv signal
    # TODO: add digital operations to MSDSL expr library
    model.set_this_cycle(model.rx_recv, DigitalArray([1, 0], model.rx_recv_n))

    # RX clock recovery
    model.set_this_cycle(model.rx_clk, model.v_cap_rx > 0)

    # probe signals of interest
    model.add_probe(model.v_in)
    model.add_probe(model.i_ind_tx)
    model.add_probe(model.i_ind_rx)
    model.add_probe(model.v_cap_tx)
    model.add_probe(model.v_cap_rx)
    model.add_probe(model.v_det_tx)
    model.add_probe(model.v_det_rx)
    model.add_probe(model.v_hpf_tx)
    model.add_probe(model.v_hpf_rx)
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