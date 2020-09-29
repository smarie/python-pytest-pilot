# from pytest_pilot import EasyMarker
#
# envid = EasyMarker('envid', mode='silos')
from .conftest import envid


@envid('a')
def test_foo_a():
    pass

@envid('b')
def test_foo_b():
    pass

def test_foo():
    pass
