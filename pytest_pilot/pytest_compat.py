"""
A module to manage compatibility with older pytest versions
"""
import pytest

try:
    _ = pytest.param
    from pytest import param as pytest_param
    support_multi_marks = True

except AttributeError:
    # if not this is how it was done
    # see e.g. https://docs.pytest.org/en/2.9.2/skipping.html?highlight=mark%20parameter#skip-xfail-with-parametrize
    def pytest_param(c, marks):
        if len(marks) > 1:
            # raise ValueError("Multiple marks on parameters not supported for old versions of pytest")
            res = c
            for m in marks:
                res = pytest_param(res, (m, ))
            return res
        else:
            paramvalue = marks[0](c)

            # from https://www.reddit.com/r/learnpython/comments/6rmaxp/overriding_repr_on_an_instance/

            class MyMarkDecorator(paramvalue.__class__):
                def __init__(self, old_thing):
                    self.__dict__ = old_thing.__dict__

                def __str__(self):
                    return str(c)

            paramvalue2 = MyMarkDecorator(paramvalue)
            return paramvalue2

    support_multi_marks = False


def apply_mark_to(marker, on, is_pytest_param=True):
    """
    A custom marker to define the required environment id
    See http://doc.pytest.org/en/latest/example/markers.html

    :param marker: a  pytest.mark.xxx(xxx) mark
    :param on: the target object to mark: typically a test function, a fixture or a parameter value
    :param is_param: True if the value is a parameter value, False if it is a fixture or function
    :return:
    """
    if not is_pytest_param:
        return marker(on)
    else:
        try:
            # recent pytest version : ParameterSet
            existing_values = on.values
            existing_marks = on.marks

            kwargs = dict()
            try:
                existing_id = on.id
                if existing_id is not None:
                    kwargs['id'] = existing_id
            except AttributeError:
                pass

            return pytest_param(*existing_values, marks=existing_marks + (marker, ), **kwargs)

        except AttributeError:
            # older pytest version (pytest 2)
            try:
                markname = on.markname
                # actually with this pytest version we can just pile calls, it works the same :)
                return pytest_param(on, marks=(marker,))
            except AttributeError:
                # probably no mark
                return pytest_param(on, marks=(marker,))


def itermarkers(item, name):
    try:
        # newer pytest: markers with the same name can coexist
        return item.iter_markers(name=name)
    except AttributeError:
        # older pytest: only one mark with the same name can exist
        marker = item.get_marker(name)
        if marker is None:
            return ()
        else:
            return marker,


try:
    from _pytest.warning_types import PytestUnknownMarkWarning
except ImportError:
    PytestUnknownMarkWarning = UserWarning
