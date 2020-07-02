# create virtual environment
$ANASYMOD_PYTHON -m venv venv
source venv/bin/activate

# upgrade pip
python -m pip install --upgrade pip

# install various python dependencies
pip install wheel
pip install pytest pytest-cov

# install anasymod
pip install -e .

# specify python location (needed for msdsl)
export PYTHON_MSDSL=`which python`
echo $$PYTHON_MSDSL

# run tests
pytest --cov-report=xml --cov=anasymod tests -v -r s -s -x

# upload coverage information
bash <(curl -s https://codecov.io/bash)
