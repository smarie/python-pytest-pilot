from contextlib import contextmanager
from os.path import dirname, join, pardir
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


@contextmanager
def finalizer(tdir):
    try:
        print("using testdir %s" % tdir)
        yield
    finally:
        # actually this is probably not needed :)
        print("finalizing test dir %s" % tdir)
        tdir.finalize()


def test_ensure_pytest_pilot_installed(testdir):
    """Ensures that pytest-pilot is installed."""
    result = testdir.runpytest(testdir.tmpdir, '--trace-config')
    expected_lines = ["*pytest-pilot-*"]
    result.stdout.fnmatch_lines(expected_lines)


def test_basic_markers_help(testdir):
    """executes the test in ../test_cases/basic/ folder """

    with finalizer(testdir):
        testdir.makeconftest(dedent("""
                                    from pytest_pilot import EasyMarker
                    
                                    a_marker = EasyMarker('a', allowed_values=('red', 'yellow'))
                                    b_marker = EasyMarker('b', 'bbb', not_filtering_skips_marked=True)
                                    """))

        # assert that markers descriptions appear correctly
        mresult = testdir.runpytest(testdir.tmpdir, '--markers')
        # print(result.stdout)
        expected_lines = ["@pytest.mark.a(value): mark test to run only when command option a is used to set "
                          "--a to <value>, or if the option is not used at all.",
                          "@pytest.mark.b(value): mark test to run only when command option bbb is used to "
                          "set --b to <value>."]
        mresult.stdout.fnmatch_lines(expected_lines)

        # Note: we cannot run it another time here: ValueError: option names {'--a'} already added
        # that's why we do it again in the next test
        # mresult = testdir.runpytest(testdir.tmpdir, '--help')


def test_basic_options_help(testdir):
    """executes the test in ../test_cases/basic/ folder """

    with finalizer(testdir):
        # basicdir = testdir.mkdir('basic2')
        case_folder = join(CASES_DIR, 'basic')

        testdir.makeconftest(get_conftest(case_folder))
        testdir.makepyfile(get_file(case_folder, 'test_basic.py'))
        make_file(testdir, case_folder, '__init__.py')  # required for the "import from ." to work

        # 2) assert
        result = testdir.runpytest(testdir.tmpdir, '--help')

        expected_lines = """custom options:
  --flavour=NAME        run tests marked as requiring flavour NAME (marked
                        with @flavour(NAME)), as well as tests not marked with
                        @flavour. If you call `pytest` without this option,
                        tests marked with @flavour will *all* be run
  --envid=NAME          run tests marked as requiring environment NAME (marked
                        with @envid(NAME)), as well as tests not marked with
                        @envid. Important: if you call `pytest` without this
                        option, tests marked with @envid will *not* be run.""".splitlines(False)
        result.stdout.fnmatch_lines(expected_lines)


def test_basic_run_envquery(testdir):
    """executes the test in ../test_cases/basic/ folder """

    with finalizer(testdir):
        # basicdir = testdir.mkdir('basic')
        case_folder = join(CASES_DIR, 'basic')
        testdir.makeconftest(get_conftest(case_folder))
        testdir.makepyfile(get_file(case_folder, 'test_basic.py'))
        make_file(testdir, case_folder, '__init__.py')  # required for the "import from ." to work

        # 2) run
        result = testdir.runpytest(testdir.tmpdir, '-v', '-s', '--envid', 'env1')
        # the only test skipped should be the one with env2
        result.assert_outcomes(passed=4, skipped=1)


def test_basic_run_flavourquery(testdir):
    """executes the test in ../test_cases/basic/ folder """

    with finalizer(testdir):
        # basicdir = testdir.mkdir('basic')
        case_folder = join(CASES_DIR, 'basic')
        testdir.makeconftest(get_conftest(case_folder))
        testdir.makepyfile(get_file(case_folder, 'test_basic.py'))
        make_file(testdir, case_folder, '__init__.py')  # required for the "import from ." to work

        # 2) run
        result = testdir.runpytest(testdir.tmpdir, '-v', '-s', '--flavour', 'red', '--envid', 'env2')
        #
        result.assert_outcomes(passed=3, skipped=2)


def test_nameconflict(testdir):
    """tests that a name conflict raises an exception"""

    testdir.makeconftest(dedent("""
                                from pytest_pilot import EasyMarker
                                
                                colormarker = EasyMarker('color', allowed_values=('red', 'yellow'))
                                """))

    result = testdir.runpytest(testdir.tmpdir)
    expected_lines = "ValueError: Error registering marker 'Pytest marker 'color' with commandline option '--color' " \
                     "and pytest mark '@pytest.mark.color(<color>)'': a command with this name already exists. " \
                     "Conflicting name(s): ['--color']"
    result.stderr.fnmatch_lines(expected_lines)
