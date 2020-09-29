from .conftest import slow, envid
import pytest


@pytest.mark.parametrize("a", [0, pytest.param(False, marks=pytest.param.envid), slow()(True), 1])
def test_foo(a):
    pass
