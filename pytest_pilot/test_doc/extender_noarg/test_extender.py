from .conftest import slow


@slow
def test_bar_slow():
    pass


def test_bar():
    pass
