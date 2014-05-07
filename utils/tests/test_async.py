import string

from utils.async import ResultsPool, ResultsThreadPool


def pytest_generate_tests(metafunc):
    metafunc.parametrize('pool_class',
        argvalues=[ResultsPool, ResultsThreadPool],
        ids=['processes', 'threads'],
        scope='module')


def async_task(arg1, arg2):
    """Task to reverse arguments. Asynchronously..."""
    return arg2, arg1


def _apply_task(pool_class):
    with pool_class(processes=3) as pool:
        for letter, digit in zip(string.letters[:3], string.digits[:3]):
            pool.apply_async(async_task, [letter, digit])
    return pool


def test_async(pool_class):
    pool = _apply_task(pool_class)
    assert pool.successful

    for result in pool.results:
        # Result should have reversed args, i.e.
        # digit, letter = async_task(letter, digit)
        digit, letter = result.get()
        assert digit in string.digits
        assert letter in string.letters
    num_results = len(pool.results)

    # Do it again to make sure results get cleared correctly
    new_pool = _apply_task(pool_class)
    assert len(new_pool.results) == num_results

    # Also double check that the context manager gave us a new pool instance
    assert pool is not new_pool
