from msdsl import MixedSignalModel, RangeOf, AnalogSignal, sum_op, Deriv
from anasymod import ExampleControl

def main(cap=1e-12, res=600, n_array=47):
    ctrl = ExampleControl()

    # define ports
    m = MixedSignalModel('current_switch_array', dt=ctrl.dt)
    m.add_digital_input('ctrl', n_array)
    m.add_analog_input('v_in')
    m.add_analog_output('v_out', init=0) # can change initial value if desired

    # find number of zeros
    m.immediate_assign('n_on', n_array - sum_op([m.ctrl[k] for k in range(m.ctrl.width)]))

    # compute the unit current
    m.immediate_assign('i_unit', (m.v_in - m.v_out)/res)

    # compute the array current
    m.immediate_assign('i_array', m.n_on * m.i_unit)

    # define the voltage update on the cap
    m.next_cycle_assign(m.v_out, m.v_out + m.i_array / (n_array * cap) * ctrl.dt)

    # write model
    ctrl.write_model(m)

if __name__ == '__main__':
    main()
