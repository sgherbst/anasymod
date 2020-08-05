# upgrade pip
python -m pip install --upgrade pip

# install various python dependencies
# using a version of pytest more recent than 5 won't work because it is not compatible
# with the pytest.config global used in unittest/basic_sim/test_basic_sim.py
pip install wheel
pip install "pytest<5" pytest-cov

# install anasymod
pip install -e .

# specify python location (needed for msdsl)
export PYTHON_MSDSL=`which python`
echo $PYTHON_MSDSL

# use a default target if not specified
if [[ -z "$ANASYMOD_TARGET" ]]; then
    ANASYMOD_TARGET=sim_icarus
fi

# run simulation-based tests.  optional arguments:
# --target <target_name> to specify the simulator (sim_icarus, sim_vivado, etc.)
# --classification <classification> to select which tests are run (basic, weekend, etc.)
pytest --cov-report=xml -v -r s -s \
    --cov=anasymod --target=$ANASYMOD_TARGET unittests

# if we're on the FPGA server, then run some tests on the FPGA board
# note that --cov-append is used so that we added to the previously
# collected coverage data
if [[ -n "${FPGA_SERVER}" ]]; then
    pytest --cov-report=xml --cov-append -v -r s -s \
        --cov=anasymod --target=emulate_vivado \
        unittests/basic_sim/test_basic_sim.py::TestBasicSIM.test_firmware \
        unittests/basic_sim/test_basic_sim.py::TestBasicSIM.test_rc
fi

# upload coverage information
bash <(curl -s https://codecov.io/bash)
