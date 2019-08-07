# pytest-pilot

*Slice in your test base thanks to powerful markers*

[![Python versions](https://img.shields.io/pypi/pyversions/pytest-pilot.svg)](https://pypi.python.org/pypi/pytest-pilot/) [![Build Status](https://travis-ci.org/smarie/python-pytest-pilot.svg?branch=master)](https://travis-ci.org/smarie/python-pytest-pilot) [![Tests Status](https://smarie.github.io/python-pytest-pilot/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-pytest-pilot/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-pytest-pilot/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-pytest-pilot)

[![Documentation](https://img.shields.io/badge/doc-latest-blue.svg)](https://smarie.github.io/python-pytest-pilot/) [![PyPI](https://img.shields.io/pypi/v/pytest-pilot.svg)](https://pypi.python.org/pypi/pytest-pilot/) [![Downloads](https://pepy.tech/badge/pytest-pilot)](https://pepy.tech/project/pytest-pilot) [![Downloads per week](https://pepy.tech/badge/pytest-pilot/week)](https://pepy.tech/project/pytest-pilot) [![GitHub stars](https://img.shields.io/github/stars/smarie/python-pytest-pilot.svg)](https://github.com/smarie/python-pytest-pilot/stargazers)

In `pytest` we can create custom markers and filter tests according to them using the `-m` flag, as explained [here](https://docs.pytest.org/en/latest/example/markers.html). However it only supports one kind of marker query behaviour: a test with a mark <M> will run *even* if you do not use the `-m <M>` flag. It is also not easy to understand what happens when a marker has a parameter, and how to filter according to this.

`pytest-pilot` proposes a higher-level API to create and register pytest markers, so that they are easy to understand and use.
 

## Installing

```bash
> pip install pytest_pilot
```

## Usage 

**TODO**

## Main features / benefits

**TODO**

## See Also

 - pytest tutorial on [working with custom markers](https://docs.pytest.org/en/latest/example/markers.html)
 - [this excellent explanation](https://stackoverflow.com/a/52845103/7262247) about how to add options so as to filter on custom markers or on parameter names and values
 - pytest [hooks](https://docs.pytest.org/en/latest/_modules/_pytest/hookspec.html)
 
### Others

*Do you like this library ? You might also like [my other python libraries](https://github.com/smarie/OVERVIEW#python)* 

## Want to contribute ?

Details on the github page: [https://github.com/smarie/python-pytest-pilot](https://github.com/smarie/python-pytest-pilot)
