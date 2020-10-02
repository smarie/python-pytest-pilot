from inspect import isfunction, isclass

import warnings
import pytest

try:  # python 3.5+
    from typing import Set, Any, List, Iterable
except ImportError:
    pass

from _pytest.mark import MarkDecorator
from .pytest_compat import itermarkers, apply_mark_to, PytestUnknownMarkWarning


info_mode = False
debug_mode = False


def set_verbosity_level(pytest_config_verbositylevel):
    global info_mode, debug_mode
    info_mode = pytest_config_verbositylevel >= 3  # -vv
    debug_mode = pytest_config_verbositylevel >= 4  # -vvv


class EasyMarkerDecorator(MarkDecorator):
    """
    A mark decorator that in addition provides a .param(*values) convenience method
    """
    @classmethod
    def create_with_name(cls, name):
        # create a pytest.mark.<name>, and copy its internal mark
        _md = getattr(pytest.mark, name)
        try:
            mark = _md.mark
        except AttributeError:
            # happens in pytest 2, to maybe move in compat in the future
            mark = _md.markname
        return cls(mark)

    def param(self, *values):
        """ Convenience shortcut for `pytest.param(*values, marks=self)` """
        return pytest.param(*values, marks=self)


class EasyMarker(MarkDecorator):
    """
    Creates a pair of marker + commandline option for pytest. Marker instances can be used

     - to decorate test classes or test functions: @marker or @marker(arg) depending whether you set has_arg=False/True
     - in parametrization values with `pytest.param(*<argvalues>, marks=<self>)` or
     `pytest.param(*<argvalues>, marks=<self>(arg))` (for this, we inherit from MarkDecorator and override <self>.mark)

    In addition, `<self>.param(*<argvalues>)` or `<self>(arg).param(*<argvalues>)` is a convenience method provided to
    do the same than `pytest.param(*<argvalues>, marks=<self>)` or `pytest.param(*<argvalues>, marks=<self>(arg))`.
    """
    __slots__ = 'marker_id', 'full_name', \
                'has_arg', 'allowed_values', 'used_values', \
                'cmdoption_short', 'cmdoption_long',  \
                'not_filtering_skips_marked', 'filtering_skips_unmarked', \
                'cmdhelp', 'markhelp'

    _all_markers = []

    def __init__(self,
                 marker_id,             # type: str
                 mode,                  # type: str
                 full_name=None,        # type: str
                 has_arg=True,          # type: bool
                 allowed_values=None,   # type: Iterable[Any]
                 cmdoption_short=None,  # type: str
                 cmdoption_long=None,   # type: str
                 cmdhelp=None,          # type: str
                 markhelp=None,         # type: str
                 ):
        """
        Constructor

        TODO

        :param marker_id: the name of the pytest mark. Applying this marker with `@marker(arg)` will be equivalent to
            applying @pytest.mark.<marker_id>(arg)
        :param mode: a mandatory string indicating the working mode of this mark and the associated filter option. Four
            modes are supported:
             - 'silos': When the option is inactive, only non-marked tests are run. When the option is active, only
               relevant marked tests run. There is no test in common between these "silos"
             - 'extender': When the option is inactive, only non-marked tests are run, this is the "base" set
               of tests. When the option is active, it adds the relevant marked tests to the base set.
             - 'hard_filter': When the option is inactive, all tests run. When the option is active, only the relevant
               marked tests run.
             - 'soft_filter': When the option is inactive, all tests run. When the option is active, all non-marked
               tests continue to run, but among marked tests only the relevant ones run.
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
        :param cmdhelp: the help message displayed when `pytest --help` is called
        :param markhelp: the help message displayed when `pytest --markers` is called
        """

        # mode validation
        if mode == "silos":
            # When the option is inactive, only non-marked tests are run.
            not_filtering_skips_marked = True
            # When the option is active, only relevant marked tests run. There is no test in common between these silos
            filtering_skips_unmarked = True
        elif mode == "extender":
            # When the option is inactive, only non-marked tests are run, this is the "base" set of tests.
            not_filtering_skips_marked = True
            # When the option is active, it adds the relevant marked tests to the base set.
            filtering_skips_unmarked = False
        elif mode == "hard_filter":
            # When the option is inactive, all tests run.
            not_filtering_skips_marked = False
            # When the option is active, only the relevant marked tests run.
            filtering_skips_unmarked = True
        elif mode == "soft_filter":
            # When the option is inactive, all tests run.
            not_filtering_skips_marked = False
            # When the option is active, all non-marked tests continue to run, but among marked tests only
            # the relevant ones run.
            filtering_skips_unmarked = False
            if not has_arg:
                raise ValueError("It does not make sense to set `mode` to `'soft_filter'` when the marker has "
                                 "no arguments.")
        else:
            raise ValueError("Invalid 'mode' %r. Only 'silos', 'extender', 'hard_filter' or 'soft_filter' are "
                             "supported." % mode)

        # identifiers
        if marker_id is None:
            raise ValueError("a non-None `marker_id` is mandatory")
        self.marker_id = marker_id

        # no need to call super constructor, we will never use it directly
        # indeed we override the .mark attribute with a property, see below
        # super(EasyMarker, self).__init__(Mark(marker_id, (), {}))

        self.full_name = full_name if full_name is not None else marker_id  # (default)

        # arguments
        self.has_arg = has_arg
        # note: we do not use a set to store the allowed values because we want to preserve the order
        self.allowed_values = tuple(allowed_values) if allowed_values is not None else None
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

        # help messages
        self.cmdhelp = cmdhelp if cmdhelp is not None else self._get_default_cmdhelp()
        self.markhelp = markhelp if markhelp is not None else self._get_default_markhelp()

        # register the marker so that we can list them all in `list_all()`
        EasyMarker._all_markers.append(self)

        # prepare to collect the list of values actually used
        self.used_values = set()

    @property
    def mark(self):
        # called by pytest when    pytest.param(<argvalue>, marks=<self>)
        if self.has_arg:
            raise ValueError("This marker '%s' has a mandatory argument" % self.marker_id)
        return self.get_mark_decorator().mark

    def param(self, *values):
        """ Convenience shortcut for `pytest.param(*values, marks=self)` """
        return pytest.param(*values, marks=self)

    def __str__(self):
        return "Pytest marker '%s' with CLI option '%s' and decorator '@pytest.mark.%s(<%s>)'" \
               % (self.full_name, self.cmdoption_both, self.marker_id, self.marker_id)

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
            first_part = "only run tests marked as %s (marked with @%s)." % (self.full_name, self.marker_id)

        if self.not_filtering_skips_marked:
            return first_part + " Important: if you call `pytest` without this option, tests marked with @%s will " \
                                "*not* be run." % self.marker_id
        else:
            return first_part + " If you call `pytest` without this option, tests marked with @%s will *all* be run." \
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
            suffix = " <value> should be one of %r." % (self.allowed_values,) if self.allowed_values is not None else ""
            if self.not_filtering_skips_marked:
                return "%s(value): mark test to run *only* when %s (%r option) is set to <value>.%s" \
                       % (self.marker_id, self.cmdoption_both, self.full_name, suffix)
            else:
                return "%s(value): mark test to run *both* when %s (%r option) is set to <value> " \
                       "and if %s is not set.%s" \
                       % (self.marker_id, self.cmdoption_both, self.full_name, self.cmdoption_both, suffix)
        else:
            if self.not_filtering_skips_marked:
                return "%s: mark test to run *only* when %s (%r option) is set." \
                       % (self.marker_id, self.cmdoption_both, self.full_name)
            else:
                return "%s: mark test to run *both* when %s (%r option) is set and when it is not set." \
                       % (self.marker_id, self.cmdoption_both, self.full_name)

    def __call__(self, *args, **kwargs):
        """
        Called when the marker is either called with an argument, or called to decorate a function

        Note: we purposedly override MarkDecorator.__call__ because we do not have to support accumulating arguments:
        either there are arguments or not, but if there are, they are provided only once.

        :param args:
        :param kwargs:
        :return:
        """
        if not self.has_arg:
            # (a) Marker without argument
            if len(args) == 1 and len(kwargs) == 0 and (isfunction(args[0]) or isclass(args[0])):
                # used without parenthesis:   @marker
                return self.get_mark_decorator()(args[0])
            else:
                # used with parenthesis:   @marker()
                assert len(args) == 0 and len(kwargs) == 0, "This marker does not accept any argument. " \
                                                            "Use <self>.param(<value>) if you wish to mark a specific" \
                                                            " @parametrize value"
                # return self to fallback on the no parenthesis mode
                return self
        else:
            # (b) Marker with a mandatory argument: this has to be @marker(arg)
            return self.get_mark_decorator(*args)

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
                if self.allowed_values is not None:
                    if mark_value[0] not in self.allowed_values:
                        raise ValueError("%r is not allowed for marker %r. Allowed values are %r"
                                         % (mark_value[0], self.marker_id, self.allowed_values))

        # create it
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=PytestUnknownMarkWarning)
            return EasyMarkerDecorator.create_with_name(self.marker_id)(*mark_value)

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
        Helper function to retrieve all values marked if this marker accepts arguments

        :param item:
        :return:
        """
        # todo read item.callspec.params ?
        return [mark.args[0] if self.has_arg else True for mark in itermarkers(item, name=self.marker_id)]

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
            # usage in pytest
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
        no_query = query is None if self.has_arg else query is False

        if no_query:
            # /1/ we run without CLI option filter
            if self.not_filtering_skips_marked:
                # (a) skip all tests that have marks
                if len(required_marks) > 0:
                    if self.has_arg:
                        if len(required_marks) == 1:
                            pytest.skip("This test requires %r=%r. Run `pytest %s=%s` to activate it."
                                        % (self.marker_id, required_marks[0], self.cmdoption_long, required_marks[0]))
                        else:
                            pytest.skip("This test requires %r in %r. Run `pytest %s=<arg>` to activate it."
                                        % (self.marker_id, required_marks, self.cmdoption_long))
                    else:
                        pytest.skip("This test requires %r. Run `pytest %s` to activate it."
                                    % (self.marker_id, self.cmdoption_long))
                else:
                    if info_mode:
                        print("%s item has no marks and option '%s' was not used, item can run"
                              % (logprefix, self.cmdoption_long))
            else:
                # (b) keep all tests
                if info_mode:
                    print("%s option '%s' was not used, all items can run" % (logprefix, self.cmdoption_long))

        else:
            # /2/ we run with a CLI option filter, for example `pytest --envid=a` or `pytest --blue`.
            if len(required_marks) > 0:
                # -- current test has at least 1 mark of this type: if the mark has an arg, check that it matches query.
                # NOTE: ONE MATCH IS ENOUGH to avoid being skipped ! (this is an OR, not an AND)
                if self.has_arg and query not in required_marks:
                    if len(required_marks) == 1:
                        pytest.skip("This test requires %r=%r. Currently `%s=%s` so it is skipped."
                                    % (self.marker_id, required_marks[0], self.cmdoption_long, query))
                    else:
                        pytest.skip("This test requires %r in %r. Currently `%s=%s` so it is skipped."
                                    % (self.marker_id, required_marks[0], self.cmdoption_long, query))
                else:
                    # match: the test has the right mark
                    if info_mode:
                        print("%s item marks %r matches query filter '%s', it can run"
                              % (logprefix, required_marks, query))
            else:
                # -- the test does not have this mark.
                if self.filtering_skips_unmarked:
                    # (a) skip all tests that have no marks
                    if self.has_arg:
                        pytest.skip("This test does not have mark '%s', and pytest was run with `%s=%s` so it is "
                                    "skipped." % (self.marker_id, self.cmdoption_long, query))
                    else:
                        pytest.skip("This test does not have mark '%s', and pytest was run with `%s` so it is "
                                    "skipped." % (self.marker_id, self.cmdoption_long))
                else:
                    # (b) keep all tests that have no marks
                    if info_mode:
                        print("%s item has no marks, it can run" % (logprefix, ))

    @classmethod
    def list_all(cls):
        # type: (...) -> List[EasyMarker]
        return cls._all_markers
