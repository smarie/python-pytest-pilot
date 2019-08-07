from enum import Enum

import pytest

from pytest_pilot.pytest_compat import itermarkers, apply_mark_to


class NoFlagBehavior(Enum):
    """
    Describes what happens to all tests *marked* with marker <M>
    when users call pytest *without* the commandline filtering flag defined by <M>.
    """
    SkipAllMarked = 0  # marked tests are SKIPPED if the user does not specify a flag.
    RunAllMarked = 1   # marked tests are RUN even if the user does not specify a flag.


class NoMarkBehavior(Enum):
    """
    Describes what happens to tests NOT marked with marker <M>.
    """
    RunOnlyIfNoFlag = 0  # unmarked test are SKIPPED if a filtering flag is received
    AlwaysRun = 1        # unmarked test are RUN even if a filtering flag is received


class EasyMarker(object):
    """
    A helper class to create pytest marks that can automatically be registered with a commandline filtering option.

    """
    __slots__ = 'marker_id', 'full_name', 'noflag_behaviour', 'nomark_behaviour'

    _all_markers = []

    def __init__(self,
                 marker_id,                                     # type: str
                 full_name=None,                                # type: str
                 noflag_behaviour=NoFlagBehavior.RunAllMarked,  # type: NoFlagBehavior
                 nomark_behaviour=NoMarkBehavior.AlwaysRun      # type: NoFlagBehavior
                 ):
        """
        Constructor

        :param marker_id:
        :param full_name:
        :param noflag_behaviour:
        :param nomark_behaviour:
        """
        self.marker_id = marker_id
        self.full_name = full_name if full_name is not None else marker_id
        self.noflag_behaviour = noflag_behaviour
        self.nomark_behaviour = nomark_behaviour

        # register the marker so that we can list them all in `list_all()`
        EasyMarker._all_markers.append(self)

    @property
    def cmdhelp(self):
        return "only run tests matching the %s NAME." % self.full_name

    @property
    def markhelp(self):
        return "mark test to run only on %s with <id>" % self.full_name

    def __str__(self):
        return "Pytest marker '%s' with commandline option '%s' and pytest mark '@pytest.mark.%s(<%s>)'" \
               % (self.full_name, self.cmdoption, self.marker_id, self.marker_id)

    def __repr__(self):
        return str(self)

    @property
    def cmdoption(self):
        return "--%s" % self.marker_id

    def get_mark_decorator(self, mark_value):
        # dynamically create @pytest.mark.<marker_id>(marker_value)
        return getattr(pytest.mark, self.marker_id)(mark_value)

    def apply_mark_to(self, mark_value, on, is_pytest_param):
        mark = self.get_mark_decorator(mark_value)
        return apply_mark_to(mark, on, is_pytest_param=is_pytest_param)

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
        if query is None:
            query = item.config.getoption(self.cmdoption)

        required_marks = self.read_marks(item)

        if query is None:
            if self.noflag_behaviour is NoFlagBehavior.SkipAllMarked:
                # skip all tests that have marks
                if len(required_marks) > 0:
                    pytest.skip("test requires '%s' in %r. Please use the '%s' command flag to activate one of these."
                                % (self.marker_id, required_marks, self.cmdoption))

        else:
            # we run on a specific environment
            if len(required_marks) > 0:
                if query not in required_marks:
                    pytest.skip("This test only runs if '%s' is in %r. Currently it is '%s' (from '%s' command)"
                                % (self.marker_id, required_marks, query, self.cmdoption))
                else:
                    # match: the test is meant to be run on the required environment
                    pass
            else:
                # the test has no constraint
                if self.nomark_behaviour is NoMarkBehavior.RunOnlyIfNoFlag:
                    pytest.skip("This test does not have flag '%s'. Currently it is explicitly used and set to '%s' "
                                "(from '%s' command)" % (self.marker_id, query, self.cmdoption))

    @classmethod
    def list_all(cls):
        return cls._all_markers
