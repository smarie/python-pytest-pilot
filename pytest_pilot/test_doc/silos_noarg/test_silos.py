# from pytest_pilot import EasyMarker
#
# envid = EasyMarker('envid', mode='silos')
from .conftest import envid


@envid
def test_foo_a():
    pass


def test_foo():
    pass


@envid.agnostic
def test_bar():
    pass
