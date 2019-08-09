# pytest-pilot

*Slice in your test base thanks to powerful markers*

[![Python versions](https://img.shields.io/pypi/pyversions/pytest-pilot.svg)](https://pypi.python.org/pypi/pytest-pilot/) [![Build Status](https://travis-ci.org/smarie/python-pytest-pilot.svg?branch=master)](https://travis-ci.org/smarie/python-pytest-pilot) [![Tests Status](https://smarie.github.io/python-pytest-pilot/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-pytest-pilot/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-pytest-pilot/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-pytest-pilot)

[![Documentation](https://img.shields.io/badge/doc-latest-blue.svg)](https://smarie.github.io/python-pytest-pilot/) [![PyPI](https://img.shields.io/pypi/v/pytest-pilot.svg)](https://pypi.python.org/pypi/pytest-pilot/) [![Downloads](https://pepy.tech/badge/pytest-pilot)](https://pepy.tech/project/pytest-pilot) [![Downloads per week](https://pepy.tech/badge/pytest-pilot/week)](https://pepy.tech/project/pytest-pilot) [![GitHub stars](https://img.shields.io/github/stars/smarie/python-pytest-pilot.svg)](https://github.com/smarie/python-pytest-pilot/stargazers)

In `pytest` we can create custom markers and filter tests according to them using the `-m` flag, as explained [here](https://docs.pytest.org/en/latest/example/markers.html). However 

 - by default it only supports one kind of marker query behaviour: a test with a mark <M> will run *even* if you do not use the `-m <M>` flag. If you wish to implement something more complex, you have to add code in your `contest.py` as explained [here](http://doc.pytest.org/en/latest/example/markers.html#marking-platform-specific-tests-with-pytest) 
 
 - It is also not easy to understand what happens when a marker has a parameter (an argument) and how to filter according to this. It seems from [the examples in the doc](http://doc.pytest.org/en/latest/example/markers.html#custom-marker-and-command-line-option-to-control-test-runs) that the only way to handle these is again to add code in your `contest.py`
 
 - In other words, it is not easy to expose a "functional" view to the user, even if all core mechanisms are perfectly working.

`pytest-pilot` proposes **a high-level API to create and register pytest markers so that they are easy to understand and use**. To do this it does not use fancy mechanisms: it simply automates most the patterns demonstrated in the `pytest` documentation. 
 

## Installing

```bash
> pip install pytest-pilot
```

## Usage 

### Basic

The easiest way to define a marker is to create an instance of `EasyMarker`, anywhere in your code (in test files, in `contest.py` files, or even in other python files). 

For example let's create two markers: 

 - one `envid` marker defining the python environment on which we run. Tests that have this marker should run **only** if `pytest` is called with a `--envid` flag indicating that the environment is active.
 
 - one `flavour` marker representing an optional filter. Tests that have this marker should run either if `pytest` is called with the correct `--flavour`, or if the `--flavour` flag is not set


```python
from pytest_pilot import EasyMarker

flavourmarker = EasyMarker(marker_id='flavour', 
                           allowed_values=('red', 'yellow'))

envmarker = EasyMarker('envid', 
                       full_name='environment', 
                       not_filtering_skips_marked=True)
```

We can now define a few tests in a test file:

```python
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
```

And we can see that the filtering works as expected:

 - with no options, the tests marked as requiring an environment are correctly skipped:

```bash
>>> pytest
============================= test session starts =============================
(...)
collected 5 items                                                              
test_basic.py::test_yellow_noenv PASSED                            [ 20%]
test_basic.py::test_yellow_env1 SKIPPED                            [ 40%]
test_basic.py::test_env2 SKIPPED                                   [ 60%]
test_basic.py::test_red_noenv PASSED                               [ 80%]
test_basic.py::test_nomark PASSED                                  [100%]
===================== 3 passed, 2 skipped in 0.09 seconds =====================
```

 - with an `--envid` option we can add one of them, the non marked tests still being able to run:

```bash
>>> pytest --envid env1
============================= test session starts =============================
(...)
collected 5 items                                                              
test_basic.py::test_yellow_noenv PASSED                                  [ 20%]
test_basic.py::test_yellow_env1 PASSED                                   [ 40%]
test_basic.py::test_env2 SKIPPED                                         [ 60%]
test_basic.py::test_red_noenv PASSED                                     [ 80%]
test_basic.py::test_nomark PASSED                                        [100%]
===================== 4 passed, 1 skipped in 0.08 seconds =====================
```

 - we can use both options together and get expected results:

```bash
>>> pytest --envid env2 --flavour red
============================= test session starts =============================
(...)
collected 5 items                                                              
test_basic.py::test_yellow_noenv SKIPPED                                 [ 20%]
test_basic.py::test_yellow_env1 SKIPPED                                  [ 40%]
test_basic.py::test_env2 PASSED                                          [ 60%]
test_basic.py::test_red_noenv PASSED                                     [ 80%]
test_basic.py::test_nomark PASSED                                        [100%]
===================== 3 passed, 2 skipped in 0.07 seconds =====================
```

### Verbosity levels

You can use the verbose pytest flags to get a little more explanation about why tests are skipped or run:

```bash
>>> pytest -vv --envid env2
(verbose explanations)
>>> pytest -vvv --envid env2
(even more verbose explanations)
```

### Help

Help on command options is automatically added to the `pytest --help` output:

```bash
>>> pytest --help

(...)

custom options:
  --flavour=NAME        run tests marked as requiring flavour NAME (marked
                        with @flavour(NAME)), as well as tests not marked with
                        @flavour. If you call `pytest` without this option,
                        tests marked with @flavour will *all* be run
  --envid=NAME          run tests marked as requiring environment NAME (marked
                        with @envid(NAME)), as well as tests not marked with
                        @envid. Important: if you call `pytest` without this
                        option, tests marked with @envid will *not* be run.

(...)
```

Help on markers is automatically added to the `pytest --markers` output:

```bash
>>> pytest --markers

(...)

@pytest.mark.flavour(value): mark test to run only when command option flavour is used to set --flavour to <value>, or if the option is not used at all.

@pytest.mark.envid(value): mark test to run only when command option environment is used to set --envid to <value>.

(...)
```

### Customization

Almost everything is configurable from the `EasyMarker` constructor: help messages, command option short and long names, filtering behavious when the flag is present or not and the mark is present or not, etc.

See [API reference](./api_reference.md) for details.

## Main features / benefits

 - Create intuitive markers in minutes, with consistent behaviour and associated command options, documented with user-friendly help.

## See Also

 - pytest tutorial on [working with custom markers](https://docs.pytest.org/en/latest/example/markers.html)
 - [this excellent explanation](https://stackoverflow.com/a/52845103/7262247) about how to add options so as to filter on custom markers or on parameter names and values
 - pytest [hooks](https://docs.pytest.org/en/latest/_modules/_pytest/hookspec.html)
 
### Others

*Do you like this library ? You might also like [my other python libraries](https://github.com/smarie/OVERVIEW#python)* 

## Want to contribute ?

Details on the github page: [https://github.com/smarie/python-pytest-pilot](https://github.com/smarie/python-pytest-pilot)
