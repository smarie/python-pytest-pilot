from distutils.version import LooseVersion
from os.path import dirname, join, pardir

import pytest
from textwrap import dedent

CASES_DIR = join(dirname(__file__), pardir, 'test_cases')


def get_conftest(case_folder):
    return get_file(case_folder, 'conftest.py')


def get_file(case_folder, file_name):
    with open(join(case_folder, file_name)) as f:
        return f.read()


def make_file(testdir, case_folder, file_name):
    dest = testdir.tmpdir.join(file_name)
    dest.dirpath().ensure_dir()

    with open(join(case_folder, file_name)) as f:
        contents = f.read()
        dest.write(contents)


# @pytest.fixture
# def mytestdir(testdir):
#     print("using testdir %s" % testdir)
#     yield testdir
#     print("finalizing test dir %s" % testdir)
#     testdir.finalize()


def test_ensure_pytest_pilot_installed(testdir):
    """Ensures that pytest-pilot is installed."""
    result = testdir.runpytest('--trace-config')
    if result.ret != 5:
        print(result.stderr.str())
    assert result.ret == 5
    expected_lines = ["*pytest-pilot-*"]
    result.stdout.fnmatch_lines(expected_lines)


def test_basic_markers_help(testdir):
    """Creates two markers and check that pytest --markers returns correct help on those """

    testdir.makeconftest(dedent("""
                                from pytest_pilot import EasyMarker
                
                                silos_marker = EasyMarker('silos', has_arg=False, mode="silos")
                                extender_marker = EasyMarker('extender', allowed_values=('red', 'yellow'), mode="extender")
                                hardfilter_marker = EasyMarker('hard_filter', full_name='bbb', mode="hard_filter")
                                softfilter_marker = EasyMarker('soft_filter', mode="soft_filter")
                                """))

    # assert that markers descriptions appear correctly
    result = testdir.runpytest('--markers')
    if result.ret != 0:
        print(result.stderr.str())
    assert result.ret == 0
    expected_lines = """
@pytest.mark.silos: mark test to run *only* when --silos ('silos' option) is set.
@pytest.mark.extender(value): mark test to run *only* when --extender ('extender' option) is set to <value>. <value> should be one of ('red', 'yellow').
@pytest.mark.hard_filter(value): mark test to run *both* when --hard_filter ('bbb' option) is set to <value> and if --hard_filter is not set.
@pytest.mark.soft_filter(value): mark test to run *both* when --soft_filter ('soft_filter' option) is set to <value> and if --soft_filter is not set.
""".strip().splitlines(False)
    result.stdout.fnmatch_lines(expected_lines)

    # Note: we cannot run it another time here: ValueError: option names {'--a'} already added
    # that's why we do it again in the next test
    # mresult = testdir.runpytest(testdir.tmpdir, '--help')


def test_basic_options_help(testdir):
    """executes the test in ../test_cases/basic/ folder """

    # basicdir = testdir.mkdir('basic2')
    case_folder = join(CASES_DIR, 'basic')

    testdir.makeconftest(get_conftest(case_folder))
    testdir.makepyfile(get_file(case_folder, 'test_basic.py'))
    make_file(testdir, case_folder, '__init__.py')  # required for the "import from ." to work

    # 2) assert
    result = testdir.runpytest(testdir.tmpdir, '--help')

    if LooseVersion(pytest.__version__) < "5.0.0":
        # note: in old pytest the help is formatted a bit differently
        expected_lines = ["  -Z, --silo            only run tests marked as silo (marked with @silo)."]
    else:
        expected_lines = """  -Z, --silo            only run tests marked as silo (marked with @silo).
                        Important: if you call `pytest` without this option,
                        tests marked with @silo will *not* be run.
  --hf                  only run tests marked as hf (marked with @hf). If you
                        call `pytest` without this option, tests marked with @hf
                        will *all* be run.
  --envid=NAME          run tests marked as requiring environment NAME (marked
                        with @envid(NAME)), as well as tests not marked with
                        @envid. Important: if you call `pytest` without this
                        option, tests marked with @envid will *not* be run.
  --flavour=NAME        run tests marked as requiring flavour NAME (marked with
                        @flavour(NAME)), as well as tests not marked with
                        @flavour. If you call `pytest` without this option,
                        tests marked with @flavour will *all* be run.""".splitlines(False)
    result.stdout.fnmatch_lines(expected_lines)


@pytest.mark.parametrize("cmdoptions,results", [
    ((), dict(passed=4, skipped=3)),
    (('-Z',), dict(passed=1, skipped=6)),
    (('--silo',), dict(passed=1, skipped=6)),
    (('--hf',), dict(passed=2, skipped=5)),
    (('--hf', '--flavour=red'), dict(passed=1, skipped=6)),
    (('--hf', '--flavour=yellow'), dict(passed=2, skipped=5)),
    (('--envid', 'foo'), dict(passed=4, skipped=3)),
    (('--envid=env1',), dict(passed=5, skipped=2)),
    (('--flavour=red', '--envid=env2'), dict(passed=4, skipped=3))
])
def test_basic_run_queries(testdir, cmdoptions, results):
    """executes the test in ../test_cases/basic/ folder with option --silo"""

    # basicdir = testdir.mkdir('basic')
    case_folder = join(CASES_DIR, 'basic')
    testdir.makeconftest(get_conftest(case_folder))
    testdir.makepyfile(get_file(case_folder, 'test_basic.py'))
    make_file(testdir, case_folder, '__init__.py')  # required for the "import from ." to work

    # 2) run
    result = testdir.runpytest(testdir.tmpdir, '-v', '-s', *cmdoptions)
    # the only test skipped should be the one with env2
    result.assert_outcomes(**results)


def test_nameconflict(testdir):
    """tests that a name conflict raises an exception"""

    testdir.makeconftest(dedent("""
                                from pytest_pilot import EasyMarker
                                
                                colormarker = EasyMarker('color', mode="extender", allowed_values=('red', 'yellow'))
                                """))

    result = testdir.runpytest(testdir.tmpdir)
    expected_lines = "ValueError: Error registering <Pytest marker 'color' with CLI option '--color' " \
                     "and decorator '@pytest.mark.color(<color>)'>: a command with this long or short name already " \
                     "exists. Conflicting name(s): ['--color']"
    result.stderr.fnmatch_lines(expected_lines)


def test_nameconflict_short(testdir):
    testdir.makeconftest(dedent("""
                                from pytest_pilot import EasyMarker

                                a = EasyMarker('a', cmdoption_short='-a', mode="extender")
                                aa = EasyMarker('aa', cmdoption_short='-a', mode="extender")
                                """))

    result = testdir.runpytest(testdir.tmpdir)
    expected_str = "ValueError: Error registering <Pytest marker 'a' with CLI option '-a/--a' " \
                   "and decorator '@pytest.mark.a(<a>)'>: a command with this long or short name already " \
                   "exists. Caught: ValueError('lowercase shortoptions reserved'"
    assert expected_str in '\n'.join(result.stderr.lines)
