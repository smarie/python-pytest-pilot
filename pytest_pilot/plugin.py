"""
See https://docs.pytest.org/en/latest/writing_plugins.html
and https://docs.pytest.org/en/latest/_modules/_pytest/hookspec.html
"""
import pytest


# ------------ declare a new hook that users should implement
from pytest_pilot import EasyMarker


def pytest_addhooks(pluginmanager):
    """called at plugin registration time to allow adding new hooks via a call to
    ``pluginmanager.add_hookspecs(module_or_class, prefix)``.


    :param _pytest.config.PytestPluginManager pluginmanager: pytest plugin manager

    .. note::
        This hook is incompatible with ``hookwrapper=True``.
    """
    from pytest_pilot import new_hooks
    # avoid warnings with pytest-2.8
    method = getattr(pluginmanager, "add_hookspecs", None)
    if method is None:
        method = pluginmanager.addhooks
    method(new_hooks)


all_markers = None


# Note: we can not use the pytest_addoption(parser) hook because it is called beforereading the users' conftest.py
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_load_initial_conftests(early_config, parser, args):
    """
    Adds the options corresponding to all declared markers

    :param parser:
    :return:
    """
    # first let the loading happen
    yield

    # then call the extra hook to know what the user wants
    results = early_config.pluginmanager.hook.pytest_pilot_markers()
    nb_plugin_that_answered_with_a_non_none = len(results)

    global all_markers
    assert nb_plugin_that_answered_with_a_non_none < 2, "should not happen since our hook has first_results == True"
    if nb_plugin_that_answered_with_a_non_none == 0:
        # default behaviour: register all markers created by users
        all_markers = EasyMarker.list_all()
    else:
        all_markers = results[0]

    # then add the options accordingly
    for marker in all_markers:
        parser.addoption(marker.cmdoption, action="store", metavar="NAME", help=marker.cmdhelp)


def pytest_configure(config):
    # register our additional markers in the help
    global all_markers
    for marker in all_markers:
        config.addinivalue_line(
            "markers", "%s(id): %s" % (marker.marker_id, marker.markhelp)
        )


def pytest_runtest_setup(item):
    """
    Dynamically skips tests that can not be run on the current environment
    :param item:
    :return:
    """
    global all_markers
    for marker in all_markers:
        marker.skip_if_not_compliant(item)
