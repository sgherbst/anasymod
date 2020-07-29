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
pytest --cov-report=xml --cov=anasymod tests -v -r s -s
# to run tests in unittests directory, a command such as:
# pytest --cov-report=xml --cov=anasymod unittests -v -r s -s -x
# shall be used, note that it is also possible to specify a test target by adding
# the argument --target <target_name> to the pytest call
# the argument --classification <classification> can be used to select,
# which set of tests shall be executed (basic, weekend, ...)

# upload coverage information
bash <(curl -s https://codecov.io/bash)
