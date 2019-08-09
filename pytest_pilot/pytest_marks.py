from enum import Enum

import pytest

try:  # python 3.5+
    from typing import Set, Any, List, Iterable
except ImportError:
    pass


from pytest_pilot.pytest_compat import itermarkers, apply_mark_to


info_mode = False
debug_mode = False


def set_verbosity_level(pytest_config_verbositylevel):
    global info_mode, debug_mode
    info_mode = pytest_config_verbositylevel >= 3  # -vv
    debug_mode = pytest_config_verbositylevel >= 4  # -vvv


class EasyMarker(object):
    """
    A helper class to create pytest marks.
    TODO
     that can automatically be registered with a commandline filtering option.
    """
    __slots__ = 'marker_id', 'full_name', \
                'has_arg', 'allowed_values', 'used_values', \
                'cmdoption_short', 'cmdoption_long',  \
                'not_filtering_skips_marked', 'filtering_skips_unmarked', \
                'cmdhelp', 'markhelp'

    _all_markers = []

    def __init__(self,
                 marker_id,                         # type: str
                 full_name=None,                    # type: str
                 has_arg=True,                      # type: bool
                 allowed_values=None,               # type: Iterable[Any]
                 cmdoption_short=None,              # type: str
                 cmdoption_long=None,               # type: str
                 not_filtering_skips_marked=False,  # type: bool
                 filtering_skips_unmarked=False,    # type: bool
                 cmdhelp=None,                      # type: str
                 markhelp=None                      # type: str
                 ):
        """
        Constructor

        TODO

        :param marker_id: the name of the pytest mark. Applying this marker with `@marker(arg)` will be equivalent to
            applying @pytest.mark.<marker_id>(arg)
        :param full_name: the full name of the marker, to be used in help texts. If `None` (default), it defaults to
            `marker_id`.
        :param has_arg: if this is `True` (default), the marker has a single argument and the filtering commandline
            option accepts an argument too. For example a `colormarker` with id `color` will accept an argument
            describing which color: `@colormarker('yellow')`. If this is `False`, the marker has no argument and the
            filtering commandline option is a flag with no arguments too. For example a `smokemarker` with id `smoke`:
            `@smokemarker`.
        :param allowed_values: a predefined set of values that can be used for this marker. Applying the mark with another
            value as argument will result in a `ValueError`being raised. `None` (default) will allow users to apply
            this mark with any value. Note that this can only be set if `has_arg`is `True`
        :param cmdoption_short: the id to use for the "short" command option (for example providing `'E'` or `'-E'`
            will result in  the option `'-E'`). `None` (default) will *not* create a "short" command option, to avoid
            name collisions.
        :param cmdoption_long: the id to use for the "long" command option (for example providing `'env'` or `'--env'`
            will result in the option `'--env'`). `None` (default) will use `marker_id` for the long command option.
        :param not_filtering_skips_marked: if this is `False` (default), a tests *marked* with this marker *will* run
            when the user calls pytest *without* the associated commandline filtering option. If it is `True` it will be
            skipped. In other words if this is `True`, marked tests can only run when the option is explicitly used.
        :param filtering_skips_unmarked: if this is `False` (default), a test *not marked* with this marker *will* run
            when the user calls pytest *with* the associated commandline filtering option. If this is `True` it will be
            skipped. In other words if this is `True`, unmarked tests can only run when the option is *not* used.
        :param cmdhelp: the help message displayed when `pytest --help` is called
        :param markhelp: the help message displayed when `pytest --markers` is called
        """
        # identifiers
        if marker_id is None:
            raise ValueError("a non-None `marker_id` is mandatory")
        self.marker_id = marker_id

        self.full_name = full_name if full_name is not None else marker_id  # (default)

        # arguments
        self.has_arg = has_arg
        self.allowed_values = set(allowed_values) if allowed_values is not None else None
        if not self.has_arg and self.allowed_values is not None:
            raise ValueError("`allowed_values` should not be provided if `has_arg` is `False`, as the marker does not "
                             "accept any arguments")

        # cmdoption short
        if cmdoption_short is not None:
            if cmdoption_short.startswith('--'):
                raise ValueError("Short command option should only have a single leading dash `-` symbol or zero, not "
                                 "two. Found %s" % cmdoption_short)
            else:
                cmdoption_short = "-%s" % cmdoption_short.strip('-')
        self.cmdoption_short = cmdoption_short

        # cmdoption long
        if cmdoption_long is None:
            cmdoption_long = self.marker_id

        if cmdoption_long.startswith('-') and cmdoption_long[1] != '-':
            raise ValueError("Long command option should have two leading dash `-` symbols or zero, not one. "
                             "Found %s" % cmdoption_long)
        else:
            self.cmdoption_long = "--%s" % cmdoption_long.strip('-')

        # query filters
        self.not_filtering_skips_marked = not_filtering_skips_marked
        self.filtering_skips_unmarked = filtering_skips_unmarked
        if self.filtering_skips_unmarked and self.not_filtering_skips_marked and not self.has_arg:
            raise ValueError("It does not make sense to set both `filtering_skips_unmarked` and "
                             "`not_filtering_skips_marked` to `True` when the marker has no arguments.")

        # help messages
        self.cmdhelp = cmdhelp if cmdhelp is not None else self._get_default_cmdhelp()
        self.markhelp = markhelp if markhelp is not None else self._get_default_markhelp()

        # register the marker so that we can list them all in `list_all()`
        EasyMarker._all_markers.append(self)

        # prepare to collect the list of values actually used
        self.used_values = set()

    def __str__(self):
        return "Pytest marker '%s' with commandline option '%s' and pytest mark '@pytest.mark.%s(<%s>)'" \
               % (self.full_name, self.cmdoption_long, self.marker_id, self.marker_id)

    def __repr__(self):
        return str(self)

    def _get_default_cmdhelp(self):
        if self.has_arg:
            if self.filtering_skips_unmarked:
                first_part = "only run tests marked as requiring %s NAME (marked with @%s(NAME))." \
                             % (self.full_name, self.marker_id)
            else:
                first_part = "run tests marked as requiring %s NAME (marked with @%s(NAME)), as well as tests not " \
                             "marked with @%s." % (self.full_name, self.marker_id, self.marker_id)
        else:
            return "only run tests marked as %s (marked with @%s)." % (self.full_name, self.marker_id)

        if self.not_filtering_skips_marked:
            return first_part + " Important: if you call `pytest` without this option, tests marked with @%s will " \
                                "*not* be run." % self.marker_id
        else:
            return first_part + " If you call `pytest` without this option, tests marked with @%s will *all* be run" \
                                "" % self.marker_id

    @property
    def cmdoption_both(self):
        if self.cmdoption_short:
            if self.cmdoption_long:
                return "%s/%s" % (self.cmdoption_short, self.cmdoption_long)
            else:
                return "%s" % self.cmdoption_short
        else:
            return "%s" % self.cmdoption_long

    def _get_default_markhelp(self):
        if self.has_arg:
            if self.not_filtering_skips_marked:
                suffix = "."
            else:
                suffix = ", or if the option is not used at all."

            return "%s(value): mark test to run only when command option %s is used to set %s to <value>%s" \
                   % (self.marker_id, self.full_name, self.cmdoption_both, suffix)

        else:
            if self.not_filtering_skips_marked:
                word = "only"
            else:
                word = "even"

            return "%s: mark test to run %s when command option %s is used." \
                   % (self.marker_id, word, self.cmdoption_both)

    def __call__(self, *args, **kwargs):
        """
        Called when the marker is either called with an argument, or called to decorate a function

        TODO should we inherit from MarkDecorator to automatically benefit from this?

        :param args:
        :param kwargs:
        :return:
        """
        return self.get_mark_decorator(*args, **kwargs)

    def get_mark_decorator(self, *mark_value):
        """
        dynamically create @pytest.mark.<marker_id>(mark_value)
        and remembers the set of all used values

        :param mark_value:
        :return:
        """
        nbargs = len(mark_value)
        if not self.has_arg:
            # we expect no args
            if nbargs > 0:
                raise ValueError("This marker '%s' accepts no arguments" % self.marker_id)
        else:
            # we expect a single arg
            if nbargs == 0:
                raise ValueError("This marker '%s' has a mandatory argument" % self.marker_id)
            elif nbargs > 1:
                raise ValueError("This marker '%s' has a single mandatory argument, received %s: %s"
                                 % (self.marker_id, nbargs, mark_value))
            else:
                # single value:
                # TODO self.used_values.add(mark_value[0]) but sometimes it received a MarkDecorator
                pass

        # create it
        return getattr(pytest.mark, self.marker_id)(*mark_value)

    def apply_to_param_value(self, param_value, *args):
        """
        Helper function to apply a mark to a parameter

        :param param_value:
        :param args: the mark argument or nothing if the mark is a flag
        :return:
        """
        mark = self.get_mark_decorator(*args)
        return apply_mark_to(mark, param_value, is_pytest_param=True)

    def read_marks(self, item):
        """
        Helper function to retrieve all required environments

        :param item:
        :return:
        """
        return [mark.args[0] for mark in itermarkers(item, name=self.marker_id)]

    def skip_if_not_compliant(self, item, query=None):
        """
        Utility function to mark the pytest item as skipped if its markers make it not compliant with the currently
        selected env.

        :param item:
        :param query: if None, the current options from item.config is used
        :return:
        """
        logprefix = "[pytest-pilot] %s [marker %s] " % (item, self.marker_id)

        if debug_mode:
            print('%s checking if item should be skipped according to options' % logprefix)

        if query is None:
            try:
                query = item.config.getoption(self.cmdoption_long[2:])
                if debug_mode:
                    print("%s filtering query option '%s' is currently '%s'" % (logprefix, self.cmdoption_long, query))
            except ValueError:
                # ValueError: no option named 'a' can happen sometimes/ in some versions
                pass
            except AttributeError:
                # AttributeError: 'Namespace' object has no attribute 'a' can happen sometimes/ in some versions
                pass

        required_marks = self.read_marks(item)

        if query is None:
            # -- we run without filter
            if self.not_filtering_skips_marked:
                # skip all tests that have marks
                if len(required_marks) > 0:
                    pytest.skip("test requires '%s' in %r. Please use the '%s' command option to activate one of these."
                                % (self.marker_id, required_marks, self.cmdoption_long))
                else:
                    if info_mode:
                        print("%s item has no marks and option '%s' was not used, item can run"
                              % (logprefix, self.cmdoption_long))
            else:
                if info_mode:
                    print("%s option '%s' was not used, all items can run" % (logprefix, self.cmdoption_long))

        else:
            # -- we run with a filter
            if len(required_marks) > 0:
                # -- the test has marks: apply the filter
                if query not in required_marks:
                    pytest.skip("This test is marked to only runs if '%s' is in %r. Currently it is set to '%s' (from "
                                "the '%s' command option)" % (self.marker_id, required_marks, query,
                                                              self.cmdoption_long))
                else:
                    # match: the test is meant to be run on the required environment
                    if info_mode:
                        print("%s item marks %r contain query filter '%s', it can run"
                              % (logprefix, required_marks, query))
            else:
                # -- the test has no marks
                if self.filtering_skips_unmarked:
                    # skip all tests that have no marks
                    pytest.skip("This test does not have marker '%s'. Currently it is explicitly required with value"
                                " '%s' (from the '%s' command option)" % (self.marker_id, query, self.cmdoption_long))
                else:
                    if info_mode:
                        print("%s item has no marks, it can run" % (logprefix, ))

    @classmethod
    def list_all(cls):
        # type: (...) -> List[EasyMarker]
        return cls._all_markers
