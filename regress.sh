# install various python dependencies
pip install wheel
pip install pytest pytest-cov

# install anasymod
pip install -e .

# specify python location (needed for msdsl)
export PYTHON_MSDSL=`which python`
echo $$PYTHON_MSDSL

# run tests
pytest --cov-report=xml --cov=anasymod tests -v -r s

# upload coverage information
bash <(curl -s https://codecov.io/bash)
