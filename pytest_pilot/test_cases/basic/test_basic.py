from .conftest import flavourmarker, envmarker


@flavourmarker('yellow')
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
    pass
