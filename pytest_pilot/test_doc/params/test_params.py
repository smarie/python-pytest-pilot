from .conftest import slow, envid
import pytest


@pytest.mark.parametrize("b", [
    # pytest.param(-1, marks=pytest.mark.foo),
    pytest.param(0, marks=slow),
    slow.param(0),
    pytest.param(1, marks=envid('h')),
    envid('h').param(1)
    # pytest.mark.bar(1) > does not work with latest pytests
])
def test_bar(b):
    print(b)


@slow
@envid('r')
def test_barabar():
    pass


@slow
class TestFoo:
    def test_a(self):
        pass

    def test_b(self):
        pass


# todo activate when this dependency is added to the tests
# from pytest_cases import parametrize_with_cases
#
# @slow
# def case_a():
#     return 1
#
#
# @envid('r')
# def case_b():
#     return 2
#
#
# @envid('r')
# class CasesA:
#
#     @envid('e')
#     def case_a(self):
#         return 1
#
#     def case_b(self):
#         return 2
#
#
# @parametrize_with_cases("c", cases='.')
# def test_bar2(c):
#     assert c in (1, 2)
