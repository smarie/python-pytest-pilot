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

### 1. Basics

The easiest way to define a marker is to create an instance of `EasyMarker` in [a `contest.py` file](https://docs.pytest.org/en/latest/writing_plugins.html#conftest-py-plugins). 

When you create a marker with `mymarker = EasyMarker('mymarker', ...)`, you get 2 things:

 - `@mymarker(arg)` is a decorator that is equivalent to `@pytest.mark.mymarker(arg)`. You can use it to mark some of your tests. For example:

```python
@mymarker('red')
def test_foo():
    pass

@mymarker('yellow')
def test_bar():
    pass
```

 - an associated `--mymarker` CLI option is automatically registered: `pytest --mymarker=<arg>` or `pytest --mymarker <arg>` will enable this option. For example

```bash
>>> pytest --mymarker=red
```

### 2. Arguments

By default the `@mymarker` decorator accepts a single argument. The set of allowed arguments can be restricted with `allowed_values=...`. Alternately `EasyMarker` can be declared to have no argument and be just a flag (`has_arg=False`). In that case the decorator can be used without parenthesis, and the CLI option will be a flag as well.

### 3. Names

By default the option has just a long name, identical to the marker id. You can customize it and optionally add a short name using `cmdoption_long` and `cmdoption_short`.

### 4. Modes

Now all the purpose of this library is to allow you to easily configure **which tests should run** when this `--mymarker` CLI option is active, and which ones should run when it is not. This is configured with the mandatory `mode` argument, with 4 possible values:

 - `'silos'`: when the option is **inactive**, only non-marked tests are run. When the option is **active** (`pytest --mymarker <arg>`), only tests marked with `@mymarker(<arg>)` run. There is no test in common between these "silos".

 - `'extender'`: when the option is **inactive**, only non-marked tests are run, this is the "base" set of tests. When the option is **active** (`pytest --mymarker <arg>`), it tests marked with `@mymarker(<arg>)` are added to the base set.
   
 - `'hard_filter'`: when the option is inactive, all tests run. When the option is active, only the relevant marked tests run.
   
 - `'soft_filter'`: when the option is inactive, all tests run. When the option is active, all non-marked tests continue to run, but among marked tests, only the relevant ones run. 


### 5. Examples

#### Silos

The silo mode is a way to partition your tests into several, non-intersecting, sets. Unmarked tests are in the "default" silo.

For example we can create an `envid` marker defining the python environment on which a test runs. Tests that have this marker should run **only** if `pytest` is called with a `--envid` flag indicating that the environment is active. Tests that do not have this marker are considered in the "default" environment and should only run when no environment is set.

 - `conftest.py`:

```python
from pytest_pilot import EasyMarker

envid = EasyMarker('envid', mode='silos')
```

 - `test_silos.py` (you'll have to create an `__init__.py` in the folder to allow for relative imports):

```python
from .conftest import envid

@envid('a')
def test_foo_a():
    pass

@envid('b')
def test_foo_b():
    pass

def test_foo():
    pass
```

Running `pytest` (with the `-rs` option to show a summary of skipped tests) yields:

```
>>> pytest -rs
============================= test session starts ==========================================
(...)
collected 3 items

pytest_pilot/test_doc/test_silos.py::test_foo_a SKIPPED       [ 33%]
pytest_pilot/test_doc/test_silos.py::test_foo_b SKIPPED       [ 66%]
pytest_pilot/test_doc/test_silos.py::test_foo PASSED          [100%]

========================== short test summary info =========================================
SKIPPED [1] <file>: This test requires 'envid'='a'. Run `pytest --envid=a` to activate it.
SKIPPED [1] <file>: This test requires 'envid'='b'. Run `pytest --envid=b` to activate it.
========================== 1 passed, 2 skipped in 0.04s ====================================
```

And we can instead activate environment `'b'`.

```
>>> pytest -rs --envid=b
============================= test session starts ==========================================
(...)
collected 3 items

pytest_pilot/test_doc/test_silos.py::test_foo_a SKIPPED        [ 33%]
pytest_pilot/test_doc/test_silos.py::test_foo_b PASSED         [ 66%]
pytest_pilot/test_doc/test_silos.py::test_foo SKIPPED          [100%]

========================== short test summary info =============================================================
SKIPPED [1] <file>: This test requires 'envid'='a'. Currently `--envid=b` so it is skipped.
SKIPPED [1] <file>: This test does not have mark 'envid', and pytest was run with `--envid=b` so it is skipped
========================== 1 passed, 2 skipped in 0.04s ========================================================
```

Note that as can be seen above, `test_foo`, that was not marked, is now skipped (it is implicitly in the "no env" silo so if we activate another silo it becomes skipped). This is the main difference with the ["extender" mode below](#extender).


#### Extender

The extender mode is probably the simplest to understand: marked tests are optional tests, that can be added to the other tests when the option is specified. For example let's mark a few tests as being slow tests that should be skipped for daily testing. Note that this time we'll create a marker with no arguments to show that such markers can also be created, but it could of course receive arguments just as in previous example.

 - `conftest.py`:

```python
from pytest_pilot import EasyMarker

slow = EasyMarker('slow', has_arg=False, mode='extender')
```

 - `test_extender.py`:

```python
from .conftest import slow

@slow
def test_bar_slow():
    pass

def test_bar():
    pass
```

Running `pytest` (with the `-rs` option to show a summary of skipped tests) yields:

```
>>> pytest -rs
============================= test session starts ==========================================
(...)
collected 2 items

pytest_pilot/test_doc/test_extender.py::test_bar_slow SKIPPED       [ 50%]
pytest_pilot/test_doc/test_extender.py::test_foo PASSED             [100%]

========================== short test summary info =========================================
SKIPPED [1] <file>: This test requires 'slow'. Run `pytest --slow` to activate it.
========================== 1 passed, 1 skipped in 0.04s ====================================
```

And we can run all tests including the slow ones with `--slow`:

```
>>> pytest -rs --slow
============================= test session starts ==========================================
(...)
collected 2 items

pytest_pilot/test_doc/test_extender.py::test_bar_slow PASSED        [ 50%]
pytest_pilot/test_doc/test_extender.py::test_foo PASSED             [100%]

================================ 2 passed in 0.04s =========================================
```


#### Hard filter

"Hard filter" mode is the opposite of "Extender". Instead of adding tests when the option is active, it removes all irrelevant tests, keeping only those matching the query.

 - `conftest.py`:

```python
from pytest_pilot import EasyMarker

# below we demonstrate the usage of `allowed_values` to restrict the possible values
flavour = EasyMarker('flavour', allowed_values=('red', 'yellow'), mode='hard_filter')
```

 - `test_hardfilter.py` (you'll have to create an `__init__.py` in the folder to allow for relative imports):

```python
from .conftest import flavour

@flavour('yellow')
def test_foo_yellow():
    pass

@flavour('red')
def test_foo_red():
    pass

def test_foo():
    pass
```

Running `pytest` (with the `-rs` option to show a summary of skipped tests) yields:

```
>>> pytest -rs
============================= test session starts ==========================================
(...)
collected 3 items                                                                                                                                                                                                   
pytest_pilot/test_doc/test_hardfilter.py::test_foo_yellow PASSED         [ 33%]
pytest_pilot/test_doc/test_hardfilter.py::test_foo_red PASSED            [ 66%]
pytest_pilot/test_doc/test_hardfilter.py::test_foo PASSED                [100%]

================================ 3 passed in 0.04s =========================================
```

We can instead filter on tests with the `'red'` flavour:

```
>>> pytest -rs --flavour=red
============================= test session starts ==========================================
(...)
collected 3 items

pytest_pilot/test_doc/test_hardfilter.py::test_foo_yellow SKIPPED         [ 33%]
pytest_pilot/test_doc/test_hardfilter.py::test_foo_red PASSED             [ 66%]
pytest_pilot/test_doc/test_hardfilter.py::test_foo SKIPPED                [100%]

========================== short test summary info =============================================================
SKIPPED [1] <file>: This test requires 'flavour'='yellow'. Currently `--flavour=red` so it is skipped.
SKIPPED [1] <file>: This test does not have mark 'flavour', and pytest was run with `--flavour=red` so it is skipped.
========================== 1 passed, 2 skipped in 0.04s ========================================================
```

You can see that `test_foo`, that was not marked, has been skipped. This is the main difference with the [soft filer](#soft-filter) presented below.


#### Soft filter

"Soft filter" mode is very similar to "Hard filter". The only difference is for non-marked tests. While in hard filter mode they are skipped as soon as the option is active, in soft filter mode they are always run.

 - `conftest.py`:

```python
from pytest_pilot import EasyMarker

flavour = EasyMarker('flavour', allowed_values=('red', 'yellow'), mode='soft_filter')
```

 - `test_hardfilter.py` (you'll have to create an `__init__.py` in the folder to allow for relative imports):

```python
from .conftest import flavour

@flavour('yellow')
def test_foo_yellow():
    pass

@flavour('red')
def test_foo_red():
    pass

def test_foo():
    pass
```

Running `pytest` (with the `-rs` option to show a summary of skipped tests) yields:

```
>>> pytest -rs
============================= test session starts ==========================================
(...)
collected 3 items                                                                                                                                                                                                   
pytest_pilot/test_doc/test_hardfilter.py::test_foo_yellow PASSED         [ 33%]
pytest_pilot/test_doc/test_hardfilter.py::test_foo_red PASSED            [ 66%]
pytest_pilot/test_doc/test_hardfilter.py::test_foo PASSED                [100%]

================================ 3 passed in 0.04s =========================================
```

We can instead filter on tests with the `'yellow'` flavour:

```
>>> pytest -rs --flavour=yellow
============================= test session starts ==========================================
(...)
collected 3 items

pytest_pilot/test_doc/test_hardfilter.py::test_foo_yellow PASSED           [ 33%]
pytest_pilot/test_doc/test_hardfilter.py::test_foo_red SKIPPED             [ 66%]
pytest_pilot/test_doc/test_hardfilter.py::test_foo PASSED                  [100%]

========================== short test summary info =============================================================
SKIPPED [1] <file>: This test requires 'flavour'='red'. Currently `--flavour=yellow` so it is skipped.
========================== 2 passed, 1 skipped in 0.04s ========================================================
```

You can see that now `test_foo`, that was not marked, was not skipped - as opposed to the previous example of "hard filter".

### 7. Misc

#### Using the markers in parametrized tests

If your tests are parametrized, you should be able to use the markers on each parametrization value:

```python
@pytest.mark.parametrize("a", [0, envid(False), slow(True), 1])
def test_foo(a):
    pass
```

However this is an [open issue](https://github.com/smarie/python-pytest-pilot/issues/12) (help from a pytest expert would be much appreciated!).


#### Further customization

See [API reference](./api_reference.md) for details.

#### Debug / Verbosity levels

You can use the verbose pytest flags with the `-s` option to get a little more explanation about why tests are skipped or why they are NOT skipped (while you think they should):

```bash
>>> pytest -s -vv --flavour=red
(verbose explanations)
>>> pytest -s -vvv --flavour=red
(even more verbose explanations)
```

#### Help

Help on command options is automatically added to the `pytest --help` output:

```bash
>>> pytest --help

(...)

custom options:
  --flavour=NAME        run tests marked as requiring flavour NAME (marked with @flavour(NAME)), as well as tests not marked with @flavour. If you call `pytest` without this option, tests marked with @flavour will *all* be run.

(...)
```

Help on markers is automatically added to the `pytest --markers` output:

```bash
>>> pytest --markers

(...)

@pytest.mark.flavour(value): mark test to run *both* when --flavour ('flavour' option) is set to <value> and if --flavour is not set. <value> should be one of ('red', 'yellow').

(...)
```


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
