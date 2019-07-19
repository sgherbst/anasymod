from msdsl import MixedSignalModel, DigitalOutput, DigitalInput
from anasymod import ExampleControl

def main():
    ctrl = ExampleControl()

    # create the model
    model = MixedSignalModel('bitwise', DigitalInput('a'), DigitalInput('b'), DigitalOutput('a_and_b'),
                             DigitalOutput('a_or_b'), DigitalOutput('a_xor_b'), DigitalOutput('a_inv'),
                             DigitalOutput('b_inv'), dt=ctrl.dt)
    model.set_this_cycle(model.a_and_b, model.a & model.b)
    model.set_this_cycle(model.a_or_b, model.a | model.b)
    model.set_this_cycle(model.a_xor_b, model.a ^ model.b)
    model.set_this_cycle(model.a_inv, ~model.a)
    model.set_this_cycle(model.b_inv, ~model.b)

    # write model
    ctrl.write_model(model)

if __name__ == '__main__':
    main()