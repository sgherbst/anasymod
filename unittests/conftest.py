import os
import pytest

def pytest_addoption(parser):
    parser.addoption("--rtenv", action="store", default="nocplusplus",
        help="Select for which Run Time Environment test should be executed.")
    parser.addoption("--classification", action="store", default="basic",
                     help="Select what classification of test should be executed.")
    parser.addoption("--target", action="store", default='sim_icarus',
                     help="Select for which target the test should be executed.")

"""
@pytest.fixture( scope="session")
def setup_environment():
    return "helllo"

def pytest_namespace():
    return {'basic' : pytest.mark.usefixtures("basic")}


@pytest.fixture(scope="session")
def basic():
    print("yippi basic", pytest.config.getoption("--classification"))
    print(TestClassification.basic not in pytest.config.getoption("--classification"))
    basic = pytest.mark.skipif(
        TestClassification.basic not in pytest.config.getoption("--classification"),
        reason="need basic as argumentfor --classification",
    )
    return basic

@pytest.fixture
def weekend():
    print("weekend")
    return pytest.mark.skipif(
        TestClassification.weekend not in pytest.config.getoption("--classification")
    )
"""
