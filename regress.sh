# create virtual environment
$ANASYMOD_PYTHON -m venv venv
source venv/bin/activate

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
echo $$PYTHON_MSDSL

# run tests
pytest --cov-report=xml --cov=anasymod unittests tests -v -r s -s
# for the unittests, the test target can be specified by adding
# --target <target_name> to the pytest call, while the argument
# --classification <classification> can be used to select,
# which set of tests shall be executed (basic, weekend, ...)

# upload coverage information
bash <(curl -s https://codecov.io/bash)
