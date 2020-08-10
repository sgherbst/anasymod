class RunTimeEnvs:
    """
    Container including enums for supported Run Time Environments.
    """

    nocplusplus = "nocplusplus"
    pmmlegacy = "pmmlegacy"
    stdsc_gcc_32 = "stdsc_gcc_32"
    stdsc_gcc_64 = "stdsc_gcc_64"
    stdsc_vc14_32 = "stdsc_vc14_32"
    stdsc_vc14_64 = "stdsc_vc14_64"

class TestClassification:
    """
    Container including enums for supported Run Time Environments.
    """

    basic = "basic"
    weekend = "weekend"


class Target:
    """
    Container including enums for supported Targets.
    """

    sim_icarus = "sim_icarus"
    sim_vivado = "sim_vivado"
    build_vivado = "build_vivado"
    emulate_vivado = "emulate_vivado"
    sim_xcelium = "sim_xcelium"

