"""
See https://docs.pytest.org/en/latest/writing_plugins.html
and https://docs.pytest.org/en/latest/_modules/_pytest/hookspec.html
"""
import pytest


# ------------ declare a new hook that users should implement
from pytest_pilot import EasyMarker
from pytest_pilot.pytest_marks import set_verbosity_level


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


# Note: we can not use the pytest_addoption(parser) hook because it is called before reading the users' conftest.py
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

    # existing options
    existing_opts = vars(early_config.option)

    # then add the options accordingly
    for marker in all_markers:
        # For long names (and sometimes short ones too?) the conflict
        # does not raise an error in pytest when adding the option, therefore
        # we try to provide some early detection here.
        short_exists = marker.cmdoption_short.strip('-') in existing_opts if marker.cmdoption_short is not None else False
        long_exists = marker.cmdoption_long.strip('-') in existing_opts
        if short_exists or long_exists:
            conflicting = []
            if short_exists:
                conflicting.append(marker.cmdoption_short)
            if long_exists:
                conflicting.append(marker.cmdoption_long)
            raise ValueError("Error registering <%s>: a command with this long or short name already exists."
                             " Conflicting name(s): %s" % (marker, conflicting))

        # No long name conflict. add option and catch short name conflicts
        names = []
        if marker.cmdoption_short is not None:
            names.append(marker.cmdoption_short)
        if marker.cmdoption_long is not None:
            names.append(marker.cmdoption_long)
        try:
            if marker.has_arg:
                parser.addoption(*names, action="store", metavar="NAME", help=marker.cmdhelp)
            else:
                parser.addoption(*names, action="store_true", help=marker.cmdhelp)
        except Exception as e:
            raise ValueError("Error registering <%s>: a command with this long or short name already exists. "
                             "Caught: %r" % (marker, e))


def pytest_configure(config):
    # register our additional markers in the help
    global all_markers
    for marker in all_markers:
        config.addinivalue_line("markers", marker.markhelp)

    # detect if we are in verbose mode
    verbositylevel = config.getoption('verbose')
    set_verbosity_level(verbositylevel)


# def pytest_collection_modifyitems(items, config):
#     # todo new option for markers to decide between skipping and deselecting ?
#     see https://github.com/smarie/python-pytest-pilot/issues/14
#     deselect_by_mark(items, config)


def pytest_runtest_setup(item):
    """
    Dynamically skips tests that can not be run on the current environment
    :param item:
    :return:
    """
    global all_markers
    for marker in all_markers:
        marker.skip_if_not_compliant(item)
