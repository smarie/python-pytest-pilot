# Changelog

### 0.8.0 - New `easymarkers` fixture

 - New `easymarkers` fixture to access current values of all CLI options related to EasyMarkers, from within tests. Fixed [#17](https://github.com/smarie/python-pytest-pilot/issues/17)

### 0.7.0 - New `agnostic` mark

 - `@<marker>.agnostic` can be used to decorate tests that should always run, whatever the configuration. This is only relevant for `mode='silos'` or `mode='hard_filter'`. Fixes [#15](https://github.com/smarie/python-pytest-pilot/issues/15)

### 0.6.0 - Usage in parametrization

 - `EasyMarker` markers can now be used on parameters in tests (and also on case functions, if you use `pytest-cases` :)). Fixes [#12](https://github.com/smarie/python-pytest-pilot/issues/12)

### 0.5.0 - Better API, implementation and documentation

 - `EasyMarker` API improvements: now a single `mode` argument with four supported values (`'silos'`, `'extender'`, `hard_filter`, `soft_filter`) replaces the very unfriendly `filtering_skips_unmarked` and `not_filtering_skips_marked`. This argument is mandatory, so that users have to decide what they want as a resulting behaviour. Fixes [#5](https://github.com/smarie/python-pytest-pilot/issues/5)
 - Markers without arguments (`EasyMarker(has_arg=False)`) now work correctly. Fixes [#8](https://github.com/smarie/python-pytest-pilot/issues/8)
 - Short command option name (`EasyMarker(cmdoption_short=...)`) is now registered correctly. Fixed [#9](https://github.com/smarie/python-pytest-pilot/issues/9)
 - `allowed_values` are now correctly taken into account by `EasyMarker`. Fixes [#1](https://github.com/smarie/python-pytest-pilot/issues/1) 
 - Removed annoying warning about marks registration. Fixes [#6](https://github.com/smarie/python-pytest-pilot/issues/6)
 - Improved the various messages printed when using `pytest --markers` and `pytest --help`. In particular, using `--markers` shows the allowed values for a given marker.

### 0.1.2 - packaging improvements

 - packaging improvements: set the "universal wheel" flag to 1, and cleaned up the `setup.py`. In particular removed dependency to `six` for setup and added `py.typed` file, as well as set the `zip_safe` flag to False. Removed tests folder from package. Fixes [#4](https://github.com/smarie/python-pytest-pilot/issues/4)

### 0.1.1 - `pyproject.toml`

Added `pyproject.toml`

### 0.1.0 - First public version

 * Initial fork from private repository
