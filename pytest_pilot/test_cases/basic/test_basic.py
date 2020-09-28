import pytest

from .conftest import flavourmarker, envmarker, silomarker, hardfilter


@silomarker
def test_silo():
    pass


@hardfilter
def test_hf():
    pass


@flavourmarker('yellow')
@hardfilter
def test_yellow_noenv():
    pass


@flavourmarker('yellow')
@envmarker('env1')
def test_yellow_env1():
    pass


@envmarker('env2')
def test_env2():
    pass


@flavourmarker('red')
def test_red_noenv():
    pass


def test_nomark():
    """ we use this opportunity to test that this raises a value error"""
    with pytest.raises(ValueError):
        flavourmarker('pink')

