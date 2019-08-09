pytest_plugins = ["pytester"]


def pytest_configure(config):
    # MANDATORY ; configure  pytester to run pytest in subprocesses and not in the same process, otherwise strange
    # things happen: the conftest.py files from the test runs interact with the meta runs !
    config.option.runpytest = 'subprocess'
    assert config.getvalue("runpytest") == 'subprocess'
