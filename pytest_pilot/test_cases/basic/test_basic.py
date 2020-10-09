import pytest

from .conftest import flavour, envid, silo, hardfilter


@silo
def test_silo(easymarkers):
    assert easymarkers.silo is True
    assert easymarkers.hf is False
    assert easymarkers.envid is None or isinstance(easymarkers.envid, str)
    assert easymarkers.flavour is None or easymarkers.flavour in ("red", "yellow")


@hardfilter
def test_hf(easymarkers):
    assert easymarkers.silo is False
    assert easymarkers.hf is False or easymarkers.hf is True
    assert easymarkers.envid is None or isinstance(easymarkers.envid, str)
    assert easymarkers.flavour is None or easymarkers.flavour in ("red", "yellow")


@flavour('yellow')
@hardfilter
def test_yellow_noenv(easymarkers):
    assert easymarkers.silo is False
    assert easymarkers.flavour is None or easymarkers.flavour == 'yellow'
    assert easymarkers.envid is None or isinstance(easymarkers.envid, str)
    assert easymarkers.hf is False or easymarkers.hf is True


@flavour('yellow')
@envid('env1')
def test_yellow_env1(easymarkers):
    assert easymarkers.silo is False
    assert easymarkers.flavour is None or easymarkers.flavour == 'yellow'
    assert easymarkers.envid == 'env1'
    assert easymarkers.hf is False


@envid('env2')
def test_env2(easymarkers):
    assert easymarkers.silo is False
    assert easymarkers.envid == 'env2'
    assert easymarkers.hf is False
    assert easymarkers.flavour is None or easymarkers.flavour in ("red", "yellow")


@flavour('red')
def test_red_noenv(easymarkers):
    assert easymarkers.silo is False
    assert easymarkers.envid is None or isinstance(easymarkers.envid, str)
    assert easymarkers.flavour is None or easymarkers.flavour == 'red'
    assert easymarkers.hf is False


def test_nomark(easymarkers):
    """ we use this opportunity to test that this raises a value error"""

    assert easymarkers.silo is False
    assert easymarkers.envid is None or isinstance(easymarkers.envid, str)
    assert easymarkers.hf is False
    assert easymarkers.flavour is None or easymarkers.flavour in ("red", "yellow")

    with pytest.raises(ValueError):
        flavour('pink')

