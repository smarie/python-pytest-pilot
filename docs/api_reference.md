# API reference

In general, using `help(symbol)` is the recommended way to get the latest documentation. In addition, this page provides an overview of the various elements in this package.

### `EasyMarker`

A helper class to create pytest marks.

```python
EasyMarker(marker_id,             # type: str
           mode,                  # type: str
           full_name=None,        # type: str
           has_arg=True,          # type: bool
           allowed_values=None,   # type: Iterable[Any]
           cmdoption_short=None,  # type: str
           cmdoption_long=None,   # type: str
           cmdhelp=None,          # type: str
           markhelp=None,         # type: str
           )
```

Creates a pair of marker + commandline option for pytest.

**Parameters:**

 - `marker_id`: the name of the pytest mark. Applying this marker with `@marker(arg)` will be equivalent to applying @pytest.mark.<marker_id>(arg)
 - `mode`: a mandatory string indicating the working mode of this mark and the associated filter option. Four modes are supported:
 
     - 'silos': When the option is inactive, only non-marked tests are run. When the option is active, only relevant marked tests run. There is no test in common between these "silos"
     - 'extender': When the option is inactive, only non-marked tests are run, this is the "base" set of tests. When the option is active, it adds the relevant marked tests to the base set.
     - 'hard_filter': When the option is inactive, all tests run. When the option is active, only the relevant marked tests run.
     - 'soft_filter': When the option is inactive, all tests run. When the option is active, all non-marked tests continue to run, but among marked tests only the relevant ones run.
 
 - `full_name`: the full name of the marker, to be used in help texts. If `None` (default), it defaults to `marker_id`.
 - `has_arg`: if this is `True` (default), the marker has a single argument and the filtering commandline option accepts an argument too. For example a `colormarker` with id `color` will accept an argument describing which color: `@colormarker('yellow')`. If this is `False`, the marker has no argument and the filtering commandline option is a flag with no arguments too. For example a `smokemarker` with id `smoke`: `@smokemarker`.
 - `allowed_values`: a predefined set of values that can be used for this marker. Applying the mark with another value as argument will result in a `ValueError`being raised. `None` (default) will allow users to apply this mark with any value. Note that this can only be set if `has_arg`is `True`
 - `cmdoption_short`: the id to use for the "short" command option (for example providing `'E'` or `'-E'` will result in  the option `'-E'`). `None` (default) will *not* create a "short" command option, to avoid name collisions.
 - `cmdoption_long`: the id to use for the "long" command option (for example providing `'env'` or `'--env'` will result in the option `'--env'`). `None` (default) will use `marker_id` for the long command option.
 - `cmdhelp`: the help message displayed when `pytest --help` is called
 - `markhelp`: the help message displayed when `pytest --markers` is called
