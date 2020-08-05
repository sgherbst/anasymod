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
if [ -z "$ANASYMOD_TARGET" ]; then ANASYMOD_TARGET=sim_icarus; fi

# run tests.  optional arguments:
# --target <target_name> to specify the simulator (sim_icarus, sim_vivado, etc.)
# --classification <classification> to select which tests are run (basic, weekend, etc.)
pytest --cov-report=xml --cov=anasymod --target=$ANASYMOD_TARGET unittests -v -r s -s

# upload coverage information
bash <(curl -s https://codecov.io/bash)
