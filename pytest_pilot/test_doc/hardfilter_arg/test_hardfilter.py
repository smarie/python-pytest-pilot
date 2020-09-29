from .conftest import flavour


@flavour('yellow')
def test_foo_yellow():
    pass


@flavour('red')
def test_foo_red():
    pass


def test_foo():
    pass
