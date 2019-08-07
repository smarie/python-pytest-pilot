# from pluggy import HookimplMarker, HookspecMarker
#
# # the symbol that can be used on users' hooks:
# # @pytest-pilot.hookimpl
# pytest_pilot_hookimpl = HookimplMarker("pytest-pilot")
#
# pytest_pilot_hookspec = HookspecMarker("pytest-pilot")


# @pytest_pilot_hookspec(firstresult=True)
def pytest_pilot_markers():
    """pytest-pilot hook to declare which markers should be active. If not provided, all markers will be exposed. To
    explicitly state that no markers should be exposed, return an empty tuple ()."""
