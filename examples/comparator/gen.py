from msdsl import MixedSignalModel
from anasymod import ExampleControl

def main():
    ctrl = ExampleControl()

    # define ports
    m = MixedSignalModel('comparator', dt=ctrl.dt)
    m.add_analog_input('in_p')
    m.add_analog_input('in_n')
    m.add_digital_output('out', init=0)
    m.add_digital_input('clk')

    # define behavior
    m.immediate_assign('out_async', m.in_p > m.in_n)
    m.next_cycle_assign(m.out, m.out_async, clk=m.clk, rst="1'b0")

    # write model
    ctrl.write_model(m)

if __name__ == '__main__':
    main()
