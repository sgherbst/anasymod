from msdsl import MixedSignalModel, RangeOf, AnalogSignal
from anasymod import ExampleControl

def main(cap=1e-12, res=600):
    ctrl = ExampleControl()

    # define ports
    m = MixedSignalModel('current_switch', dt=ctrl.dt)
    m.add_digital_input('ctrl')
    m.add_analog_input('v_in')
    m.add_analog_output('v_out')

    # define the circuit
    c = m.make_circuit()
    gnd = c.make_ground()

    c.switch('net_v_in', 'net_v_out', m.ctrl, r_on=res, r_off=10e3*res)
    c.capacitor('net_v_out', gnd, cap, voltage_range=RangeOf(m.v_out))
    c.voltage('net_v_in', gnd, m.v_in)

    c.add_eqns(
        m.v_out == AnalogSignal('net_v_out')
    )

    # write model
    ctrl.write_model(m)

if __name__ == '__main__':
    main()
